# ROM Organizer

A Python tool to organize your game ROM collection into a clean, platform-based directory structure.

## Features

- 🗂️ **Automatic Organization**: Scans directories recursively and organizes ROMs by platform
- 🎮 **Multi-Platform Support**: Supports 20+ gaming platforms (NES, SNES, PlayStation, Genesis, etc.)
- 🔬 **Header Detection**: Reads ROM file headers to reliably identify platforms even with ambiguous extensions
- 🔐 **Hash Calculation**: Calculate MD5/SHA-1/SHA-256 hashes for ROM verification with RetroAchievements and Redump
- 🧬 **BIOS Detection**: Automatically identifies and separates BIOS files from game ROMs
- 🚫 **Smart Directory Exclusion**: Automatically skips media directories (imgs, artwork, screenshots, etc.)
- 🔍 **Dry Run Mode**: Preview changes before actually moving files
- 📋 **Copy Mode**: Option to copy files instead of moving them
- 📊 **Verbose Mode**: Detailed scanning progress output
- 🎯 **File Limiting**: Process a limited number of files for testing

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

# Calculate SHA-1 hashes (for RetroAchievements)
python rom_organizer.py /path/to/messy/roms /path/to/organized --hash --hash-algorithm sha1

# Verbose mode to see detailed progress
python rom_organizer.py /path/to/messy/roms /path/to/organized --verbose --dry-run

# Process only first 100 files (testing)
python rom_organizer.py /path/to/messy/roms /path/to/organized --limit 100 --dry-run
```

### Command-Line Options

| Option | Description |
|--------|-------------|
| `source` | Source directory to scan for ROMs (required) |
| `target` | Target directory for organized ROMs (required) |
| `--dry-run` | Show what would be done without actually moving files |
| `--copy` | Copy files instead of moving them |
| `--hash` | Calculate and display hashes for ROM verification |
| `--hash-algorithm` | Hash algorithm: `md5`, `sha1`, or `sha256` (default: `md5`) |
| `-v`, `--verbose` | Enable verbose output showing detailed scanning progress |
| `--limit` | Limit the number of files to process (useful for testing) |

### Examples

**Preview organization:**
```bash
python rom_organizer.py ~/Downloads/roms ~/RetroGaming/organized --dry-run
```

**Organize with SHA-1 hash calculation (for RetroAchievements verification):**
```bash
python rom_organizer.py ~/Downloads/roms ~/RetroGaming/organized --hash --hash-algorithm sha1 --copy
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

The tool supports multiple hash algorithms for ROM verification:

### Supported Hash Algorithms
- **MD5**: Standard checksum for general verification
- **SHA-1**: Used by RetroAchievements for achievement compatibility
- **SHA-256**: Modern cryptographic hash for enhanced security

### Tools to Find/Check Hashes
- **RetroAchievements (RA) Hasher (RAHasher)**: A command-line tool for finding hashes for achievement compatibility. Use SHA-1 with `--hash-algorithm sha1`
- **ROM Vault/Redump**: Databases with verified hashes for physical game dumps. Typically uses MD5 or SHA-1
- **No-Intro**: Validate your collection against No-Intro DAT files

### Examples

**Calculate MD5 hashes (Redump/general):**
```bash
python rom_organizer.py ~/roms ~/organized --hash --dry-run
```

**Calculate SHA-1 hashes (RetroAchievements):**
```bash
python rom_organizer.py ~/roms ~/organized --hash --hash-algorithm sha1 --dry-run
```

**Calculate SHA-256 hashes:**
```bash
python rom_organizer.py ~/roms ~/organized --hash --hash-algorithm sha256 --dry-run
```

Output examples:
```
Moving: Super Mario Bros.nes (MD5: 811b027eaf99c2def7b933c5208636de)
Moving: Legend of Zelda.nes (SHA1: 6681ccb20167f68c60ce5f6d3e044feef78f79ab)
```

You can then verify these hashes against RetroAchievements, Redump, or other ROM verification databases.

## Platform Detection

The tool uses multiple methods to detect platforms for accurate organization:

### Detection Methods (in priority order)

1. **Directory Structure**: Platform names in the source path (highest priority)
   - Example: `/roms/nes/game.bin` → detected as NES

2. **ROM Header Detection**: Reads file headers to identify platform signatures
   - **NES**: Checks for 'NES\x1a' header signature
   - **N64**: Detects big-endian, byte-swapped, and little-endian formats
   - **Game Boy/GBC**: Verifies Nintendo logo in header
   - **Genesis/Master System**: Looks for 'SEGA' signatures
   - **PlayStation**: Checks for system area signatures
   - And more...

3. **File Extension**: Matches common ROM extensions to platforms (fallback)

### Why Header Detection?

Many ROM formats share the same file extensions (`.bin`, `.iso`, `.img`), making extension-based detection unreliable. Header detection reads the actual ROM data to identify the platform accurately.

**Example**: A `.bin` file could be:
- Game Boy Advance ROM
- Sega Genesis ROM
- PlayStation disc image
- Atari 2600 ROM

The tool reads the file header to determine which platform it actually belongs to.

### For Best Results:
- Keep ROMs in platform-specific folders when possible
- Use standard ROM file extensions
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

## Directory Exclusion

The tool automatically skips common media directories to avoid moving non-ROM files:
- `imgs`, `images`, `img` - Image files, artwork
- `covers`, `cover` - Game cover art
- `screenshots`, `screenshot`, `snaps`, `snap` - Screenshots
- `artwork`, `art` - Artwork and graphics
- `videos`, `video` - Video files
- `manuals`, `manual`, `docs`, `documentation` - Manuals and documentation
- `preview`, `previews` - Preview images

**Example**: If you have a structure like `\GB\imgs\`, the `imgs` directory will be skipped and its contents won't be moved.

Use `--verbose` mode to see which directories are being skipped during scanning.

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