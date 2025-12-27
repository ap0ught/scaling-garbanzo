#!/usr/bin/env python3
"""
ROM Organizer - A tool to organize game ROMs and BIOS files

This script scans directories for game ROM files and organizes them into:
- /roms/{platform}/ - Contains all game files for that platform
- /bios/{platform}/ - Contains all BIOS files for that platform
"""

import os
import sys
import shutil
import hashlib
import argparse
from pathlib import Path
from typing import Dict, List, Optional


# Common ROM file extensions by platform
ROM_EXTENSIONS = {
    'nes': ['.nes', '.unf', '.unif'],
    'snes': ['.smc', '.sfc', '.fig', '.swc', '.mgd'],
    'n64': ['.z64', '.n64', '.v64'],
    'gba': ['.gba', '.agb', '.bin'],
    'gbc': ['.gbc', '.cgb', '.sgb'],
    'gb': ['.gb', '.sgb'],
    'nds': ['.nds', '.ids'],
    'genesis': ['.smd', '.gen', '.bin'],  # .md removed to avoid conflict with Markdown files
    'mastersystem': ['.sms'],
    'gamegear': ['.gg'],
    'psx': ['.bin', '.cue', '.img', '.mdf', '.pbp', '.toc', '.cbn', '.m3u', '.chd'],
    'ps2': ['.iso', '.bin', '.img', '.mdf', '.z', '.z2', '.bz2', '.dump', '.cso', '.ima', '.gz', '.chd'],
    'psp': ['.iso', '.cso', '.pbp', '.elf', '.prx'],
    'dreamcast': ['.cdi', '.gdi', '.chd'],
    'saturn': ['.cue', '.bin', '.mds', '.mdf', '.chd'],
    'atari2600': ['.a26', '.bin'],
    'atari7800': ['.a78'],
    'lynx': ['.lnx', '.o'],
    'jaguar': ['.j64', '.jag'],
    'segacd': ['.cue', '.bin', '.chd'],
    '3do': ['.iso', '.cue', '.chd'],
    'pcengine': ['.pce', '.sgx'],
    'pcenginecd': ['.cue', '.ccd', '.chd'],
    'neogeo': ['.zip'],
    'neogeocd': ['.cue', '.chd'],
    'arcade': ['.zip'],
    'mame': ['.zip'],
    'fba': ['.zip'],
}

# BIOS file keywords (case-insensitive)
BIOS_KEYWORDS = [
    'bios', 'boot', 'firmware', 'syscard', 'system',
    'scph', 'ps-', 'playstation',
]

# Pre-computed set of all ROM extensions for efficient lookup
ALL_ROM_EXTENSIONS = set(ext for exts in ROM_EXTENSIONS.values() for ext in exts)

# ROM header signatures for platform detection
# Format: platform -> list of (offset, signature_bytes)
ROM_HEADERS = {
    'nes': [(0, b'NES\x1a')],
    'snes': [
        # SNES ROMs may have a 512-byte SMC header, check for known patterns
        (0x7FC0, None),  # Internal header location (no-header ROM)
        (0x81C0, None),  # Internal header location (with SMC header)
    ],
    'n64': [
        (0, b'\x80\x37\x12\x40'),  # Big-endian (z64)
        (0, b'\x37\x80\x40\x12'),  # Byte-swapped (v64)
        (0, b'\x40\x12\x37\x80'),  # Little-endian (n64)
    ],
    'gba': [(0xA0, b'\x96')],  # Nintendo logo check
    'gb': [(0x104, b'\xCE\xED\x66\x66\xCC\x0D')],  # Nintendo logo start
    'gbc': [(0x104, b'\xCE\xED\x66\x66\xCC\x0D')],  # Same as GB
    'genesis': [
        (0x100, b'SEGA'),  # Sega Genesis header
        (0x100, b'SEGADISCSYSTEM'),  # Sega CD
    ],
    'mastersystem': [(0x7FF0, b'TMR SEGA')],
    'psx': [
        # PSX discs use .cue + .bin, check for specific patterns in bin files
        (0x9320, b'PLAYSTATION'),  # Common location in system area
    ],
    'saturn': [(0, b'SEGA SEGASATURN')],
    'dreamcast': [(0, b'SEGA SEGAKATANA')],
}


def read_file_header(filepath: Path, offset: int, length: int) -> Optional[bytes]:
    """Read bytes from a file at a specific offset."""
    try:
        with open(filepath, 'rb') as f:
            f.seek(offset)
            return f.read(length)
    except (IOError, OSError):
        return None


def detect_platform_from_header(filepath: Path) -> Optional[str]:
    """
    Detect platform by reading ROM file headers.
    Returns platform name or None if no match found.
    """
    for platform, signatures in ROM_HEADERS.items():
        for offset, signature in signatures:
            if signature is None:
                continue
            
            header_data = read_file_header(filepath, offset, len(signature))
            if header_data and header_data == signature:
                return platform
            
            # For some platforms, check if signature appears anywhere in the header
            if platform in ['genesis', 'mastersystem']:
                header_data = read_file_header(filepath, offset, 256)
                if header_data and signature in header_data:
                    return platform
    
    return None


def calculate_hash(filepath: Path, algorithm: str = 'md5') -> str:
    """Calculate hash of a file."""
    try:
        hash_func = hashlib.new(algorithm)
    except ValueError:
        print(f"Warning: Unsupported hash algorithm '{algorithm}', using MD5", file=sys.stderr)
        hash_func = hashlib.md5()
    
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def is_bios_file(filename: str) -> bool:
    """Check if a file is likely a BIOS file based on its name."""
    filename_lower = filename.lower()
    return any(keyword in filename_lower for keyword in BIOS_KEYWORDS)


def detect_platform(filepath: Path, extension: str) -> Optional[str]:
    """
    Detect the platform for a ROM file based on header signature, extension, and path.
    Returns the platform name or None if unknown.
    """
    # Check parent directory names for platform hints (highest priority)
    parent_parts = [p.lower() for p in filepath.parts]
    
    # Try to match platform from directory structure
    for platform in ROM_EXTENSIONS.keys():
        if platform in parent_parts:
            return platform
    
    # Try header-based detection for files with ambiguous extensions
    ext_lower = extension.lower()
    if ext_lower in ['.bin', '.iso', '.img']:
        # These extensions are shared across platforms, try header detection
        header_platform = detect_platform_from_header(filepath)
        if header_platform:
            return header_platform
    
    # For cartridge-based systems, always try header detection
    if ext_lower in ['.nes', '.gba', '.gb', '.gbc', '.z64', '.n64', '.v64', '.smd', '.gen', '.sms']:
        header_platform = detect_platform_from_header(filepath)
        if header_platform:
            return header_platform
    
    # Try to match by extension (fallback)
    for platform, extensions in ROM_EXTENSIONS.items():
        if ext_lower in extensions:
            # If multiple platforms share an extension, prefer more specific detection
            if ext_lower in ['.bin', '.iso', '.cue', '.img']:
                # These are generic, try to detect from path first
                for platform_name in ROM_EXTENSIONS.keys():
                    if platform_name in parent_parts:
                        return platform_name
            return platform
    
    return None


def scan_directory(source_dir: Path) -> Dict[str, List[Path]]:
    """
    Recursively scan a directory for ROM and BIOS files.
    Returns a dictionary mapping platforms to lists of files.
    """
    results = {
        'roms': {},
        'bios': {},
        'unknown': []
    }
    
    print(f"Scanning directory: {source_dir}")
    
    for root, dirs, files in os.walk(source_dir):
        root_path = Path(root)
        
        for filename in files:
            filepath = root_path / filename
            extension = filepath.suffix
            
            # Skip non-ROM files
            if not extension:
                continue
            
            # Detect platform
            platform = detect_platform(filepath, extension)
            
            if platform:
                # Determine if it's a BIOS file
                if is_bios_file(filename):
                    if platform not in results['bios']:
                        results['bios'][platform] = []
                    results['bios'][platform].append(filepath)
                else:
                    if platform not in results['roms']:
                        results['roms'][platform] = []
                    results['roms'][platform].append(filepath)
            else:
                # Unknown platform
                if extension.lower() in ALL_ROM_EXTENSIONS:
                    results['unknown'].append(filepath)
    
    return results


def organize_files(results: Dict, target_dir: Path, dry_run: bool = False, 
                   copy_mode: bool = False, calculate_hashes: bool = False,
                   hash_algorithm: str = 'md5'):
    """
    Organize the scanned files into the target directory structure.
    
    Args:
        results: Dictionary from scan_directory
        target_dir: Root directory for organized files
        dry_run: If True, only show what would be done without moving files
        copy_mode: If True, copy files instead of moving them
        calculate_hashes: If True, calculate and display file hashes
        hash_algorithm: Hash algorithm to use ('md5', 'sha1', 'sha256')
    """
    action = "Would copy" if dry_run and copy_mode else "Would move" if dry_run else "Copying" if copy_mode else "Moving"
    
    # Organize ROMs
    print(f"\n{action} ROMs:")
    for platform, files in results['roms'].items():
        platform_dir = target_dir / 'roms' / platform
        
        if not dry_run:
            platform_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n  Platform: {platform} ({len(files)} files)")
        for filepath in files:
            dest_path = platform_dir / filepath.name
            
            if calculate_hashes:
                file_hash = calculate_hash(filepath, hash_algorithm)
                hash_label = hash_algorithm.upper()
                print(f"    {action}: {filepath.name} ({hash_label}: {file_hash})")
            else:
                print(f"    {action}: {filepath.name}")
            
            if not dry_run:
                if dest_path.exists():
                    print(f"      Warning: {dest_path.name} already exists, skipping")
                    continue
                
                if copy_mode:
                    shutil.copy2(filepath, dest_path)
                else:
                    shutil.move(str(filepath), str(dest_path))
    
    # Organize BIOS files
    if results['bios']:
        print(f"\n{action} BIOS files:")
        for platform, files in results['bios'].items():
            platform_dir = target_dir / 'bios' / platform
            
            if not dry_run:
                platform_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"\n  Platform: {platform} ({len(files)} files)")
            for filepath in files:
                dest_path = platform_dir / filepath.name
                
                if calculate_hashes:
                    file_hash = calculate_hash(filepath, hash_algorithm)
                    hash_label = hash_algorithm.upper()
                    print(f"    {action}: {filepath.name} ({hash_label}: {file_hash})")
                else:
                    print(f"    {action}: {filepath.name}")
                
                if not dry_run:
                    if dest_path.exists():
                        print(f"      Warning: {dest_path.name} already exists, skipping")
                        continue
                    
                    if copy_mode:
                        shutil.copy2(filepath, dest_path)
                    else:
                        shutil.move(str(filepath), str(dest_path))
    
    # Report unknown files
    if results['unknown']:
        print(f"\nUnknown platform files ({len(results['unknown'])} files):")
        for filepath in results['unknown']:
            print(f"  {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description='Organize game ROMs and BIOS files into platform-specific directories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would happen
  python rom_organizer.py /path/to/roms /path/to/organized --dry-run
  
  # Copy files instead of moving them
  python rom_organizer.py /path/to/roms /path/to/organized --copy
  
  # Calculate and display MD5 hashes
  python rom_organizer.py /path/to/roms /path/to/organized --hash
  
  # Calculate SHA-1 hashes (for RetroAchievements)
  python rom_organizer.py /path/to/roms /path/to/organized --hash --hash-algorithm sha1
  
  # Organize files with hash calculation
  python rom_organizer.py /path/to/roms /path/to/organized --hash --copy
        """
    )
    
    parser.add_argument('source', type=str, help='Source directory to scan for ROMs')
    parser.add_argument('target', type=str, help='Target directory for organized ROMs')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be done without actually moving files')
    parser.add_argument('--copy', action='store_true',
                       help='Copy files instead of moving them')
    parser.add_argument('--hash', action='store_true',
                       help='Calculate and display hashes for verification')
    parser.add_argument('--hash-algorithm', type=str, default='md5',
                       choices=['md5', 'sha1', 'sha256'],
                       help='Hash algorithm to use (default: md5, use sha1 for RetroAchievements)')
    
    args = parser.parse_args()
    
    source_dir = Path(args.source).resolve()
    target_dir = Path(args.target).resolve()
    
    # Validate source directory
    if not source_dir.exists():
        print(f"Error: Source directory does not exist: {source_dir}", file=sys.stderr)
        sys.exit(1)
    
    if not source_dir.is_dir():
        print(f"Error: Source path is not a directory: {source_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Validate target directory
    if target_dir.exists() and not target_dir.is_dir():
        print(f"Error: Target path exists but is not a directory: {target_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Scan for ROMs
    results = scan_directory(source_dir)
    
    # Summary
    total_roms = sum(len(files) for files in results['roms'].values())
    total_bios = sum(len(files) for files in results['bios'].values())
    
    print(f"\n{'='*60}")
    print(f"Scan Summary:")
    print(f"  Total ROM files found: {total_roms}")
    print(f"  Total BIOS files found: {total_bios}")
    print(f"  Unknown files: {len(results['unknown'])}")
    print(f"  Platforms detected: {len(set(list(results['roms'].keys()) + list(results['bios'].keys())))}")
    print(f"{'='*60}")
    
    if total_roms == 0 and total_bios == 0:
        print("\nNo ROM or BIOS files found to organize.")
        sys.exit(0)
    
    # Organize files
    if args.dry_run:
        print("\n*** DRY RUN MODE - No files will be moved ***")
    
    organize_files(results, target_dir, 
                  dry_run=args.dry_run, 
                  copy_mode=args.copy,
                  calculate_hashes=args.hash,
                  hash_algorithm=args.hash_algorithm)
    
    if args.dry_run:
        print("\n*** DRY RUN COMPLETE - Run without --dry-run to actually organize files ***")
    else:
        print("\n✓ Organization complete!")


if __name__ == '__main__':
    main()
