# ROM Organizer

A Python tool to organize your game ROM collection into a clean, platform-based directory structure.

## Features

- 🗂️ **Automatic Organization**: Scans directories recursively and organizes ROMs by platform
- 🎮 **Multi-Platform Support**: Supports 20+ gaming platforms (NES, SNES, PlayStation, Genesis, etc.)
- 🔬 **Header Detection**: Reads ROM file headers to reliably identify platforms even with ambiguous extensions
- 📦 **Archive Support**: Handles ZIP, 7z, and RAR archives for arcade/MAME ROMs
- 📃 **Playlist Support**: Recognizes .m3u playlist files for multi-disc games
- 🔤 **System Aliases**: Accepts multiple naming conventions (ps1→psx, tg16→pcengine, megadrive→genesis)
- 🎯 **Format Preferences**: Smart ordering prefers CHD over ISO/BIN, native ROM formats over generic bins
- 🔐 **Hash Calculation**: Calculate MD5/SHA-1/SHA-256 hashes for ROM verification with Redump and ROM Vault
- 🎯 **RetroAchievements Integration**: Use RAHasher for achievement-compatible hashing with `--ra-hash`
- 🔄 **Duplicate Detection**: Identifies duplicate ROMs by hash across platforms
- 🗑️ **Delete Duplicates**: Automatically delete duplicate files with `--delete-duplicates`
- ⚡ **Multithreaded Hashing**: Calculate hashes in parallel after moving files for faster processing
- 🧬 **BIOS Detection**: Automatically identifies and separates BIOS files from game ROMs
- 🚫 **Smart Directory Exclusion**: Automatically skips media directories (imgs, artwork, screenshots, etc.)
- 🖼️ **Include Images Option**: Optionally include image/media directories with `--include-images`
- 🏷️ **Platform Display**: Shows platform name for each file being processed
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

# Use RetroAchievements-compatible hashing (requires RAHasher installed)
python rom_organizer.py /path/to/messy/roms /path/to/organized --ra-hash --copy

# Calculate SHA-1 hashes for general verification
python rom_organizer.py /path/to/messy/roms /path/to/organized --hash --hash-algorithm sha1

# Verbose mode to see detailed progress
python rom_organizer.py /path/to/messy/roms /path/to/organized --verbose --dry-run

# Process only first 100 files (testing)
python rom_organizer.py /path/to/messy/roms /path/to/organized --limit 100 --dry-run

# Use multithreaded hashing (faster for large collections)
python rom_organizer.py /path/to/messy/roms /path/to/organized --hash --multithreaded --threads 8

# Include image directories (move imgs, artwork, etc.)
python rom_organizer.py /path/to/messy/roms /path/to/organized --include-images

# Delete duplicate files automatically
python rom_organizer.py /path/to/messy/roms /path/to/organized --hash --delete-duplicates
```

### RetroAchievements Integration

For RetroAchievements achievement tracking, use the `--ra-hash` flag to call the external RAHasher tool:

```bash
# Organize with RetroAchievements-compatible hashing
python rom_organizer.py /path/to/messy/roms /path/to/organized --ra-hash --copy

# With multithreading for faster processing
python rom_organizer.py /path/to/messy/roms /path/to/organized --ra-hash --multithreaded --threads 8

# Dry run to test without moving files
python rom_organizer.py /path/to/messy/roms /path/to/organized --ra-hash --dry-run --verbose
```

**Important Notes**:
- The `--ra-hash` flag requires [RAHasher](https://github.com/RetroAchievements/RALibretro) to be installed and available in your PATH
- RAHasher only works with **game ROM files**, not BIOS files (BIOS files will show hash calculation failures)
- The tool automatically maps platform names to RAHasher system keys (e.g., `gba` → `GBA`, `psx` → `PS`, `genesis` → `MD`)
- Platforms without RAHasher support will show "No RAHasher system mapping" in verbose mode
- Use `--verbose` flag to see detailed error messages from RAHasher for debugging
- Archives (.zip) containing non-ROM files (like .png images) will be skipped
- See `RETROACHIEVEMENTS_HASHING.md` for installation instructions and troubleshooting

### Command-Line Options

| Option | Description |
|--------|-------------|
| `source` | Source directory to scan for ROMs (required) |
| `target` | Target directory for organized ROMs (required) |
| `--dry-run` | Show what would be done without actually moving files |
| `--copy` | Copy files instead of moving them |
| `--hash` | Calculate and display hashes for ROM verification (MD5/SHA-1/SHA-256) |
| `--ra-hash` | Use RetroAchievements-compatible hashing via RAHasher (requires RAHasher installed) |
| `--hash-algorithm` | Hash algorithm for `--hash`: `md5`, `sha1`, or `sha256` (default: `md5`) |
| `-v`, `--verbose` | Enable verbose output showing detailed scanning progress |
| `--limit` | Limit the number of files to process (useful for testing) |
| `--multithreaded` | Use multithreaded hashing after moving files (faster) |
| `--threads` | Number of threads for multithreaded hashing (default: 4) |
| `--include-images` | Include image/media directories instead of excluding them |
| `--delete-duplicates` | Delete duplicate files instead of skipping them (requires `--hash` or `--ra-hash`) |

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

You can then verify these hashes against Redump, ROM Vault, or other ROM verification databases.

### RetroAchievements Hash Verification

**Important**: The hash calculations above use **standard file hashing** (entire file MD5/SHA-1/SHA-256), which is different from RetroAchievements' platform-specific hashing methods.

For **RetroAchievements achievement compatibility**, you need to use specialized tools like:
- **RAHasher** (official tool) - produces exact RA hashes
- **rcheevos** library - for custom integration
- **RetroArch UI** - for quick visual verification

📖 **See the complete guide**: [RETROACHIEVEMENTS_HASHING.md](RETROACHIEVEMENTS_HASHING.md)

This guide explains:
- How RA hashing differs from standard file hashing
- How to use RAHasher for RA hash generation
- When to use each hashing method
- Integration workflows with this ROM organizer

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

### Including Image Directories

If you want to move image/media directories along with your ROMs, use the `--include-images` flag:

```bash
python rom_organizer.py /roms /organized --include-images
```

This will include all directories that would normally be excluded (imgs, artwork, screenshots, etc.) and organize their contents by platform.

**Use cases:**
- Moving an entire ROM collection including artwork/screenshots
- Backing up complete ROM sets with all media files
- Reorganizing a collection where images are organized by platform

## Archive Support

The tool handles multiple archive formats intelligently:

### Supported Archive Formats
- **ZIP** (`.zip`)
- **7-Zip** (`.7z`)
- **RAR** (`.rar`)

### How it works
- **Inspects archive contents**: Opens archives to detect ROM types inside
- **Arcade/MAME ROMs**: Archive files are commonly used for arcade games and are automatically organized into `arcade` platform
- **ROM detection**: If the archive contains identifiable ROM files (by extension), the tool will try to detect the platform
- **Preserved format**: Archives are moved as-is, not extracted

**Example**: A `.7z` file containing `.bin` files in an arcade directory will be organized as an arcade ROM.

## System Aliases

The tool accepts multiple naming conventions for the same platform:

| Alias | Canonical Platform |
|-------|-------------------|
| `ps1`, `psone` | `psx` |
| `tg16`, `turbografx16`, `pce` | `pcengine` |
| `pcecd` | `pcenginecd` |
| `megadrive`, `md` | `genesis` |
| `dc` | `dreamcast` |
| `sms` | `mastersystem` |
| `gg` | `gamegear` |

**Example**: ROMs in a directory named `/ps1/` will be organized as PlayStation (psx) ROMs.

## Format Preferences

The tool includes smart format ordering for when multiple versions of the same game exist:

### Disc-Based Systems
- **Prefers**: CHD → ISO/CSO → CUE/BIN
- **Reason**: CHD is more compressed and efficient
- **Systems**: PlayStation, PS2, PSP, Dreamcast, Saturn, Sega CD, PC Engine CD, 3DO

### Cartridge-Based Systems
- **Prefers**: Native formats (`.nes`, `.sfc`, `.z64`) → Generic `.bin`
- **Reason**: Native formats have proper headers and metadata
- **Systems**: NES, SNES, N64, Game Boy, GBA, NDS

### Arcade Systems
- **Prefers**: ZIP → 7z → RAR
- **Systems**: MAME, FBA, Neo Geo, Arcade

### Playlist Support
Multi-disc games often use `.m3u` playlist files to group disc images together. The tool recognizes these for:
- PlayStation (PSX)
- PlayStation 2 (PS2)
- Sega CD
- Saturn
- Dreamcast
- PC Engine CD
- 3DO

**Example**: `Final Fantasy VII.m3u` along with its disc `.bin`/`.cue` files will all be organized together.

## Multithreaded Hashing

For large ROM collections, hash calculation can be slow. The tool supports multithreaded hashing:

```bash
# Move files first, then calculate hashes in parallel
python rom_organizer.py /roms /organized --hash --multithreaded --threads 8
```

**Benefits:**
- Moves files quickly without waiting for hash calculation
- Calculates hashes in parallel using multiple CPU cores
- Displays all hashes together after processing
- Ideal for large collections (100+ files)

**How it works:**
1. Files are moved/copied to destination first
2. Hash calculation happens in parallel using thread pool
3. Progress is shown during calculation
4. All hashes are displayed at the end

Use `--threads N` to control the number of parallel hash calculations (default: 4).

## Duplicate Detection

When using hash calculation (`--hash`), the tool automatically detects duplicate ROMs:

```bash
python rom_organizer.py /roms /organized --hash --hash-algorithm sha1 --dry-run
```

**Output example:**
```
  Platform: psx (2 files)
    Would move: Castlevania X.iso [Platform: PSX] (SHA1: ecdb3675c7238c0e94d256801aa7655b24f47cac)
    Would move: Bomberman (US).iso [Platform: PSX] (SHA1: c514eace1667e74c959ec218d7e12f46dc7754b9)

  Platform: ps2 (1 files)
    ⚠️  Duplicate: Bomberman (US).iso [Platform: PS2] (SHA1: c514eace1667e74c959ec218d7e12f46dc7754b9) - same as Bomberman (US).iso [PSX]
```

**Features:**
- Detects duplicate files by comparing hashes
- Shows which file it's a duplicate of and from which platform
- Works across different platforms (e.g., a ROM mistakenly in PS2 folder that's actually a PSX game)
- Prevents moving duplicate files (skips them with a warning by default)
- Platform name shown in square brackets for easy identification: `[Platform: PSX]`

**Duplicate types detected:**
1. **Filename duplicates**: Files with the same name already in destination
2. **Hash duplicates**: Different filenames but identical content (detected via hash)

### Deleting Duplicates Automatically

Use the `--delete-duplicates` flag to automatically delete duplicate files instead of just warning about them:

```bash
python rom_organizer.py /roms /organized --hash --delete-duplicates
```

**Output example:**
```
  Platform: nes (1 files)
    Would move: game1.nes [Platform: NES] (MD5: 5570629d24c9f035bbb7ba308a1e2aab)

  Platform: psx (1 files)
    🗑️  Deleting duplicate: game1.iso [Platform: PSX] (MD5: 5570629d24c9f035bbb7ba308a1e2aab) - same as game1.nes [NES]

🗑️  Deleted 1 duplicate file(s)
```

**Important notes:**
- Requires `--hash` to be enabled (cannot delete duplicates without hash verification)
- Only deletes files that are exact duplicates (same hash)
- First file encountered is kept, subsequent duplicates are deleted
- Use `--dry-run` first to preview what would be deleted
- Deleted files are removed permanently

**Safety:**
Always use `--dry-run` first to verify which files would be deleted:
```bash
python rom_organizer.py /roms /organized --hash --delete-duplicates --dry-run
```

## Platform Display

All output now shows the platform for each file being processed:

```
Would move: game.iso [Platform: PSX]
Moved: rom.nes [Platform: NES]
```

This makes it clear which platform each ROM belongs to, especially helpful when organizing large collections.

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide with common workflows
- **[PLATFORMS.md](PLATFORMS.md)** - Complete platform reference with all supported systems and file extensions
- **[RETROACHIEVEMENTS_HASHING.md](RETROACHIEVEMENTS_HASHING.md)** - Guide to RetroAchievements hash verification and tools
- **[config.json.example](config.json.example)** - Example configuration for custom platform definitions

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