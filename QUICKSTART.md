# Quick Start Guide

## Installation

```bash
git clone https://github.com/ap0ught/scaling-garbanzo.git
cd scaling-garbanzo
```

## Basic Usage

### 1. Preview what will happen (Dry Run)
```bash
python rom_organizer.py /path/to/your/roms /path/to/organized --dry-run
```

This will show you:
- How many ROMs were found
- What platforms were detected
- Where each file will be moved
- No files are actually moved

### 2. Organize your ROMs (with copy)
```bash
python rom_organizer.py /path/to/your/roms /path/to/organized --copy
```

This will:
- Copy (not move) your ROMs to the organized structure
- Keep your original files intact
- Create `/roms/{platform}/` and `/bios/{platform}/` folders

### 3. Organize with hash verification
```bash
python rom_organizer.py /path/to/your/roms /path/to/organized --hash --copy
```

This will:
- Calculate MD5 hash for each file (default)
- Display hashes for verification with Redump
- Copy files to organized structure

### 4. Organize with SHA-1 hashes (for RetroAchievements)
```bash
python rom_organizer.py /path/to/your/roms /path/to/organized --hash --hash-algorithm sha1 --copy
```

This will:
- Calculate SHA-1 hash for each file
- Display hashes for verification with RetroAchievements
- Copy files to organized structure

## Example Workflow

```bash
# Step 1: See what you have
python rom_organizer.py ~/Downloads/roms ~/RetroGaming --dry-run

# Step 2: Copy files to organized structure
python rom_organizer.py ~/Downloads/roms ~/RetroGaming --copy

# Step 3: Verify with SHA-1 hashes for RetroAchievements (optional)
python rom_organizer.py ~/Downloads/roms ~/RetroGaming --hash --hash-algorithm sha1 --dry-run
```

## Result Structure

After running the organizer, your files will be in:

```
~/RetroGaming/
├── roms/
│   ├── nes/          # All NES ROMs
│   ├── snes/         # All SNES ROMs
│   ├── psx/          # All PlayStation ROMs
│   └── ...
└── bios/
    ├── psx/          # PlayStation BIOS files
    ├── ps2/          # PS2 BIOS files
    └── ...
```

## Tips

1. **Always start with --dry-run** to preview changes
2. **Use --copy** to keep your originals safe
3. **Use --hash with --hash-algorithm sha1** to verify ROMs for RetroAchievements compatibility
4. **Use --hash with MD5** (default) for Redump database verification
5. The tool reads ROM headers to reliably detect platforms even with ambiguous file extensions
6. Keep source ROMs in platform folders for better detection when header signatures are unavailable
7. **Use --verbose** to see detailed progress and which directories are being skipped
8. **Use --limit** for testing on large collections (e.g., `--limit 100` processes first 100 files)
9. Media directories (imgs, artwork, screenshots) are automatically skipped

## Common Issues

**"Unknown platform files" reported?**
- The file extension might not be in our database
- Manually move these to the correct platform folder after organization

**Files not detected?**
- Make sure file extensions are correct (.nes, .sfc, .bin, etc.)
- Check that files aren't corrupted or renamed incorrectly

**Need to add a platform?**
- Edit the `ROM_EXTENSIONS` dictionary in `rom_organizer.py`
- Or open an issue on GitHub
