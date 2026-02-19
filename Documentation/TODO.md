# TODO - Pokemon Fire Red MCP

## Screenshot Pipeline
- [x] Fix screenshot viewing - currently times out when Claude tries to read base64 data URI directly
- [x] Solution: Save base64 PNG to disk via Python helper, then use Read tool on the saved .png file
- [x] Create a `save_screenshot.py` helper with `ScreenshotManager` class (session IDs, labels, timestamps)
- [x] Add screenshot helper as an MCP tool so it saves to disk automatically (`get_screenshot` now saves to disk)

## Battle Detection
- [x] Detect battles without user telling us — read memory to check battle state
- [x] Fire Red US v1.0 battle flag address identified: `gBattleTypeFlags` at `0x02022B4C`
- [x] Implement `get_battle_state` MCP tool (reads battle type, outcome, battler count)

## Battle Handling
- [x] Read opponent Pokemon data from memory during battle (`get_opponent_pokemon`, `get_opponent_party`)
- [ ] After battle animation opens (~3 seconds / ~180 frames), press A to proceed
- [ ] Need to handle: move selection, item usage, switching, running
- [ ] Map out the battle menu flow (Fight / Bag / Pokemon / Run)
- [ ] Add move name lookup table (currently moves only have IDs)

## Menu Cursor Tracking
- [x] The start menu **remembers cursor position** between opens — must track where cursor currently is
- [x] Read menu cursor position from memory: `sStartMenuCursorPos` at `0x020370F4`
- [x] Menu order array: `sStartMenuOrder` at `0x020370F6` (9 bytes, maps cursor → option enum)
- [x] Menu order (0-indexed enum): 0=Pokedex, 1=Pokemon, 2=Bag, 3=Player, 4=Save, 5=Option, 6=Exit
- [x] Implemented `get_start_menu_state` MCP tool that reads cursor position and resolves to option name

## In-Game Save MCP Tool
- [x] Create `save_game` MCP tool that performs the in-game save via menu navigation
- [x] Safest approach: reset cursor to top first (UP x8), then DOWN x4 to Save
- [x] Sequence: START > UP×8 > DOWN×4 > A > A (confirm) > wait > A (overwrite) > wait > A (dismiss) > B
- [x] Distinct from emulator save states (`save_state`/`load_state`) which are instant snapshots
- [ ] Consider adding a `load_game` tool that resets and loads from .sav (soft reset: A+B+START+SELECT)

## Future Work
- [ ] Add move name lookup table (Gen 3 move ID → name)
- [ ] Add item name lookup table (Gen 3 item ID → name)
- [ ] Battle action tools: `use_move(slot)`, `use_item(item_id)`, `switch_pokemon(slot)`, `run_from_battle()`
- [ ] Wild encounter rate detection / repel tracking
- [ ] Map name lookup from map_group + map_num
- [ ] PC box reading and management
