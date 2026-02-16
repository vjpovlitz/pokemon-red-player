# Playing Pokemon Red (Original Game)

This guide covers how to play the original Pokemon Red using an emulator with your own ROM.

---

## Recommended Emulator: mGBA

**mGBA** is the best Game Boy / Game Boy Color emulator available:
- Highly accurate emulation
- Free and open source
- Active development
- Save state support
- Speed controls
- Controller support

**Website:** https://mgba.io

---

## Setup Instructions

### Step 1: Download mGBA

1. Go to https://mgba.io/downloads.html
2. Download the Windows 64-bit installer (`.exe`) or portable version (`.7z`)
3. Run the installer or extract the portable version to a folder

### Step 2: Organize Your Files

Create a folder structure for your games:

```
C:\Emulation\
├── mGBA\                  # Emulator installation
├── ROMs\
│   └── GameBoy\
│       └── Pokemon Red.gb  # Your ROM file
└── Saves\                 # Save files (optional organization)
```

### Step 3: Configure mGBA

1. Open mGBA
2. Go to **Tools > Settings**
3. Configure these recommended settings:

**Paths:**
- Set your ROMs folder as the default path
- Set a saves folder location

**Audio:**
- Sample rate: 48000 Hz
- Buffer size: 1024 (increase if you hear crackling)

**Video:**
- Filter: None (for crisp pixels) or Bilinear (for smoothing)
- Frame skip: 0
- Sync to video: Enabled

**Controllers:**
- Go to **Tools > Settings > Controllers**
- Map your keyboard or gamepad:

| Game Boy | Recommended Key | Alt Key |
|----------|-----------------|---------|
| D-Pad    | Arrow Keys      | WASD    |
| A        | Z               | Enter   |
| B        | X               | Backspace |
| Start    | Enter           | S       |
| Select   | Shift           | A       |
| L        | Q               |         |
| R        | E               |         |

### Step 4: Load Your ROM

1. **File > Load ROM** (or drag and drop the `.gb` file)
2. Select your `Pokemon Red.gb` file
3. The game will start automatically

---

## Essential Controls & Features

### Save States (Quick Save/Load)

Save your exact position anytime:

| Action | Shortcut |
|--------|----------|
| Quick Save | Shift + F1 through F9 |
| Quick Load | F1 through F9 |
| Save State Menu | File > Save State |
| Load State Menu | File > Load State |

**Tip:** Use save states before difficult battles or catching legendaries!

### Speed Controls

| Action | Shortcut |
|--------|----------|
| Fast Forward (hold) | Hold Tab |
| Toggle Fast Forward | Shift + Tab |
| Turbo (very fast) | Hold Shift + Tab |

**Tip:** Use fast forward to speed through grinding or long walks.

### Other Useful Shortcuts

| Action | Shortcut |
|--------|----------|
| Pause | Ctrl + P |
| Reset | Ctrl + R |
| Fullscreen | Ctrl + F |
| Screenshot | F12 |
| Mute | Ctrl + M |

---

## In-Game Saving vs Save States

**In-Game Save:**
- Press Start > SAVE in the game
- Creates a `.sav` file alongside your ROM
- Works just like on real hardware
- Persistent and reliable

**Save States:**
- Instant snapshot of exact game state
- Can save anywhere (even mid-battle)
- Great for risky situations
- Multiple slots available (F1-F9)

**Recommendation:** Use both! In-game save regularly, and use save states for backup before important moments.

---

## Troubleshooting

### Game Won't Load
- Ensure the file extension is `.gb` (not `.zip`)
- Verify the ROM isn't corrupted
- Try **File > Load ROM** instead of drag-and-drop

### No Sound
- Check **Audio > Mute** is not enabled
- Go to **Tools > Settings > Audio** and verify output device
- Try increasing buffer size if audio stutters

### Controls Not Working
- Go to **Tools > Settings > Controllers**
- Click on each button and press the key you want
- Make sure no duplicate mappings

### Save File Not Loading
- Ensure the `.sav` file has the same name as the ROM
- Example: `Pokemon Red.gb` needs `Pokemon Red.sav`
- Check that saves are in the same folder as the ROM

### Game Runs Too Fast/Slow
- Disable fast forward if enabled
- Check **Tools > Settings > Emulation** for sync settings
- Enable "Sync to video" for proper speed

---

## Alternative Emulators

If mGBA doesn't work for you:

| Emulator | Platform | Notes |
|----------|----------|-------|
| **BGB** | Windows | Very accurate, good debugger |
| **SameBoy** | Windows/Mac/Linux | High accuracy |
| **RetroArch** | Multi-platform | Uses mGBA/Gambatte cores |
| **Pizza Boy** | Android | Best mobile option |
| **Delta** | iOS | Requires sideloading |

---

## Pokemon Red Tips

### Starter Pokemon
- **Bulbasaur** - Easiest early game (strong vs first two gyms)
- **Charmander** - Harder early game, powerful late
- **Squirtle** - Balanced choice

### Essential Items to Get
- **Running Shoes** - Not in Gen 1! You walk everywhere
- **Bicycle** - Get from Cerulean City bike shop (need Bike Voucher)
- **HM01 Cut** - SS Anne from Captain
- **HM02 Fly** - Route 16, requires Cut

### Missable Pokemon
- **Snorlax** - Only 2 in game (Route 12 and 16)
- **Legendary Birds** - One each: Articuno, Zapdos, Moltres
- **Mewtwo** - Post-game only

### Useful Glitches (Optional)
Gen 1 has famous glitches if you want to experiment:
- Mew glitch (encounter Mew without cheats)
- Item duplication
- Walk through walls

---

## File Locations

After playing, your files will be:

```
mGBA\
├── mGBA.exe
├── config.ini          # Your settings
└── saves\              # Or same folder as ROM
    └── Pokemon Red.sav # Your save file
```

**Backup your `.sav` file regularly!**

---

## Quick Start Checklist

- [ ] Download mGBA from https://mgba.io/downloads.html
- [ ] Install or extract mGBA
- [ ] Place your Pokemon Red ROM in a known folder
- [ ] Open mGBA and load the ROM (File > Load ROM)
- [ ] Configure controls (Tools > Settings > Controllers)
- [ ] Play and enjoy!

---

## Resources

- **mGBA Official Site:** https://mgba.io
- **mGBA GitHub:** https://github.com/mgba-emu/mgba
- **Pokemon Red Walkthrough:** https://bulbapedia.bulbagarden.net/wiki/Appendix:Red_and_Blue_walkthrough
- **Pokedex:** https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_by_Kanto_Pok%C3%A9dex_number
