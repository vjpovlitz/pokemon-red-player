-- ==========================================================================
-- mgba_server.lua — TCP JSON server for mGBA scripting engine
-- ==========================================================================
--
-- PURPOSE:
--   This script runs inside mGBA (loaded via Tools > Scripting > File > Load
--   Script). It opens a TCP socket on localhost:5555 and accepts connections
--   from external programs (the Python MCP bridge). Commands arrive as
--   newline-delimited JSON and responses are sent back the same way.
--
-- PROTOCOL:
--   Request:  {"cmd": "<command>", ...params}\n
--   Response: {"ok": true, "value": ...}\n   or   {"ok": false, "error": "..."}\n
--
--   Every request can include an "id" field; the response will echo it back
--   so the client can match responses to requests.
--
-- SUPPORTED COMMANDS:
--   read8, read16, read32   — read 1/2/4 bytes from a GBA memory address
--   readRange               — read N bytes as a hex string
--   write8, write16, write32 — write 1/2/4 bytes to a GBA memory address
--   press                   — hold a button for N frames
--   screenshot              — capture frame as base64 PNG
--   saveState / loadState   — save/load emulator state slots
--   runFrames               — advance emulation by N frames (deferred response)
--   getKeys                 — read currently pressed buttons
--   ping                    — connectivity check
--
-- ARCHITECTURE:
--   The server is non-blocking. On each frame, mGBA calls our registered
--   callbacks:
--     1. "keysRead" callback → poll() → accept new connections + read data
--     2. "frame" callback → on_frame() → process pending button holds and
--        frame-advance requests
--
--   Button presses are queued into `pending_presses` and applied via
--   emu:addKey() each frame until their duration expires. Frame-advance
--   requests are queued into `pending_frames` and count down each frame;
--   the response is only sent once the requested number of frames has elapsed.
--
-- REQUIREMENTS:
--   mGBA 0.10+ with scripting enabled. No external Lua libraries needed —
--   uses mGBA's built-in `socket`, `emu`, `console`, and `callbacks` APIs.
-- ==========================================================================

local PORT = 5555       -- TCP port to listen on (must match mgba_client.py)
local server = nil      -- TCP server socket
local clients = {}      -- Connected clients: list of {sock=socket, buffer=""}

-- -------------------------------------------------------------------------
-- GBA button mapping
-- Maps human-readable button names to mGBA's C.GBA.KEY_* constants.
-- These are bitmask values used with emu:addKey().
-- -------------------------------------------------------------------------
-- Resolve key constants: try C.GBA_KEY (mGBA 0.10+), then C.GBA, then hardcoded
local GBA_KEYS
if C and C.GBA_KEY then
    GBA_KEYS = C.GBA_KEY
elseif C and C.GBA then
    GBA_KEYS = {
        A = C.GBA.KEY_A, B = C.GBA.KEY_B, SELECT = C.GBA.KEY_SELECT,
        START = C.GBA.KEY_START, RIGHT = C.GBA.KEY_RIGHT, LEFT = C.GBA.KEY_LEFT,
        UP = C.GBA.KEY_UP, DOWN = C.GBA.KEY_DOWN, R = C.GBA.KEY_R, L = C.GBA.KEY_L
    }
else
    -- Hardcoded GBA key IDs (stable across all mGBA versions)
    GBA_KEYS = { A=0, B=1, SELECT=2, START=3, RIGHT=4, LEFT=5, UP=6, DOWN=7, R=8, L=9 }
end

local BUTTON_MAP = {
    A      = GBA_KEYS.A,
    B      = GBA_KEYS.B,
    SELECT = GBA_KEYS.SELECT,
    START  = GBA_KEYS.START,
    RIGHT  = GBA_KEYS.RIGHT,
    LEFT   = GBA_KEYS.LEFT,
    UP     = GBA_KEYS.UP,
    DOWN   = GBA_KEYS.DOWN,
    R      = GBA_KEYS.R,
    L      = GBA_KEYS.L
}

-- Queue of active button holds.
-- Each entry: {key = GBA_KEY_CONSTANT, frames_remaining = N}
-- On each frame, active keys are OR'd together and applied via emu:addKey().
local pending_presses = {}

-- Queue of frame-advance requests waiting to complete.
-- Each entry: {client = socket, frames_remaining = N, id = request_id}
-- The response is sent only after the countdown reaches zero.
local pending_frames = {}


-- ==========================================================================
-- JSON ENCODER / DECODER
-- ==========================================================================
-- mGBA's Lua 5.4 environment does not include a JSON library, so we
-- implement minimal encode/decode here. Handles: string, number, boolean,
-- nil (→ null), and tables (auto-detects array vs object).
-- ==========================================================================

local function json_encode(val)
    local t = type(val)
    if val == nil then
        return "null"
    elseif t == "boolean" then
        return val and "true" or "false"
    elseif t == "number" then
        -- Guard against special float values that aren't valid JSON
        if val ~= val then return "null" end       -- NaN
        if val == math.huge then return "1e999" end
        if val == -math.huge then return "-1e999" end
        return tostring(val)
    elseif t == "string" then
        -- Escape special characters for JSON string safety
        local escaped = val:gsub('\\', '\\\\')
                           :gsub('"', '\\"')
                           :gsub('\n', '\\n')
                           :gsub('\r', '\\r')
                           :gsub('\t', '\\t')
        return '"' .. escaped .. '"'
    elseif t == "table" then
        -- Determine if this is an array (sequential integer keys 1..N)
        local is_array = true
        local max_i = 0
        for k, _ in pairs(val) do
            if type(k) ~= "number" or k ~= math.floor(k) or k < 1 then
                is_array = false
                break
            end
            if k > max_i then max_i = k end
        end
        if is_array and max_i == #val then
            -- Encode as JSON array: [val1, val2, ...]
            local parts = {}
            for i = 1, #val do
                parts[i] = json_encode(val[i])
            end
            return "[" .. table.concat(parts, ",") .. "]"
        else
            -- Encode as JSON object: {"key": val, ...}
            local parts = {}
            for k, v in pairs(val) do
                table.insert(parts, json_encode(tostring(k)) .. ":" .. json_encode(v))
            end
            return "{" .. table.concat(parts, ",") .. "}"
        end
    end
    return "null"
end

-- Recursive-descent JSON parser. Returns a Lua value from a JSON string.
local function json_decode(str)
    local pos = 1

    -- Skip whitespace characters at current position
    local function skip_ws()
        while pos <= #str and str:sub(pos, pos):match("[ \t\r\n]") do
            pos = pos + 1
        end
    end

    local parse_value -- forward declaration for mutual recursion

    -- Parse a JSON string (assumes pos is at the opening quote)
    local function parse_string()
        pos = pos + 1 -- skip opening "
        local result = {}
        while pos <= #str do
            local ch = str:sub(pos, pos)
            if ch == '"' then
                pos = pos + 1
                return table.concat(result)
            elseif ch == '\\' then
                -- Handle escape sequences
                pos = pos + 1
                local esc = str:sub(pos, pos)
                if esc == 'n' then table.insert(result, '\n')
                elseif esc == 't' then table.insert(result, '\t')
                elseif esc == 'r' then table.insert(result, '\r')
                elseif esc == '"' then table.insert(result, '"')
                elseif esc == '\\' then table.insert(result, '\\')
                elseif esc == '/' then table.insert(result, '/')
                else table.insert(result, esc) end
            else
                table.insert(result, ch)
            end
            pos = pos + 1
        end
        error("unterminated string")
    end

    -- Parse a JSON number (integer or float, with optional exponent)
    local function parse_number()
        local start = pos
        if str:sub(pos, pos) == '-' then pos = pos + 1 end
        while pos <= #str and str:sub(pos, pos):match("[0-9]") do pos = pos + 1 end
        if pos <= #str and str:sub(pos, pos) == '.' then
            pos = pos + 1
            while pos <= #str and str:sub(pos, pos):match("[0-9]") do pos = pos + 1 end
        end
        if pos <= #str and str:sub(pos, pos):match("[eE]") then
            pos = pos + 1
            if pos <= #str and str:sub(pos, pos):match("[+-]") then pos = pos + 1 end
            while pos <= #str and str:sub(pos, pos):match("[0-9]") do pos = pos + 1 end
        end
        return tonumber(str:sub(start, pos - 1))
    end

    -- Parse a JSON object: {"key": value, ...}
    local function parse_object()
        pos = pos + 1 -- skip {
        skip_ws()
        local obj = {}
        if str:sub(pos, pos) == '}' then pos = pos + 1; return obj end
        while true do
            skip_ws()
            local key = parse_string()
            skip_ws()
            pos = pos + 1 -- skip :
            skip_ws()
            obj[key] = parse_value()
            skip_ws()
            if str:sub(pos, pos) == ',' then
                pos = pos + 1
            else
                break
            end
        end
        skip_ws()
        pos = pos + 1 -- skip }
        return obj
    end

    -- Parse a JSON array: [value, value, ...]
    local function parse_array()
        pos = pos + 1 -- skip [
        skip_ws()
        local arr = {}
        if str:sub(pos, pos) == ']' then pos = pos + 1; return arr end
        while true do
            skip_ws()
            table.insert(arr, parse_value())
            skip_ws()
            if str:sub(pos, pos) == ',' then
                pos = pos + 1
            else
                break
            end
        end
        skip_ws()
        pos = pos + 1 -- skip ]
        return arr
    end

    -- Dispatch to the correct parser based on the first character
    parse_value = function()
        skip_ws()
        local ch = str:sub(pos, pos)
        if ch == '"' then return parse_string()
        elseif ch == '{' then return parse_object()
        elseif ch == '[' then return parse_array()
        elseif ch == 't' then pos = pos + 4; return true    -- "true"
        elseif ch == 'f' then pos = pos + 5; return false   -- "false"
        elseif ch == 'n' then pos = pos + 4; return nil     -- "null"
        else return parse_number() end
    end

    return parse_value()
end


-- ==========================================================================
-- NETWORK HELPERS
-- ==========================================================================

-- Send a JSON response object to a client, terminated by newline.
local function send_response(sock, resp)
    local data = json_encode(resp) .. "\n"
    sock:send(data)
end


-- ==========================================================================
-- COMMAND HANDLER
-- ==========================================================================
-- Dispatches a parsed JSON request to the appropriate mGBA API call.
-- Returns a response table, or nil for deferred responses (runFrames).
-- ==========================================================================

local function handle_command(sock, req)
    local cmd = req.cmd
    if not cmd then
        return {ok = false, error = "missing 'cmd' field"}
    end

    -- ----- Memory reads -----
    if cmd == "read8" then
        -- Read a single byte from GBA memory
        local val = emu:read8(req.addr)
        return {ok = true, value = val}

    elseif cmd == "read16" then
        -- Read a 16-bit little-endian value from GBA memory
        local val = emu:read16(req.addr)
        return {ok = true, value = val}

    elseif cmd == "read32" then
        -- Read a 32-bit little-endian value from GBA memory
        local val = emu:read32(req.addr)
        return {ok = true, value = val}

    elseif cmd == "readRange" then
        -- Read N bytes starting at addr, return as hex string
        -- e.g., readRange(0x02000000, 4) → "a1b2c3d4"
        local bytes = {}
        for i = 0, (req.length or 1) - 1 do
            bytes[i + 1] = string.format("%02x", emu:read8(req.addr + i))
        end
        return {ok = true, value = table.concat(bytes)}

    -- ----- Memory writes -----
    elseif cmd == "write8" then
        emu:write8(req.addr, req.value)
        return {ok = true}

    elseif cmd == "write16" then
        emu:write16(req.addr, req.value)
        return {ok = true}

    elseif cmd == "write32" then
        emu:write32(req.addr, req.value)
        return {ok = true}

    -- ----- Button input -----
    elseif cmd == "press" then
        -- Queue a button to be held for N frames.
        -- The actual key injection happens in on_frame() via emu:addKey().
        local button = string.upper(req.button or "")
        local gba_key = BUTTON_MAP[button]
        if not gba_key then
            return {ok = false, error = "unknown button: " .. (req.button or "nil")}
        end
        local frames = req.frames or 10
        table.insert(pending_presses, {key = gba_key, frames_remaining = frames})
        return {ok = true}

    -- ----- Screenshot -----
    elseif cmd == "screenshot" then
        -- Capture current frame: save to temp file, read back, base64 encode.
        -- mGBA's emu:screenshot(path) writes a PNG to disk.
        local tmp = (os.getenv("TEMP") or os.getenv("TMP") or "/tmp") .. "/mgba_screenshot.png"
        emu:screenshot(tmp)
        local f = io.open(tmp, "rb")
        if not f then
            return {ok = false, error = "failed to capture screenshot"}
        end
        local data = f:read("*a")
        f:close()
        os.remove(tmp) -- clean up temp file

        -- Base64 encode the PNG binary data
        local b64chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        local encoded = {}
        for i = 1, #data, 3 do
            local b1 = data:byte(i) or 0
            local b2 = data:byte(i + 1) or 0
            local b3 = data:byte(i + 2) or 0
            -- Combine 3 bytes into a 24-bit number, then split into 4 6-bit indices
            local n = b1 * 65536 + b2 * 256 + b3
            table.insert(encoded, b64chars:sub(math.floor(n / 262144) % 64 + 1, math.floor(n / 262144) % 64 + 1))
            table.insert(encoded, b64chars:sub(math.floor(n / 4096) % 64 + 1, math.floor(n / 4096) % 64 + 1))
            if i + 1 <= #data then
                table.insert(encoded, b64chars:sub(math.floor(n / 64) % 64 + 1, math.floor(n / 64) % 64 + 1))
            else
                table.insert(encoded, "=") -- padding
            end
            if i + 2 <= #data then
                table.insert(encoded, b64chars:sub(n % 64 + 1, n % 64 + 1))
            else
                table.insert(encoded, "=") -- padding
            end
        end
        return {ok = true, value = table.concat(encoded)}

    -- ----- Save states -----
    elseif cmd == "saveState" then
        local slot = req.slot or 1
        emu:saveStateSlot(slot)
        return {ok = true}

    elseif cmd == "loadState" then
        local slot = req.slot or 1
        emu:loadStateSlot(slot)
        return {ok = true}

    -- ----- Frame advance -----
    elseif cmd == "runFrames" then
        -- Deferred response: queue the request and count down each frame.
        -- The response is sent from on_frame() once frames_remaining hits 0.
        local count = req.count or 1
        table.insert(pending_frames, {
            client = sock,
            frames_remaining = count,
            id = req.id
        })
        return nil -- nil signals "don't send response now"

    -- ----- Input state -----
    elseif cmd == "getKeys" then
        -- Return a list of button names currently pressed by the player
        local keys = emu:getKeys()
        local result = {}
        for name, gba_key in pairs(BUTTON_MAP) do
            if keys & gba_key ~= 0 then
                table.insert(result, name)
            end
        end
        return {ok = true, value = result}

    -- ----- Health check -----
    elseif cmd == "ping" then
        return {ok = true, value = "pong"}

    else
        return {ok = false, error = "unknown command: " .. cmd}
    end
end


-- ==========================================================================
-- CLIENT DATA PROCESSING
-- ==========================================================================
-- Reads available data from a client socket, appends to its buffer, and
-- processes any complete newline-terminated JSON messages.
-- ==========================================================================

local function process_client(sock)
    -- Only read if data is available (non-blocking check)
    if sock.hasdata and not sock:hasdata() then return end

    local data, err = sock:receive(1024)
    if not data then
        -- No data or error — check for real disconnect
        if err and err ~= "EAGAIN" and (not socket.ERRORS or err ~= socket.ERRORS.AGAIN) then
            for i, c in ipairs(clients) do
                if c.sock == sock then
                    table.remove(clients, i)
                    console:log("Client disconnected")
                    break
                end
            end
        end
        return
    end

    -- Look up this client's buffer
    local client_data = nil
    for _, c in ipairs(clients) do
        if c.sock == sock then
            client_data = c
            break
        end
    end
    if not client_data then return end

    -- Append new data to the client's buffer
    client_data.buffer = client_data.buffer .. data

    -- Process all complete newline-delimited JSON messages in the buffer
    while true do
        local nl = client_data.buffer:find("\n")
        if not nl then break end -- no complete message yet

        local line = client_data.buffer:sub(1, nl - 1)
        client_data.buffer = client_data.buffer:sub(nl + 1)

        if #line > 0 then
            -- Parse the JSON request
            local success, req = pcall(json_decode, line)
            if success and req then
                -- Dispatch to the command handler
                local ok2, resp = pcall(handle_command, sock, req)
                if ok2 then
                    if resp ~= nil then
                        -- Attach the request ID to the response for correlation
                        if req.id then resp.id = req.id end
                        send_response(sock, resp)
                    end
                    -- resp == nil means deferred (runFrames); response sent later
                else
                    -- Command handler threw an error
                    send_response(sock, {ok = false, error = "handler error: " .. tostring(resp), id = req.id})
                end
            else
                send_response(sock, {ok = false, error = "invalid JSON"})
            end
        end
    end
end


-- ==========================================================================
-- FRAME CALLBACKS
-- ==========================================================================

-- Called every frame by mGBA. Processes:
--   1. Pending button presses — injects active keys via emu:addKey()
--   2. Pending frame advances — counts down and sends deferred responses
local function on_frame()
    -- Clear all scripted keys first, then re-add only active ones.
    -- This prevents keys from being held permanently if addKey is persistent.
    pcall(function() emu:clearKeys() end)
    for _, gba_key in pairs(BUTTON_MAP) do
        pcall(function() emu:clearKey(gba_key) end)
    end

    -- Inject all currently-active button holds into the emulator
    local i = 1
    while i <= #pending_presses do
        local p = pending_presses[i]
        if p.frames_remaining > 0 then
            emu:addKey(p.key)
            p.frames_remaining = p.frames_remaining - 1
            i = i + 1
        else
            -- This press is done; remove it from the queue
            table.remove(pending_presses, i)
        end
    end

    -- Count down frame-advance requests and send responses when complete
    i = 1
    while i <= #pending_frames do
        local pf = pending_frames[i]
        pf.frames_remaining = pf.frames_remaining - 1
        if pf.frames_remaining <= 0 then
            -- Frame advance complete — send the deferred response
            local resp = {ok = true}
            if pf.id then resp.id = pf.id end
            pcall(send_response, pf.client, resp)
            table.remove(pending_frames, i)
        else
            i = i + 1
        end
    end
end

-- Accept any new incoming TCP connections (non-blocking)
local function check_new_connections()
    if not server then return end
    -- Only try accept if there's an incoming connection waiting
    if server.hasdata and not server:hasdata() then return end
    local sock, err = server:accept()
    if sock then
        table.insert(clients, {sock = sock, buffer = ""})
        console:log("Client connected")
    end
end

-- Main poll function: accept connections and read from all clients.
-- Registered as a "keysRead" callback so it runs every frame.
local function poll()
    check_new_connections()
    for _, c in ipairs(clients) do
        pcall(process_client, c.sock)
    end
end


-- ==========================================================================
-- INITIALIZATION
-- ==========================================================================
-- Binds the TCP server and registers mGBA frame callbacks.

local function init()
    server = socket.bind("127.0.0.1", PORT)
    if not server then
        console:error("Failed to bind to port " .. PORT)
        return
    end
    server:listen(1)
    console:log("mGBA TCP server listening on port " .. PORT)

    -- "frame" fires once per emulated frame — we use it for button injection
    -- and frame-advance countdown
    callbacks:add("frame", on_frame)

    -- "keysRead" also fires every frame — we use it to poll for network I/O
    callbacks:add("keysRead", poll)
end

init()
