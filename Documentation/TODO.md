# TODO - Pokemon Fire Red MCP

## Screenshot Pipeline
- [ ] Fix screenshot viewing - currently times out when Claude tries to read base64 data URI directly
- [ ] Solution: Save base64 PNG to disk via Python helper, then use Read tool on the saved .png file
- [ ] Create a `save_screenshot.py` helper script in `scripts/`

## Battle Detection
- [ ] Detect battles without user telling us — read memory to check battle state
- [ ] Fire Red US v1.0 battle flag address needs to be identified (likely in IWRAM or SaveBlock)
- [ ] Implement a `get_battle_state` or `is_in_battle` MCP tool

## Battle Handling
- [ ] After battle animation opens (~3 seconds / ~180 frames), press A to proceed
- [ ] Need to handle: move selection, item usage, switching, running
- [ ] Map out the battle menu flow (Fight / Bag / Pokemon / Run)
- [ ] Read opponent Pokemon data from memory during battle

## Menu Cursor Tracking
- [ ] The start menu **remembers cursor position** between opens — must track where cursor currently is
- [ ] Read menu cursor position from memory, OR track it in MCP server state
- [ ] Menu order (0-indexed): 0=Pokedex, 1=Pokemon, 2=Bag, 3=Save, 4=Option
- [ ] Before navigating, need to know current cursor pos to calculate correct number of UP/DOWN presses
- [ ] Alternatively: always press UP enough times to guarantee we're at top (Pokedex), then navigate from known position
- [ ] Find the memory address for the start menu cursor index in Fire Red US v1.0

## In-Game Save MCP Tool
- [ ] Create `save_game` MCP tool that performs the in-game save via menu navigation
- [ ] Must account for menu cursor position (see Menu Cursor Tracking above)
- [ ] Safest approach: reset cursor to top first, then DOWN x3 to Save
- [ ] Sequence: START > (reset to top) > DOWN x3 > A > A (confirm) > wait ~120 frames > A (overwrite if needed) > wait ~120 frames > A (dismiss) > B (close menu)
- [ ] Should verify save completed by checking memory or waiting adequate frames
- [ ] Distinct from emulator save states (`save_state`/`load_state`) which are instant snapshots
- [ ] Consider adding a `load_game` tool that resets and loads from .sav (soft reset: A+B+START+SELECT)

## General
- [ ] Add screenshot helper as an MCP tool so it saves to disk automatically
