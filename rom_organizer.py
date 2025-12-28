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
import zipfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed


# Common archive formats accepted at ingestion time
ARCHIVE_EXTENSIONS = ['.zip', '.7z', '.rar']

# Playlist / descriptor formats for disc sets
PLAYLIST_EXTENSIONS = ['.m3u']

# Non-ROM file extensions to filter out (config, metadata, saves, media, documents)
NON_ROM_EXTENSIONS = {
    '.cfg', '.ini', '.dat', '.xml', '.txt', '.nfo', '.diz',  # Config files
    '.json', '.yaml', '.yml',  # Metadata files
    '.sav', '.srm', '.state', '.sta',  # Save files
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tif', '.tiff',  # Images
    '.pdf', '.doc', '.docx', '.rtf'  # Documents
}

# Common ROM file extensions by platform
ROM_EXTENSIONS = {
    # Nintendo
    'nes': ['.nes', '.unf', '.unif'],
    'snes': ['.smc', '.sfc', '.fig', '.swc', '.mgd'],
    'n64': ['.z64', '.n64', '.v64'],
    'gba': ['.gba', '.agb', '.bin'],
    'gb': ['.gb', '.sgb'],  # SGB usually treated as GB-compatible
    'gbc': ['.gbc', '.cgb'],
    'nds': ['.nds', '.ids'],  # .ids is rare but harmless to include

    # Sega
    'genesis': ['.smd', '.gen', '.bin'],  # .md intentionally excluded (Markdown conflict)
    'mastersystem': ['.sms'],
    'gamegear': ['.gg'],
    'segacd': ['.cue', '.bin', '.chd', *PLAYLIST_EXTENSIONS],
    'saturn': ['.cue', '.bin', '.mds', '.mdf', '.chd', *PLAYLIST_EXTENSIONS],
    'dreamcast': ['.cdi', '.gdi', '.chd', *PLAYLIST_EXTENSIONS],

    # Sony
    'psx': ['.cue', '.bin', '.img', '.mdf', '.pbp', '.toc', '.cbn', '.chd', *PLAYLIST_EXTENSIONS],
    'ps2': ['.iso', '.cso', '.chd', '.bin', '.img', '.mdf', '.ima',
            '.gz', '.bz2', '.z', '.z2', '.dump', *PLAYLIST_EXTENSIONS],
    'psp': ['.iso', '.cso', '.pbp', '.elf', '.prx'],

    # Atari
    'atari2600': ['.a26', '.bin'],
    'atari7800': ['.a78'],
    'lynx': ['.lnx', '.o'],
    'jaguar': ['.j64', '.jag'],

    # NEC / TurboGrafx
    'pcengine': ['.pce', '.sgx'],
    'pcenginecd': ['.cue', '.ccd', '.chd', *PLAYLIST_EXTENSIONS],

    # 3DO
    '3do': ['.iso', '.cue', '.chd', *PLAYLIST_EXTENSIONS],

    # Arcade & Neo Geo (add archives + sometimes CHD for CD sets)
    'neogeo': [*ARCHIVE_EXTENSIONS],
    'neogeocd': ['.cue', '.chd', *PLAYLIST_EXTENSIONS],
    'arcade': [*ARCHIVE_EXTENSIONS],
    'mame': [*ARCHIVE_EXTENSIONS],
    'fba': [*ARCHIVE_EXTENSIONS],
}

# System aliases - accept multiple naming conventions
SYSTEM_ALIASES = {
    'tg16': 'pcengine',
    'turbografx16': 'pcengine',
    'pce': 'pcengine',
    'pcecd': 'pcenginecd',
    'megadrive': 'genesis',
    'md': 'genesis',  # key alias only; extension .md still excluded intentionally
    'ps1': 'psx',
    'psone': 'psx',
    'dc': 'dreamcast',
    'sms': 'mastersystem',
    'gg': 'gamegear',
}

# Preferred format order per system (for de-dupe / auto-pick)
# Use when multiple versions exist in the same folder
PREFERRED_EXTENSION_ORDER = {
    # Disc-based: prefer CHD > ISO/CSO > CUE/BIN (typically)
    'psx': ['.chd', '.pbp', '.cue', '.bin', '.img', '.mdf'],
    'ps2': ['.chd', '.cso', '.iso', '.gz', '.bz2', '.z', '.z2', '.bin', '.img', '.mdf', '.ima'],
    'psp': ['.cso', '.iso', '.pbp'],
    'dreamcast': ['.chd', '.gdi', '.cdi'],
    'saturn': ['.chd', '.cue', '.bin', '.mds', '.mdf'],
    'segacd': ['.chd', '.cue', '.bin'],
    'pcenginecd': ['.chd', '.cue', '.ccd'],
    '3do': ['.chd', '.cue', '.iso'],

    # Cartridge-based: prefer native ROM over "weird bin" when both exist
    'nes': ['.nes', '.unif', '.unf'],
    'snes': ['.sfc', '.smc', '.fig', '.swc', '.mgd'],
    'n64': ['.z64', '.n64', '.v64'],
    'gba': ['.gba', '.agb', '.bin'],
    'gb': ['.gb', '.sgb'],
    'gbc': ['.gbc', '.cgb'],
    'nds': ['.nds', '.ids'],

    # Arcade sets: prefer zip/7z equally; can adjust house rules as needed
    'mame': ['.zip', '.7z', '.rar'],
    'fba': ['.zip', '.7z', '.rar'],
    'arcade': ['.zip', '.7z', '.rar'],
    'neogeo': ['.zip', '.7z', '.rar'],
}

# BIOS file keywords (case-insensitive)
BIOS_KEYWORDS = [
    'bios', 'boot', 'firmware', 'syscard', 'system',
    'scph', 'ps-', 'playstation',
]

# Mapping from our platform names to RAHasher system keys
# Based on RAHasher documentation
RAHASHER_SYSTEM_MAP = {
    'gb': 'GB',
    'gba': 'GBA',
    'gbc': 'GBC',
    'nes': 'NES',
    'snes': 'SNES',
    'n64': 'N64',
    'gamecube': 'GC',
    'gc': 'GC',
    'nds': 'DS',
    'ds': 'DS',
    'dsi': 'DSi',
    'pokemonmini': 'MINI',
    'mini': 'MINI',
    'virtualboy': 'VB',
    'vb': 'VB',
    'gameandwatch': 'G&W',
    'fds': 'FDS',
    '3ds': '3DS',
    'wii': 'Wii',
    'wiiu': 'WiiU',
    'genesis': 'MD',
    'megadrive': 'MD',
    'md': 'MD',
    'mastersystem': 'SMS',
    'sms': 'SMS',
    'gamegear': 'GG',
    'gg': 'GG',
    'sega32x': '32X',
    '32x': '32X',
    'segacd': 'SegaCD',
    'saturn': 'Saturn',
    'dreamcast': 'DC',
    'dc': 'DC',
    'sg1000': 'SG1000',
    'psx': 'PS',
    'ps': 'PS',
    'ps1': 'PS',
    'playstation': 'PS',
    'ps2': 'PS2',
    'psp': 'PSP',
    'atari2600': '2600',
    '2600': '2600',
    'atari5200': '5200',
    '5200': '5200',
    'atari7800': '7800',
    '7800': '7800',
    'lynx': 'Lynx',
    'jaguar': 'Jaguar',
    'jaguarcd': 'JaguarCD',
    'pcengine': 'PCE',
    'pce': 'PCE',
    'tg16': 'PCE',
    'turbografx16': 'PCE',
    'pcenginecd': 'PCECD',
    'pcecd': 'PCECD',
    'supergrafx': 'SGX',
    'sgx': 'SGX',
    'pcfx': 'PCFX',
    'neogeopocket': 'NGP',
    'ngp': 'NGP',
    'neogeopocketcolor': 'NGPC',
    'ngpc': 'NGPC',
    'wonderswan': 'WS',
    'ws': 'WS',
    'wonderswancolor': 'WSC',
    'wsc': 'WSC',
    'colecovision': 'Coleco',
    'coleco': 'Coleco',
    'intellivision': 'Intv',
    'intv': 'Intv',
    'vectrex': 'Vectrex',
    'odyssey2': 'Odyssey2',
    'channelf': 'ChannelF',
    'cpc': 'CPC',
    'apple2': 'AppleII',
    'msx': 'MSX',
    'pc8800': 'PC8800',
    'pc9800': 'PC9800',
    'zxspectrum': 'ZXSpectrum',
    'amstradcpc': 'CPC',
    'supervision': 'Supervision',
    'megaduck': 'MegaDuck',
    'arduboy': 'Arduboy',
    'wasm4': 'WASM4',
    '3do': '3DO',
    # Note: Arcade platforms removed - they use special filename-based hashing
    'neogeocd': 'NGCD',
}


def canonical_system(system_key: str) -> str:
    """Map aliases to a canonical system key."""
    k = system_key.lower().strip()
    return SYSTEM_ALIASES.get(k, k)


def allowed_extensions(system_key: str) -> List[str]:
    """Return allowed extensions for a (possibly-aliased) system key."""
    k = canonical_system(system_key)
    return ROM_EXTENSIONS.get(k, [])


def preferred_order(system_key: str) -> List[str]:
    """Return preferred extension order for choosing among duplicates."""
    k = canonical_system(system_key)
    return PREFERRED_EXTENSION_ORDER.get(k, [])

# Pre-computed set of all ROM extensions for efficient lookup
ALL_ROM_EXTENSIONS = set(ext for exts in ROM_EXTENSIONS.values() for ext in exts)

# Directories to exclude from scanning (pre-converted to lowercase for efficient lookup)
EXCLUDED_DIRS_SET = {
    'imgs', 'images', 'img', 'artwork', 'art', 'covers', 'cover',
    'screenshots', 'screenshot', 'snaps', 'snap', 'preview', 'previews',
    'videos', 'video', 'manuals', 'manual', 'docs', 'documentation'
}

# ROM header signatures for platform detection
# Format: platform -> list of (offset, signature_bytes)
ROM_HEADERS = {
    'nes': [(0, b'NES\x1a')],
    'n64': [
        (0, b'\x80\x37\x12\x40'),  # Big-endian (z64)
        (0, b'\x37\x80\x40\x12'),  # Byte-swapped (v64)
        (0, b'\x40\x12\x37\x80'),  # Little-endian (n64)
    ],
    'gba': [(0xA0, b'\x96')],  # Nintendo logo check
    'gb': [(0x104, b'\xCE\xED\x66\x66\xCC\x0D')],  # Nintendo logo start
    'gbc': [(0x104, b'\xCE\xED\x66\x66\xCC\x0D')],  # Same as GB
    'genesis': [
        (0x100, b'SEGADISCSYSTEM'),  # Sega CD (check longer signature first)
        (0x100, b'SEGA MEGA DRIVE'),  # Genesis with full header
        (0x100, b'SEGA GENESIS'),  # Genesis US name
        (0x100, b'SEGA'),  # Generic Sega (check last)
    ],
    'mastersystem': [(0x7FF0, b'TMR SEGA')],
    'psx': [
        # PSX discs use .cue + .bin, check for specific patterns in bin files
        (0x9320, b'PLAYSTATION'),  # Common location in system area
        (0x9340, b'LICENSED BY SONY'),  # Alternative location
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
            # Seek to the platform-specific offset, then read a reasonable amount of data
            # Read at least 512 bytes (or the full signature length if larger) from that offset
            read_length = max(len(signature), 512) if signature else 512
            header_data = read_file_header(filepath, offset, read_length)
            
            if not header_data:
                continue
            
            # Check for exact match at offset
            if signature and header_data[:len(signature)] == signature:
                return platform
            
            # For some platforms, signature might be slightly offset within the region
            if platform in ['genesis', 'mastersystem'] and signature:
                if signature in header_data:
                    return platform
    
    return None


def is_zip_archive(filepath: Path) -> bool:
    """Check if a file is a valid ZIP archive."""
    try:
        return zipfile.is_zipfile(filepath)
    except Exception:
        return False


def inspect_zip_contents(filepath: Path, verbose: bool = False) -> Optional[str]:
    """
    Inspect ZIP file contents to detect platform.
    Returns the first ROM file extension found inside the ZIP.
    """
    try:
        with zipfile.ZipFile(filepath, 'r') as zf:
            for name in zf.namelist():
                # Skip directories
                if name.endswith('/'):
                    continue
                
                ext = Path(name).suffix.lower()
                if ext in ALL_ROM_EXTENSIONS:
                    if verbose:
                        print(f"      Found ROM in ZIP: {name} ({ext})")
                    return ext
    except Exception as e:
        if verbose:
            print(f"      Error reading ZIP: {e}")
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


def calculate_hash_worker(filepath: Path, algorithm: str) -> Tuple[Path, str, Optional[str]]:
    """
    Worker function for multithreaded hash calculation.
    Returns tuple of (filepath, hash_value, error_message).
    """
    try:
        hash_value = calculate_hash(filepath, algorithm)
        return (filepath, hash_value, None)
    except Exception as e:
        return (filepath, "", str(e))


def calculate_hashes_multithreaded(files: List[Path], algorithm: str = 'md5', 
                                   max_workers: int = 4, verbose: bool = False) -> Dict[Path, str]:
    """
    Calculate hashes for multiple files using thread pool.
    
    Args:
        files: List of file paths to hash
        algorithm: Hash algorithm to use
        max_workers: Number of concurrent threads
        verbose: Show progress
    
    Returns:
        Dictionary mapping file paths to their hashes
    """
    results = {}
    total = len(files)
    
    if verbose:
        print(f"\n  Calculating {algorithm.upper()} hashes using {max_workers} threads...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all hash calculation jobs
        future_to_file = {
            executor.submit(calculate_hash_worker, filepath, algorithm): filepath 
            for filepath in files
        }
        
        # Process completed hashes
        completed = 0
        for future in as_completed(future_to_file):
            filepath, hash_value, error = future.result()
            completed += 1
            
            if error:
                if verbose:
                    print(f"    Error hashing {filepath.name}: {error}")
            else:
                results[filepath] = hash_value
                if verbose and completed % 10 == 0:
                    print(f"    Progress: {completed}/{total} files hashed")
    
    if verbose:
        print(f"    Completed: {len(results)}/{total} files hashed successfully")
    
    return results


def calculate_ra_hash(filepath: Path, platform: str, verbose: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """
    Calculate RetroAchievements-compatible hash using external RAHasher tool.
    
    Args:
        filepath: Path to the ROM file
        platform: Detected platform name
        verbose: Enable verbose output
    
    Returns:
        Tuple of (hash_string, error_type) where:
        - hash_string is the RA hash or None if failed
        - error_type is one of: None, 'arcade', 'no_mapping', 'wrong_platform', 'not_found', 'timeout', 'other'
    """
    try:
        # Check if platform is arcade - these use special filename-based hashing
        if platform.lower() in ['arcade', 'mame', 'fba', 'neogeo']:
            if verbose:
                print(f"      Note: Arcade ROMs use special filename-based hashing in RetroAchievements")
            return (None, 'arcade')
        
        # Get RAHasher system key for this platform
        canonical_platform = canonical_system(platform.lower())
        rahasher_system = RAHASHER_SYSTEM_MAP.get(canonical_platform)
        
        if not rahasher_system:
            if verbose:
                print(f"      No RAHasher system mapping for platform: {platform}")
            return (None, 'no_mapping')
        
        # Build RAHasher command with system key
        cmd = ['RAHasher', rahasher_system, str(filepath)]
        if verbose:
            print(f"      Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, 
                              capture_output=True, 
                              text=True, 
                              timeout=30)
        
        # Parse RAHasher output to extract hash (try regardless of return code)
        # First, prefer the explicit "Supported Game Files" line
        lines = result.stdout.splitlines()
        for line in lines:
            if 'Supported Game Files' in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    hash_value = parts[-1].strip()
                    if (hash_value and len(hash_value) == 32 and 
                        all(c in '0123456789abcdefABCDEF' for c in hash_value)):
                        return (hash_value, None)
        
        # Fallback: consider other colon-containing lines with hex validation
        for line in lines:
            if ':' not in line:
                continue
            parts = line.split(':')
            if len(parts) >= 2:
                hash_value = parts[-1].strip()
                if (hash_value and len(hash_value) == 32 and
                    all(c in '0123456789abcdefABCDEF' for c in hash_value)):
                    return (hash_value, None)
        
        # Check if stdout itself is a valid hash (RAHasher sometimes outputs just the hash)
        stdout_clean = result.stdout.strip()
        if (stdout_clean and len(stdout_clean) == 32 and
            all(c in '0123456789abcdefABCDEF' for c in stdout_clean)):
            return (stdout_clean, None)
        
        # If we reach here and return code is 0, return stdout for debugging
        if result.returncode == 0:
            if verbose:
                print(f"      RAHasher output: {stdout_clean}")
            return (stdout_clean, None)
        
        # RAHasher failed - check if it's a platform mismatch error
        error_msg = result.stderr.strip() if result.stderr.strip() else ""
        
        # Detect platform mismatch errors (e.g., "Not a PSP game disc")
        error_type = 'other'
        combined_output = (error_msg + " " + stdout_clean).lower()
        if 'not a' in combined_output and 'game' in combined_output:
            error_type = 'wrong_platform'
        
        if verbose:
            print(f"      RAHasher failed (exit code {result.returncode})")
            if error_msg:
                print(f"      Error: {error_msg}")
            if stdout_clean:
                print(f"      Output: {stdout_clean}")
        return (None, error_type)
    except FileNotFoundError:
        if verbose:
            print(f"      RAHasher not found in PATH. Please install RAHasher from RetroAchievements.")
        return (None, 'not_found')
    except subprocess.TimeoutExpired:
        if verbose:
            print(f"      RAHasher timed out (30s) for {filepath.name}")
        return (None, 'timeout')
    except Exception as e:
        if verbose:
            print(f"      RAHasher exception: {type(e).__name__}: {str(e)}")
        return (None, 'other')


def calculate_ra_hashes_multithreaded(files: List[Tuple[Path, str]], 
                                      max_workers: int = 4, 
                                      verbose: bool = False) -> Dict[Path, str]:
    """
    Calculate RA hashes for multiple files using thread pool.
    
    Args:
        files: List of (filepath, platform) tuples
        max_workers: Number of concurrent threads
        verbose: Show progress
    
    Returns:
        Dictionary mapping file paths to their RA hashes
    """
    results = {}
    total = len(files)
    
    if verbose:
        print(f"\n  Calculating RetroAchievements hashes using {max_workers} threads...")
        print(f"    Note: This requires RAHasher to be installed and in PATH")
    
    def ra_hash_worker(filepath: Path, platform: str) -> Tuple[Path, Optional[str], Optional[str]]:
        """Worker function for RA hash calculation."""
        hash_value, error_type = calculate_ra_hash(filepath, platform, verbose=False)
        return (filepath, hash_value, error_type)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all RA hash calculation jobs
        future_to_file = {
            executor.submit(ra_hash_worker, filepath, platform): filepath 
            for filepath, platform in files
        }
        
        # Process completed hashes
        completed = 0
        for future in as_completed(future_to_file):
            filepath, hash_value, error_type = future.result()
            completed += 1
            
            if hash_value:
                results[filepath] = hash_value
                if verbose and completed % 10 == 0:
                    print(f"    Progress: {completed}/{total} files hashed")
            elif verbose:
                print(f"    Failed to hash: {filepath.name}")
    
    if verbose:
        print(f"    Completed: {len(results)}/{total} files hashed successfully")
    
    return results


def is_bios_file(filename: str) -> bool:
    """Check if a file is likely a BIOS file based on its name."""
    filename_lower = filename.lower()
    return any(keyword in filename_lower for keyword in BIOS_KEYWORDS)


def get_platforms_by_extension(extension: str) -> List[str]:
    """
    Get all platforms that support a given file extension.
    Returns list of platform names, ordered by specificity (more specific first).
    """
    ext_lower = extension.lower()
    platforms = []
    
    # Find all platforms that support this extension
    for platform, extensions in ROM_EXTENSIONS.items():
        if ext_lower in extensions:
            platforms.append(platform)
    
    # Order by specificity - platforms with fewer extensions are more specific
    # For example, .a26 is specific to atari2600, while .bin is shared by many
    platforms.sort(key=lambda p: len(ROM_EXTENSIONS[p]))
    
    return platforms


def detect_platform(filepath: Path, extension: str, verbose: bool = False) -> Optional[str]:
    """
    Detect the platform for a ROM file based on header signature, extension, and path.
    Supports ZIP/7z/RAR files by inspecting their contents.
    Supports system aliases (e.g., 'ps1' -> 'psx', 'tg16' -> 'pcengine').
    Returns the platform name or None if unknown.
    """
    ext_lower = extension.lower()
    
    # Check for highly specific extensions FIRST (before directory detection)
    # These extensions are unambiguous and should override directory names
    specific_extensions = {
        '.a26': 'atari2600',  # Only used by Atari 2600
        '.a78': 'atari7800',  # Only used by Atari 7800
        '.nes': 'nes',        # NES (will be verified by header if needed)
        '.smc': 'snes',       # SNES
        '.sfc': 'snes',       # SNES
        '.z64': 'n64',        # N64 big-endian
        '.n64': 'n64',        # N64 little-endian
        '.v64': 'n64',        # N64 byte-swapped
        '.gba': 'gba',        # Game Boy Advance
        '.agb': 'gba',        # Game Boy Advance alternate
        '.gb': 'gb',          # Game Boy
        '.sgb': 'gb',          # Super Game Boy (GB compatible)
        '.gbc': 'gbc',        # Game Boy Color
        '.cgb': 'gbc',        # Game Boy Color alternate
        '.nds': 'nds',        # Nintendo DS
        '.smd': 'genesis',    # Genesis
        '.gen': 'genesis',    # Genesis alternate
        '.sms': 'mastersystem', # Master System
        '.gg': 'gamegear',    # Game Gear
        '.pce': 'pcengine',   # PC Engine
        '.sgx': 'pcengine',   # SuperGrafx
        '.lnx': 'lynx',       # Atari Lynx
        '.j64': 'jaguar',     # Atari Jaguar
        '.jag': 'jaguar',     # Atari Jaguar alternate
    }
    
    if ext_lower in specific_extensions:
        detected_platform = specific_extensions[ext_lower]
        if verbose:
            print(f"    Detected as {detected_platform} based on specific extension {ext_lower}")
        return detected_platform
    
    # Check parent directory names for platform hints (for ambiguous extensions)
    parent_parts = [p.lower() for p in filepath.parts]
    
    # Try to match platform from directory structure (with alias support)
    for platform in ROM_EXTENSIONS.keys():
        if platform in parent_parts:
            return platform
    
    # Check for aliased system names in path
    for part in parent_parts:
        canonical = canonical_system(part)
        if canonical in ROM_EXTENSIONS:
            return canonical
    
    # Handle archive files - inspect contents to detect platform
    if ext_lower in ['.zip', '.7z', '.rar']:
        if is_zip_archive(filepath):  # This also works for most archives
            inner_ext = inspect_zip_contents(filepath, verbose)
            if inner_ext:
                # Try to detect platform from the ROM file inside the archive
                for platform, extensions in ROM_EXTENSIONS.items():
                    if inner_ext in extensions:
                        return platform
                # If inner file has a non-ROM extension (like .png), don't treat as ROM
                if inner_ext.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.txt', '.pdf', '.doc']:
                    if verbose:
                        print(f"    Archive contains non-ROM file ({inner_ext}), skipping")
                    return None
        # If we can't determine from contents, treat as arcade/MAME ROM
        return 'arcade'
    
    # Try header-based detection for files with ambiguous extensions
    if ext_lower in ['.bin', '.iso', '.img']:
        # These extensions are shared across platforms, try header detection
        header_platform = detect_platform_from_header(filepath)
        if header_platform:
            return header_platform
    
    # For cartridge-based systems with specific extensions, always try header detection
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
                # Also check aliases in path
                for part in parent_parts:
                    canonical = canonical_system(part)
                    if canonical in ROM_EXTENSIONS:
                        return canonical
            return platform
    
    return None


def scan_directory(source_dir: Path, max_files: Optional[int] = None, verbose: bool = False,
                   include_images: bool = False) -> Dict[str, List[Path]]:
    """
    Recursively scan a directory for ROM and BIOS files.
    Returns a dictionary mapping platforms to lists of files.
    
    Args:
        source_dir: Source directory to scan
        max_files: Maximum number of files to process (None for unlimited)
        verbose: Enable verbose output
        include_images: If True, include image/media directories instead of excluding them
    """
    results = {
        'roms': {},
        'bios': {},
        'unknown': [],
        'skipped_dirs': []
    }
    
    print(f"Scanning directory: {source_dir}")
    
    files_processed = 0
    
    for root, dirs, files in os.walk(source_dir):
        root_path = Path(root)
        
        # Filter out excluded directories (unless include_images is True)
        if not include_images:
            original_dirs = dirs.copy()
            dirs[:] = [d for d in dirs if d.lower() not in EXCLUDED_DIRS_SET]
            
            # Track skipped directories
            skipped = [d for d in original_dirs if d.lower() in EXCLUDED_DIRS_SET]
            if skipped and verbose:
                for skipped_dir in skipped:
                    results['skipped_dirs'].append(root_path / skipped_dir)
                    print(f"  Skipping directory: {root_path / skipped_dir}")
        
        for filename in files:
            # Check file limit
            if max_files is not None and files_processed >= max_files:
                if verbose:
                    print(f"\nReached file limit of {max_files} files")
                return results
            
            filepath = root_path / filename
            extension = filepath.suffix.lower()
            
            # Skip non-ROM files (no extension)
            if not extension:
                if verbose:
                    print(f"  Skipping (no extension): {filename}")
                continue
            
            # Skip non-ROM file extensions (config, metadata, saves, etc.)
            if extension in NON_ROM_EXTENSIONS:
                if verbose:
                    print(f"  Skipping non-ROM file: {filename} ({extension} extension)")
                continue
            
            if verbose:
                print(f"  Scanning: {filepath}")
            
            # Detect platform
            platform = detect_platform(filepath, extension, verbose)
            
            if platform:
                if verbose:
                    print(f"    Detected platform: {platform}")
                
                # Determine if it's a BIOS file
                if is_bios_file(filename):
                    if platform not in results['bios']:
                        results['bios'][platform] = []
                    results['bios'][platform].append(filepath)
                else:
                    if platform not in results['roms']:
                        results['roms'][platform] = []
                    results['roms'][platform].append(filepath)
                
                files_processed += 1
            else:
                # Unknown platform
                if extension.lower() in ALL_ROM_EXTENSIONS:
                    if verbose:
                        print(f"    Unknown platform for: {filename}")
                    results['unknown'].append(filepath)
                    files_processed += 1
    
    return results


def organize_files(results: Dict, target_dir: Path, dry_run: bool = False, 
                   copy_mode: bool = False, calculate_hashes: bool = False,
                   hash_algorithm: str = 'md5', use_multithreading: bool = False,
                   max_workers: int = 4, verbose: bool = False, delete_duplicates: bool = False,
                   use_ra_hash: bool = False):
    """
    Organize the scanned files into the target directory structure.
    
    Args:
        results: Dictionary from scan_directory
        target_dir: Root directory for organized files
        dry_run: If True, only show what would be done without moving files
        copy_mode: If True, copy files instead of moving them
        calculate_hashes: If True, calculate and display file hashes
        hash_algorithm: Hash algorithm to use ('md5', 'sha1', 'sha256')
        use_multithreading: If True, calculate hashes in parallel after moving
        max_workers: Number of threads for parallel hashing
        verbose: Enable verbose output
        delete_duplicates: If True, delete duplicate files instead of skipping them
        use_ra_hash: If True, use RAHasher for RetroAchievements-compatible hashing
    """
    action = "Would copy" if dry_run and copy_mode else "Would move" if dry_run else "Copying" if copy_mode else "Moving"
    
    # Collect files to hash later (for multithreaded mode)
    files_to_hash = []
    
    # Track seen hashes for duplicate detection
    seen_hashes = {}  # hash -> (platform, filename, filepath)
    
    # Organize ROMs
    print(f"\n{action} ROMs:")
    for platform, files in results['roms'].items():
        platform_dir = target_dir / 'roms' / platform
        
        if not dry_run:
            platform_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n  Platform: {platform} ({len(files)} files)")
        for filepath in files:
            dest_path = platform_dir / filepath.name
            
            # Check if destination already exists (duplicate filename)
            is_duplicate_name = dest_path.exists() if not dry_run else False
            
            if not dry_run:
                if is_duplicate_name:
                    print(f"    ⚠️  Duplicate: {filepath.name} [Platform: {platform.upper()}] - file already exists")
                    continue
                
                # Pre-check with RAHasher if needed (before moving)
                if calculate_hashes and use_ra_hash and not use_multithreading:
                    file_hash, error_type = calculate_ra_hash(filepath, platform, verbose)
                    if not file_hash:
                        # Skip this file - RAHasher can't process it
                        print(f"    Skipping: {filepath.name} [Platform: {platform.upper()}] - RAHasher cannot process this file")
                        continue
                
                if copy_mode:
                    shutil.copy2(filepath, dest_path)
                else:
                    shutil.move(str(filepath), str(dest_path))
                
                # Track for hashing after move if multithreading enabled
                if calculate_hashes and use_multithreading:
                    files_to_hash.append((dest_path, platform))
                elif calculate_hashes:
                    # Calculate hash immediately if not multithreading
                    if use_ra_hash:
                        # We already calculated it above before move
                        hash_label = "RA-Hash"
                    else:
                        file_hash = calculate_hash(dest_path, hash_algorithm)
                        hash_label = hash_algorithm.upper()
                    
                    if file_hash:
                        # Check for duplicate hash
                        if file_hash in seen_hashes:
                            dup_platform, dup_file, dup_path = seen_hashes[file_hash]
                            if delete_duplicates:
                                print(f"    🗑️  Deleting duplicate: {filepath.name} [Platform: {platform.upper()}] ({hash_label}: {file_hash[:16]}...) - same as {dup_file} [{dup_platform.upper()}]")
                                if not dry_run:
                                    dest_path.unlink()  # Delete the file we just moved
                            else:
                                print(f"    ⚠️  Duplicate: {filepath.name} [Platform: {platform.upper()}] ({hash_label}: {file_hash[:16]}...) - same as {dup_file} [{dup_platform.upper()}]")
                        else:
                            print(f"    Moved: {filepath.name} [Platform: {platform.upper()}] ({hash_label}: {file_hash})")
                            seen_hashes[file_hash] = (platform, filepath.name, dest_path)
                    else:
                        print(f"    Moved: {filepath.name} [Platform: {platform.upper()}] (hash calculation failed)")
                else:
                    print(f"    Moved: {filepath.name} [Platform: {platform.upper()}]")
            else:
                # Dry run mode
                if calculate_hashes and not use_multithreading:
                    if use_ra_hash:
                        file_hash, error_type = calculate_ra_hash(filepath, platform, verbose)
                        hash_label = "RA-Hash"
                        if not file_hash:
                            # Skip this file in dry-run too
                            print(f"    Skipping: {filepath.name} [Platform: {platform.upper()}] - RAHasher cannot process this file")
                            continue
                    else:
                        file_hash = calculate_hash(filepath, hash_algorithm)
                        hash_label = hash_algorithm.upper()
                    
                    if file_hash:
                        # Check for duplicate hash
                        if file_hash in seen_hashes:
                            dup_platform, dup_file, dup_path = seen_hashes[file_hash]
                            if delete_duplicates:
                                print(f"    Would delete duplicate: {filepath.name} [Platform: {platform.upper()}] ({hash_label}: {file_hash[:16]}...) - same as {dup_file} [{dup_platform.upper()}]")
                            else:
                                print(f"    ⚠️  Duplicate: {filepath.name} [Platform: {platform.upper()}] ({hash_label}: {file_hash[:16]}...) - same as {dup_file} [{dup_platform.upper()}]")
                        else:
                            print(f"    {action}: {filepath.name} [Platform: {platform.upper()}] ({hash_label}: {file_hash})")
                            seen_hashes[file_hash] = (platform, filepath.name, None)
                    else:
                        print(f"    {action}: {filepath.name} [Platform: {platform.upper()}] (hash calculation failed)")
                else:
                    print(f"    {action}: {filepath.name} [Platform: {platform.upper()}]")
    
    # Organize BIOS files
    if results['bios']:
        print(f"\n{action} BIOS files:")
        if use_ra_hash:
            print("  ⚠️  Note: BIOS files are not games and may not be supported by RAHasher")
        
        for platform, files in results['bios'].items():
            platform_dir = target_dir / 'bios' / platform
            
            if not dry_run:
                platform_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"\n  Platform: {platform} ({len(files)} files)")
            for filepath in files:
                dest_path = platform_dir / filepath.name
                
                is_duplicate_name = dest_path.exists() if not dry_run else False
                
                if not dry_run:
                    if is_duplicate_name:
                        print(f"    ⚠️  Duplicate: {filepath.name} [Platform: {platform.upper()}] - file already exists")
                        continue
                    
                    # Pre-check with RAHasher if needed (before moving)
                    if calculate_hashes and use_ra_hash and not use_multithreading:
                        file_hash, error_type = calculate_ra_hash(filepath, platform, verbose)
                        if not file_hash:
                            # Skip this file - RAHasher can't process it
                            print(f"    Skipping: {filepath.name} [Platform: {platform.upper()}] - RAHasher cannot process this file")
                            continue
                    
                    if copy_mode:
                        shutil.copy2(filepath, dest_path)
                    else:
                        shutil.move(str(filepath), str(dest_path))
                    
                    # Track for hashing
                    if calculate_hashes and use_multithreading:
                        files_to_hash.append((dest_path, platform))
                    elif calculate_hashes:
                        if use_ra_hash:
                            # We already calculated it above before move
                            hash_label = "RA-Hash"
                        else:
                            file_hash = calculate_hash(dest_path, hash_algorithm)
                            hash_label = hash_algorithm.upper()
                        
                        if file_hash:
                            # Check for duplicate hash
                            if file_hash in seen_hashes:
                                dup_platform, dup_file, dup_path = seen_hashes[file_hash]
                                if delete_duplicates:
                                    print(f"    🗑️  Deleting duplicate: {filepath.name} [Platform: {platform.upper()}] ({hash_label}: {file_hash[:16]}...) - same as {dup_file} [{dup_platform.upper()}]")
                                    if not dry_run:
                                        dest_path.unlink()
                                else:
                                    print(f"    ⚠️  Duplicate: {filepath.name} [Platform: {platform.upper()}] ({hash_label}: {file_hash[:16]}...) - same as {dup_file} [{dup_platform.upper()}]")
                            else:
                                print(f"    Moved: {filepath.name} [Platform: {platform.upper()}] ({hash_label}: {file_hash})")
                                seen_hashes[file_hash] = (platform, filepath.name, dest_path)
                        else:
                            print(f"    Moved: {filepath.name} [Platform: {platform.upper()}] (hash calculation failed)")
                    else:
                        print(f"    Moved: {filepath.name} [Platform: {platform.upper()}]")
                else:
                    # Dry run mode
                    if calculate_hashes and not use_multithreading:
                        if use_ra_hash:
                            file_hash, error_type = calculate_ra_hash(filepath, platform, verbose)
                            hash_label = "RA-Hash"
                            if not file_hash:
                                # Skip this file in dry-run too
                                print(f"    Skipping: {filepath.name} [Platform: {platform.upper()}] - RAHasher cannot process this file")
                                continue
                        else:
                            file_hash = calculate_hash(filepath, hash_algorithm)
                            hash_label = hash_algorithm.upper()
                        
                        if file_hash:
                            # Check for duplicate hash
                            if file_hash in seen_hashes:
                                dup_platform, dup_file, dup_path = seen_hashes[file_hash]
                                if delete_duplicates:
                                    print(f"    Would delete duplicate: {filepath.name} [Platform: {platform.upper()}] ({hash_label}: {file_hash[:16]}...) - same as {dup_file} [{dup_platform.upper()}]")
                                else:
                                    print(f"    ⚠️  Duplicate: {filepath.name} [Platform: {platform.upper()}] ({hash_label}: {file_hash[:16]}...) - same as {dup_file} [{dup_platform.upper()}]")
                            else:
                                print(f"    {action}: {filepath.name} [Platform: {platform.upper()}] ({hash_label}: {file_hash})")
                                seen_hashes[file_hash] = (platform, filepath.name, None)
                        else:
                            print(f"    {action}: {filepath.name} [Platform: {platform.upper()}] (hash calculation failed)")
                    else:
                        print(f"    {action}: {filepath.name} [Platform: {platform.upper()}]")
    
    # Calculate hashes in parallel if multithreading enabled
    if files_to_hash and use_multithreading and not dry_run:
        print(f"\nCalculating hashes for {len(files_to_hash)} files using {max_workers} threads...")
        
        if use_ra_hash:
            # Use RA hashing
            hash_results = calculate_ra_hashes_multithreaded(files_to_hash, max_workers, verbose)
            hash_label = "RA-Hash"
        else:
            # Use standard hashing
            paths_only = [path for path, _ in files_to_hash]
            hash_results = calculate_hashes_multithreaded(paths_only, hash_algorithm, max_workers, verbose)
            hash_label = hash_algorithm.upper()
        
        # Display results with platform info and duplicate detection
        print(f"\n{hash_label} Results:")
        files_deleted = 0
        for dest_path, platform in files_to_hash:
            if dest_path in hash_results:
                file_hash = hash_results[dest_path]
                
                # Check for duplicates
                if file_hash in seen_hashes:
                    dup_platform, dup_file, dup_path = seen_hashes[file_hash]
                    if delete_duplicates:
                        print(f"  🗑️  Deleting duplicate: {dest_path.name} [Platform: {platform.upper()}] ({hash_label}: {file_hash[:16]}...) - same as {dup_file} [{dup_platform.upper()}]")
                        if dest_path.exists():
                            dest_path.unlink()
                            files_deleted += 1
                    else:
                        print(f"  ⚠️  Duplicate: {dest_path.name} [Platform: {platform.upper()}] ({hash_label}: {file_hash[:16]}...) - same as {dup_file} [{dup_platform.upper()}]")
                else:
                    print(f"  {dest_path.name} [Platform: {platform.upper()}]: {file_hash}")
                    seen_hashes[file_hash] = (platform, dest_path.name, dest_path)
        
        if delete_duplicates and files_deleted > 0:
            print(f"\n🗑️  Deleted {files_deleted} duplicate file(s)")
    
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
  
  # Verbose mode to see detailed scanning progress
  python rom_organizer.py /path/to/roms /path/to/organized --verbose --dry-run
  
  # Process only first 100 files (useful for testing)
  python rom_organizer.py /path/to/roms /path/to/organized --limit 100 --dry-run
  
  # Use multithreaded hashing after moving files (faster for large collections)
  python rom_organizer.py /path/to/roms /path/to/organized --hash --multithreaded --threads 8
  
  # Include image directories (move imgs, artwork, etc.)
  python rom_organizer.py /path/to/roms /path/to/organized --include-images
  
  # Delete duplicate files instead of skipping them
  python rom_organizer.py /path/to/roms /path/to/organized --hash --delete-duplicates
  
  # Use RetroAchievements-compatible hashing (requires RAHasher to be installed)
  python rom_organizer.py /path/to/roms /path/to/organized --ra-hash --copy
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
    parser.add_argument('--ra-hash', action='store_true',
                       help='Use RetroAchievements-compatible hashing via RAHasher (requires RAHasher installed)')
    parser.add_argument('--hash-algorithm', type=str, default='md5',
                       choices=['md5', 'sha1', 'sha256'],
                       help='Hash algorithm to use with --hash (default: md5)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output showing detailed scanning progress')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit the number of files to process (useful for testing)')
    parser.add_argument('--multithreaded', action='store_true',
                       help='Use multithreaded hashing after moving files (faster for large collections)')
    parser.add_argument('--threads', type=int, default=4,
                       help='Number of threads for multithreaded hashing (default: 4)')
    parser.add_argument('--include-images', action='store_true',
                       help='Include image/media directories (imgs, artwork, screenshots, etc.) instead of excluding them')
    parser.add_argument('--delete-duplicates', action='store_true',
                       help='Delete duplicate files instead of skipping them (requires --hash or --ra-hash)')
    
    args = parser.parse_args()
    
    verbose = args.verbose
    
    # Validate delete-duplicates requires hash or ra-hash
    if args.delete_duplicates and not args.hash and not args.ra_hash:
        print("Error: --delete-duplicates requires --hash or --ra-hash to be enabled", file=sys.stderr)
        sys.exit(1)
    
    # Validate that --hash and --ra-hash are not used together
    if args.hash and args.ra_hash:
        print("Error: --hash and --ra-hash cannot be used together", file=sys.stderr)
        sys.exit(1)
    
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
    if verbose:
        print(f"Verbose mode enabled")
        if args.limit:
            print(f"Processing limit: {args.limit} files")
        if args.multithreaded and (args.hash or args.ra_hash):
            print(f"Multithreaded hashing enabled ({args.threads} threads)")
        if args.ra_hash:
            print(f"RetroAchievements hashing enabled (requires RAHasher)")
        if args.include_images:
            print(f"Including image/media directories")
        if args.delete_duplicates:
            print(f"Delete duplicates mode enabled")
    
    results = scan_directory(source_dir, max_files=args.limit, verbose=verbose,
                            include_images=args.include_images)
    
    # Summary
    total_roms = sum(len(files) for files in results['roms'].values())
    total_bios = sum(len(files) for files in results['bios'].values())
    
    print(f"\n{'='*60}")
    print(f"Scan Summary:")
    print(f"  Total ROM files found: {total_roms}")
    print(f"  Total BIOS files found: {total_bios}")
    print(f"  Unknown files: {len(results['unknown'])}")
    print(f"  Platforms detected: {len(set(list(results['roms'].keys()) + list(results['bios'].keys())))}")
    if verbose and results.get('skipped_dirs'):
        print(f"  Directories skipped: {len(results['skipped_dirs'])}")
    if args.limit:
        print(f"  File limit applied: {args.limit}")
    print(f"{'='*60}")
    
    if total_roms == 0 and total_bios == 0:
        print("\nNo ROM or BIOS files found to organize.")
        sys.exit(0)
    
    # Organize files
    if args.dry_run:
        print("\n*** DRY RUN MODE - No files will be moved ***")
    
    # Determine hash mode
    calculate_hashes = args.hash or args.ra_hash
    
    organize_files(results, target_dir, 
                  dry_run=args.dry_run, 
                  copy_mode=args.copy,
                  calculate_hashes=calculate_hashes,
                  hash_algorithm=args.hash_algorithm,
                  use_multithreading=args.multithreaded,
                  max_workers=args.threads,
                  verbose=verbose,
                  delete_duplicates=args.delete_duplicates,
                  use_ra_hash=args.ra_hash)
    
    if args.dry_run:
        print("\n*** DRY RUN COMPLETE - Run without --dry-run to actually organize files ***")
    else:
        print("\n✓ Organization complete!")


if __name__ == '__main__':
    main()
