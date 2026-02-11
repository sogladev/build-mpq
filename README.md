# build-mpq

A lightweight wrapper around `mpqcli` for building and validating World of Warcraft 3.3.5a client patch MPQ files. This tool's main goal is to create canonical staging areas and package them with `mpqcli` while resolving symbolic links so the resulting MPQ contains the real file data and valid WoW directory paths. Tested on Linux-first — other platforms may work but are less tested.

> ⚠️🤖 **Warning:** This project and parts of this README were created with AI assistance.

Main features:

1. Create a skeleton structure to allow easily setting up a valid MPQ directory for development.
2. Wrap `mpqcli` packaging to allow symbolic links in the staging tree: symlinks are resolved during packaging so `mpqcli` creates a valid MPQ containing the real file data.

## Features

- ✅ **Create staging areas** with the canonical WoW 3.3.5a directory structure
- ✅ **Package MPQ files** from staging areas using mpqcli
- ✅ **Validate MPQ structure** to ensure client compatibility
- ✅ **Type-safe** with full type hints
- ✅ **Well-tested** with comprehensive test coverage
- ✅ **Cross-platform** using pathlib

## Requirements

- Python 3.11+
- [mpqcli](https://github.com/Kanma/mpqcli) - Must be available in PATH

## Installation

```bash
# Clone or navigate to the project directory
cd build_mpq

# Install in development mode
pip install -e .

# Or install with dev dependencies for testing
pip install -e ".[dev]"
```

## Usage

### 1. Create a Staging Area

Create the canonical WoW 3.3.5a directory structure:

```bash
build-mpq create patch-Z.MPQ
```

This creates all 48 required directories for a complete patch.

**Create only specific categories** to avoid overwhelming directory structures:

```bash
# Create only Interface directories (27 dirs)
build-mpq create ./ui-patch --interface

# Create multiple categories (37 dirs)
build-mpq create ./custom-patch --dbc --interface --sound

# Create only DBC directory (1 dir)
build-mpq create ./dbc-patch --dbc
```

**Available categories:**
- `--dbc` - DBC files (DBFilesClient/)
- `--interface` - UI, icons, addons (Interface/*)
- `--fonts` - Font files (Fonts/)
- `--sound` - Audio files (Sound/*)
- `--textures` - Environment textures (Textures/*)
- `--models` - Character, creature, item models
- `--world` - Map data (World/*)
- `--cameras` - Camera files

**Note:** Empty directories are automatically excluded during MPQ packaging, so there's no bloat concern.

**Force recreation** if it already exists:

```bash
build-mpq create patch-Z.MPQ --force
```

### 2. Add Your Files

Place your custom files in the appropriate directories within the staging area.

**Option A: Copy files** (simple, but duplicates data):

```bash
# Copy files into staging area
cp my_spell_icon.blp patch-Z.MPQ/Interface/Icons/
cp MyCustom.dbc patch-Z.MPQ/DBFilesClient/
cp my_music.mp3 patch-Z.MPQ/Sound/Music/
```

**Option B: Use symbolic links** (recommended for development):

> **Windows Users:** Creating symlinks on Windows requires either Administrator privileges or [Developer Mode](https://learn.microsoft.com/en-us/windows/apps/get-started/enable-your-device-for-development) enabled (Windows 10+). Use `mklink` instead of `ln -s`. Alternatively, use Option A (copy files). The tool itself works fine on Windows - symlink creation is a Windows platform limitation.

```bash
# Link to your asset library (no duplication!)
ln -s ~/wow-assets/custom/icons/*.blp patch-Z.MPQ/Interface/Icons/
ln -s ~/wow-assets/custom/Spell.dbc patch-Z.MPQ/DBFilesClient/
ln -s ~/wow-assets/music/*.mp3 patch-Z.MPQ/Sound/Music/

# Symlinks are automatically resolved during packaging
# The MPQ will contain the actual file data, not broken links
```

**Benefits of symlinks:**
- ✅ No file duplication - saves disk space
- ✅ Edit assets in place - changes reflected immediately
- ✅ Multiple staging areas can reference same assets
- ✅ Symlinks are resolved during packaging - MPQ contains real data
- ✅ Broken symlinks are detected and skipped with warnings

Note: By default packaging will *dereference* symlinks — we copy symlink targets into a temporary staging tree and invoke `mpqcli` from that copy so the MPQ contains the expected relative file paths. If you prefer to keep symlinks intact, use `--no-dereference` to disable this behavior. Broken symlinks are reported (warning) and skipped.

### 3. Package the MPQ

Create an MPQ file from your staging area:

```bash
build-mpq package patch-Z.MPQ patch-Z.mpq
```

**With different compression:**

```bash
# zlib compression (default, recommended)
build-mpq package patch-Z.MPQ patch-Z.mpq -c z

# bzip2 compression (better compression, slower)
build-mpq package patch-Z.MPQ patch-Z.mpq -c b

# No compression (faster, larger files)
build-mpq package patch-Z.MPQ patch-Z.mpq -c n
```

### 4. Validate the MPQ

Check that all files in the MPQ are in valid WoW 3.3.5a directories:

```bash
build-mpq validate patch-Z.mpq
```

**Verbose output** (shows each file):

```bash
build-mpq validate patch-Z.mpq --verbose
```

## Complete Workflow Examples

### Example 1: Custom Spell Icons (UI Only)

```bash
# 1. Create staging area with only Interface directories
build-mpq create ./spell-icons-patch --interface

# 2. Add your custom icon
cp spell_custom_fireball.blp ./spell-icons-patch/Interface/Icons/

# 3. Package into MPQ (empty directories automatically excluded)
build-mpq package ./spell-icons-patch ./patch-icons-1.MPQ

# 4. Validate the structure
build-mpq validate ./patch-icons-1.MPQ

# 5. Deploy to your WoW client
cp ./patch-icons-1.MPQ /path/to/wow/Data/
```

### Example 2: Full Custom Patch (All Categories)

```bash
# 1. Create full staging area
build-mpq create ./custom-patch

# 2. Add your custom files
cp spell_custom_fireball.blp ./custom-patch/Interface/Icons/
cp Spell.dbc ./custom-patch/DBFilesClient/
cp custom_music.mp3 ./custom-patch/Sound/Music/

# 3. Package into MPQ
build-mpq package ./custom-patch ./patch-custom-1.MPQ

# 4. Validate the structure
build-mpq validate ./patch-custom-1.MPQ

# 5. Deploy to your WoW client
cp ./patch-custom-1.MPQ /path/to/wow/Data/
```

## Directory Structure

The tool creates the following canonical WoW 3.3.5a directory structure:

```
staging/
├── DBFilesClient/              # Database files (.dbc)
├── Interface/
│   ├── AddOns/                # Custom AddOns
│   ├── Buttons/               # Button textures
│   ├── Icons/                 # Spell/item icons
│   ├── Glues/                 # Login screen UI
│   └── ...                    # Many more UI directories
├── Fonts/                      # Font files
├── Sound/
│   ├── Music/                 # Background music
│   ├── Spells/                # Spell sound effects
│   ├── Creature/              # Creature sounds
│   └── ...                    # More sound categories
├── Textures/
│   └── Minimap/               # Minimap textures
├── Character/                  # Character models (.m2)
├── Creature/                  # NPC models
├── Item/                       # Item models
├── Spells/                     # Spell effect models
├── World/
│   ├── Maps/                  # ADT, WDT, WMO files
│   └── wmo/                   # World model objects
└── Cameras/                    # Camera files
```

## Why This Structure Matters

The WoW 3.3.5a client has **hard-coded directory scanning**. Files placed in incorrect locations will be silently ignored by the client. This tool ensures:

1. ✅ All directories follow the exact structure the client expects
2. ✅ Validation catches misplaced files before deployment
3. ✅ No guesswork - the structure is canonical and complete

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=build_mpq --cov-report=html

# Run specific test file
pytest tests/test_structure.py
```

### Project Structure

```
build_mpq/
├── build_mpq/
│   ├── __init__.py           # Package initialization
│   ├── cli.py                # CLI entry point
│   ├── operations.py         # Core MPQ operations
│   └── structure.py          # WoW directory definitions
├── tests/
│   ├── test_cli.py           # CLI tests
│   ├── test_operations.py    # Operations tests
│   └── test_structure.py     # Structure validation tests
├── pyproject.toml            # Project configuration
└── README.md                 # This file
```

## Troubleshooting

### "mpqcli not found in PATH"

Install mpqcli following the instructions in the Requirements section above.

### "Validation failed: X file(s) in invalid locations"

Your MPQ contains files in directories that the WoW client won't read. Common issues:

- ❌ `CustomFolder/myfile.dbc` → ✅ `DBFilesClient/myfile.dbc`
- ❌ `Icons/spell.blp` → ✅ `Interface/Icons/spell.blp`
- ❌ `Music/song.mp3` → ✅ `Sound/Music/song.mp3`

Use `build-mpq validate --verbose` to see which files are problematic.

### "Staging area already exists"

Use `--force` to recreate: `build-mpq create ./staging --force`

### Broken Symbolic Links Warning

If you see warnings about broken symbolic links during packaging:

```
⚠ Warning: 2 broken symbolic link(s) detected:
  - Interface/Icons/missing.blp -> ~/assets/missing.blp (target not found)
```

**Cause:** Symlink points to a file that doesn't exist or has been moved.

**Solution:**
1. Check that the target file exists: `ls -l staging/Interface/Icons/missing.blp`
2. Fix the symlink: `ln -sf ~/assets/correct.blp staging/Interface/Icons/missing.blp`
3. Or remove broken links: `find staging -xtype l -delete`

Broken symlinks are automatically skipped during packaging.

## Contributing

Contributions are welcome! Please ensure:

1. All tests pass: `pytest`
2. Type hints are used throughout
3. Code follows the existing style
4. New features include tests

## References

- [AzerothCore](https://www.azerothcore.org/)
- [mpqcli](https://github.com/Kanma/mpqcli)
- [WoW 3.3.5a Client Documentation](https://wowdev.wiki/)

---

**Made with ❤️ for the AzerothCore community**
