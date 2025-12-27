# Platform Reference

This document lists all supported platforms and their file extensions recognized by the ROM Organizer.

## Nintendo Platforms

### NES (Nintendo Entertainment System)
- **Extensions:** `.nes`, `.unf`, `.unif`
- **Folder:** `roms/nes/`

### SNES (Super Nintendo)
- **Extensions:** `.smc`, `.sfc`, `.fig`, `.swc`, `.mgd`
- **Folder:** `roms/snes/`

### Nintendo 64
- **Extensions:** `.z64`, `.n64`, `.v64`
- **Folder:** `roms/n64/`

### Game Boy
- **Extensions:** `.gb`, `.sgb`
- **Folder:** `roms/gb/`

### Game Boy Color
- **Extensions:** `.gbc`, `.cgb`, `.sgb`
- **Folder:** `roms/gbc/`

### Game Boy Advance
- **Extensions:** `.gba`, `.agb`, `.bin`
- **Folder:** `roms/gba/`

### Nintendo DS
- **Extensions:** `.nds`, `.ids`
- **Folder:** `roms/nds/`

## Sega Platforms

### Genesis / Mega Drive
- **Extensions:** `.smd`, `.gen`, `.bin`
- **Folder:** `roms/genesis/`
- **Note:** `.md` extension removed to avoid conflict with Markdown documentation files

### Master System
- **Extensions:** `.sms`
- **Folder:** `roms/mastersystem/`

### Game Gear
- **Extensions:** `.gg`
- **Folder:** `roms/gamegear/`

### Sega CD / Mega CD
- **Extensions:** `.cue`, `.bin`, `.chd`
- **Folder:** `roms/segacd/`

### Saturn
- **Extensions:** `.cue`, `.bin`, `.mds`, `.mdf`, `.chd`
- **Folder:** `roms/saturn/`

### Dreamcast
- **Extensions:** `.cdi`, `.gdi`, `.chd`
- **Folder:** `roms/dreamcast/`

## Sony Platforms

### PlayStation (PSX/PS1)
- **Extensions:** `.bin`, `.cue`, `.img`, `.mdf`, `.pbp`, `.toc`, `.cbn`, `.m3u`, `.chd`
- **Folder:** `roms/psx/`
- **BIOS Folder:** `bios/psx/`
- **Common BIOS:** `scph1001.bin`, `scph5501.bin`, `scph7001.bin`

### PlayStation 2
- **Extensions:** `.iso`, `.bin`, `.img`, `.mdf`, `.z`, `.z2`, `.bz2`, `.dump`, `.cso`, `.ima`, `.gz`, `.chd`
- **Folder:** `roms/ps2/`
- **BIOS Folder:** `bios/ps2/`

### PlayStation Portable (PSP)
- **Extensions:** `.iso`, `.cso`, `.pbp`, `.elf`, `.prx`
- **Folder:** `roms/psp/`

## Atari Platforms

### Atari 2600
- **Extensions:** `.a26`, `.bin`
- **Folder:** `roms/atari2600/`

### Atari 7800
- **Extensions:** `.a78`
- **Folder:** `roms/atari7800/`

### Atari Lynx
- **Extensions:** `.lnx`, `.o`
- **Folder:** `roms/lynx/`

### Atari Jaguar
- **Extensions:** `.j64`, `.jag`
- **Folder:** `roms/jaguar/`

## Other Platforms

### PC Engine / TurboGrafx-16
- **Extensions:** `.pce`, `.sgx`
- **Folder:** `roms/pcengine/`

### PC Engine CD / TurboGrafx-CD
- **Extensions:** `.cue`, `.ccd`, `.chd`
- **Folder:** `roms/pcenginecd/`

### Neo Geo
- **Extensions:** `.zip`
- **Folder:** `roms/neogeo/`

### Neo Geo CD
- **Extensions:** `.cue`, `.chd`
- **Folder:** `roms/neogeocd/`

### 3DO Interactive Multiplayer
- **Extensions:** `.iso`, `.cue`, `.chd`
- **Folder:** `roms/3do/`

### Arcade (Generic)
- **Extensions:** `.zip`
- **Folder:** `roms/arcade/`

### MAME
- **Extensions:** `.zip`
- **Folder:** `roms/mame/`

### FinalBurn Alpha (FBA)
- **Extensions:** `.zip`
- **Folder:** `roms/fba/`

## BIOS File Detection

BIOS files are automatically detected by keywords in the filename:
- `bios`
- `boot`
- `firmware`
- `syscard`
- `system`
- `scph` (PlayStation BIOS prefix)
- `ps-` (PlayStation prefix)
- `playstation`

### Example BIOS Files
- `scph1001.bin` → Detected as PlayStation BIOS → `bios/psx/`
- `ps2-bios.bin` → Detected as PlayStation 2 BIOS → `bios/ps2/`
- `syscard3.pce` → Detected as PC Engine BIOS → `bios/pcengine/`

## Multi-Disc Games

For games with multiple discs (e.g., Final Fantasy VII):
- Keep all disc files (.bin, .cue) together
- Use `.m3u` playlist files for multi-disc PSX games
- All files will be organized into the same platform folder

Example:
```
Final Fantasy VII (Disc 1).bin
Final Fantasy VII (Disc 1).cue
Final Fantasy VII (Disc 2).bin
Final Fantasy VII (Disc 2).cue
Final Fantasy VII (Disc 3).bin
Final Fantasy VII (Disc 3).cue
Final Fantasy VII.m3u
```

All files go to: `roms/psx/`

## Adding Custom Platforms

To add a new platform or additional extensions:

1. Edit `rom_organizer.py`
2. Add entry to the `ROM_EXTENSIONS` dictionary:

```python
ROM_EXTENSIONS = {
    # ... existing platforms ...
    'newplatform': ['.ext1', '.ext2', '.ext3'],
}
```

3. The organizer will automatically create `roms/newplatform/` folder

## Platform Detection Priority

The tool uses two methods to detect platforms:

1. **Directory Name** (Highest Priority)
   - If ROM is in `/some/path/nes/game.bin`, it's detected as NES

2. **File Extension** (Fallback)
   - If directory doesn't indicate platform, extension is used
   - `.bin` files need directory context (used by multiple platforms)

**Best Practice:** Keep ROMs in platform-named folders for accurate detection
