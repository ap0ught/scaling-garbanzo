# RetroAchievements Hash Verification Guide

## Overview

This guide explains how to generate **RetroAchievements (RA) hashes** locally for ROM verification and achievement compatibility. RA uses platform-specific hashing methods that differ from simple MD5/SHA-1 checksums.

## ⚠️ Important Note

The ROM organizer tool currently uses **standard file hashing** (MD5/SHA-1/SHA-256) which is suitable for:
- ✅ File verification (Redump, ROM Vault databases)
- ✅ Duplicate detection in your collection
- ✅ General ROM collection management

For **RetroAchievements achievement compatibility**, you need platform-specific hashing that handles:
- Header stripping (NES, SNES, PC Engine, etc.)
- Boot code extraction (PlayStation, Saturn, Dreamcast, etc.)
- Disc layout parsing (CUE/BIN, CHD formats)
- Custom per-platform hashing rules

---

## 🧰 Tools for RetroAchievements Hash Generation

Below are **three practical options** for generating RA-compatible hashes, from most official to most convenient.

---

## 🥇 Option 1: RAHasher (Official Tool) ⭐

**The gold standard** - produces the **exact RA hash** used by RetroAchievements servers.

### What it does

- Uses **RA's official hashing rules**
- Handles platform-specific requirements:
  - **Header stripping** 🧼 (removes headers before hashing)
  - **Partial-file hashing** 🧩 (hashes only relevant portions)
  - **Disc layouts** 💿 (CUE/BIN, CHD, ISO formats)
- Outputs the **Supported Game Files hash**

### How to use

```bash
# Cartridge-based ROMs
RAHasher yourfile.nes
RAHasher game.smc
RAHasher pokemon.gba

# Disc-based games
RAHasher game.cue
RAHasher game.chd
```

### Where to get it

- **GitHub**: [RetroAchievements/RAHasher](https://github.com/RetroAchievements/RAHasher)
- Often included in dev / contributor tooling
- Available for Windows, Linux, and macOS

### When to use

👉 **Best for**: Automation, ingestion pipelines, verification scripts, batch processing

---

## 🥈 Option 2: rcheevos Library 🧠

The **same hashing logic** that RetroArch uses internally.

### What it is

- **Library name**: `rcheevos`
- Used by RetroArch and other emulators
- Can be embedded in custom tools
- Available as C library with potential Python bindings

### Use cases

- CLI tools
- Django/web applications
- ROM scanner applications
- Metadata pipelines
- Custom ingestion systems

### Typical workflow

```text
1. Load ROM file
2. Normalize (handle headers, byte-swapping, etc.)
3. Compute RA hash using rcheevos
4. Compare to RetroAchievements server
```

### When to use

👉 **Best for**: Integrating RA hashing directly into your application, embedded systems, custom ROM managers

### Resources

- **GitHub**: [RetroAchievements/rcheevos](https://github.com/RetroAchievements/rcheevos)
- C library with documentation
- Integration examples available

---

## 🥉 Option 3: RetroArch UI (Quick Check) 👀

The **fastest way** to check a single file visually.

### Steps

1. Launch RetroArch
2. Load the game/ROM
3. Open **Quick Menu → Achievements**
4. Look for:
   - **Game Hash** (the RA hash)
   - **Hash Matches** (if game is recognized)
   - **Unsupported** (if no achievements available)

### Limitations

⚠️ Not scriptable
⚠️ Requires launching the game
⚠️ One file at a time

### When to use

👉 **Best for**: Spot-checking individual ROMs, verifying game recognition, troubleshooting achievement issues

---

## ❌ What NOT to Rely On

These methods **will NOT produce** RetroAchievements-compatible hashes:

- ❌ `md5sum file.rom` - doesn't strip headers
- ❌ `sha1sum file.rom` - full file hash, not RA hash
- ❌ Hashing `.zip` archives - RA hashes extracted content
- ❌ Standard Python `hashlib` - doesn't apply RA rules
- ❌ This ROM organizer's `--hash` flag - uses standard file hashing

**Why they don't work**: RA uses platform-specific normalization rules that must be applied before hashing.

---

## 🎯 Practical Recommendations

### For this ROM organizer:

1. **Use standard hashing** (`--hash` flag) for:
   - Duplicate detection
   - File verification against Redump
   - Collection management

2. **Use RAHasher separately** when you need:
   - RetroAchievements verification
   - Achievement compatibility checking
   - Submission to RA database

### Integration workflow:

```bash
# Step 1: Organize your ROMs
python rom_organizer.py /messy/roms /organized --copy

# Step 2: Verify RA hashes for organized ROMs
cd /organized/roms/nes
for rom in *.nes; do
    echo "Checking: $rom"
    RAHasher "$rom"
done
```

---

## 📚 Additional Resources

- **RetroAchievements Docs**: [Game Identification](https://docs.retroachievements.org/developer-docs/game-identification.html)
- **RAHasher GitHub**: [RetroAchievements/RAHasher](https://github.com/RetroAchievements/RAHasher)
- **rcheevos Library**: [RetroAchievements/rcheevos](https://github.com/RetroAchievements/rcheevos)
- **RetroAchievements**: [retroachievements.org](https://retroachievements.org)

---

## 🔮 Future Enhancement

Adding native RA hash support to this ROM organizer would require:

- Platform-specific hash functions for 30+ systems
- ISO/CD image parsing libraries
- Boot code extraction for disc-based systems
- Header detection and stripping logic
- Integration with rcheevos or RAHasher

This is a substantial feature that would significantly increase complexity. For now, using RAHasher as a separate tool is recommended.

---

**Note**: This documentation is provided to help users understand the difference between standard file hashing and RetroAchievements-specific hashing. The ROM organizer uses standard hashing for file management, while RAHasher should be used for achievement compatibility verification.
