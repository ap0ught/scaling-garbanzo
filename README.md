# ROM Organizer

A Python tool to organize your game ROM collection into a clean, platform-based directory structure.

## Features

- 🗂️ **Automatic Organization**: Scans directories recursively and organizes ROMs by platform
- 🎮 **Multi-Platform Support**: Supports 20+ gaming platforms (NES, SNES, PlayStation, Genesis, etc.)
- 🔐 **Hash Calculation**: Calculate MD5/SHA1 hashes for ROM verification with RetroAchievements and Redump
- 🧬 **BIOS Detection**: Automatically identifies and separates BIOS files from game ROMs
- 🔍 **Dry Run Mode**: Preview changes before actually moving files
- 📋 **Copy Mode**: Option to copy files instead of moving them

## Directory Structure

The tool organizes files following **Structure A (Recommended)**:

```
/roms/{platform}/    # Contains all game files for that platform
/bios/{platform}/    # Contains all BIOS files for that platform
```

### Example Output:
```
organized/
├── roms/
│   ├── nes/
│   │   ├── Super Mario Bros.nes
│   │   └── Legend of Zelda.nes
│   ├── snes/
│   │   ├── Super Metroid.sfc
│   │   └── Chrono Trigger.smc
│   ├── psx/
│   │   ├── Final Fantasy VII.bin
│   │   └── Final Fantasy VII.cue
│   └── gba/
│       └── Pokemon Emerald.gba
└── bios/
    ├── psx/
    │   └── scph1001.bin
    └── ps2/
        └── ps2-bios.bin
```

## Installation

### Requirements
- Python 3.6 or higher (no additional dependencies required)

### Setup
```bash
git clone https://github.com/ap0ught/scaling-garbanzo.git
cd scaling-garbanzo
chmod +x rom_organizer.py
```

## Usage

### Basic Usage

```bash
# Dry run (preview what will happen)
python rom_organizer.py /path/to/messy/roms /path/to/organized --dry-run

# Organize ROMs (move files)
python rom_organizer.py /path/to/messy/roms /path/to/organized

# Copy files instead of moving
python rom_organizer.py /path/to/messy/roms /path/to/organized --copy

# Calculate MD5 hashes for verification
python rom_organizer.py /path/to/messy/roms /path/to/organized --hash
```

### Command-Line Options

| Option | Description |
|--------|-------------|
| `source` | Source directory to scan for ROMs (required) |
| `target` | Target directory for organized ROMs (required) |
| `--dry-run` | Show what would be done without actually moving files |
| `--copy` | Copy files instead of moving them |
| `--hash` | Calculate and display MD5 hashes for ROM verification |

### Examples

**Preview organization:**
```bash
python rom_organizer.py ~/Downloads/roms ~/RetroGaming/organized --dry-run
```

**Organize with hash calculation (for RetroAchievements verification):**
```bash
python rom_organizer.py ~/Downloads/roms ~/RetroGaming/organized --hash --copy
```

**Move files and organize:**
```bash
python rom_organizer.py ~/Downloads/roms ~/RetroGaming/organized
```

## Supported Platforms

The tool automatically detects and organizes ROMs for the following platforms:

### Nintendo
- NES (Nintendo Entertainment System)
- SNES (Super Nintendo)
- Nintendo 64
- Game Boy / Game Boy Color / Game Boy Advance
- Nintendo DS

### Sega
- Genesis/Mega Drive
- Master System
- Game Gear
- Dreamcast
- Saturn
- Sega CD

### Sony
- PlayStation (PSX)
- PlayStation 2 (PS2)
- PlayStation Portable (PSP)

### Atari
- Atari 2600
- Atari 7800
- Atari Lynx
- Atari Jaguar

### Others
- PC Engine / TurboGrafx-16
- PC Engine CD
- Neo Geo / Neo Geo CD
- 3DO
- Arcade (MAME, FBA)

## Hash Verification

The tool can calculate MD5 hashes to help verify your ROMs against databases like:

### Tools to Find/Check Hashes
- **RetroAchievements (RA) Hasher (RAHasher)**: Verify ROMs are compatible with RetroAchievements
- **ROM Vault/Redump**: Check ROM dumps against verified databases
- **No-Intro**: Validate your collection against No-Intro DAT files

Example with hash calculation:
```bash
python rom_organizer.py ~/roms ~/organized --hash --dry-run
```

Output will include:
```
Moving: Super Mario Bros.nes (MD5: 811b027eaf99c2def7b933c5208636de)
```

You can then verify these hashes against RetroAchievements or Redump databases.

## Platform Detection

The tool uses two methods to detect platforms:

1. **File Extension**: Matches common ROM extensions to platforms
2. **Directory Structure**: Looks for platform names in the source path

For best results:
- Use standard ROM file extensions
- Keep ROMs in platform-specific folders in your source directory
- BIOS files are automatically detected by filename keywords (bios, boot, firmware, scph, etc.)

## BIOS File Detection

BIOS files are automatically identified by common keywords:
- bios
- boot
- firmware
- syscard
- system
- scph (PlayStation BIOS)
- ps- (PlayStation prefix)

## Contributing

Contributions are welcome! Feel free to:
- Add support for more platforms
- Improve platform detection logic
- Add new features
- Fix bugs

## License

This project is open source and available for personal use.

## Troubleshooting

**Unknown files reported:**
If files are marked as "unknown platform", they may:
- Have uncommon extensions not in the database
- Be in an unsupported platform format
- Need manual organization

You can manually add them to the appropriate platform folder after organization.

**Duplicate files:**
The tool will skip files that already exist in the destination to prevent overwrites.

## Safety Features

- **Dry run mode**: Always test with `--dry-run` first
- **Copy mode**: Use `--copy` to keep originals intact
- **Duplicate detection**: Won't overwrite existing files
- **Path validation**: Validates source and target directories before processing