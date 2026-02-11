# Category Flags Feature

## Overview

Added optional category flags to the `create` command to allow users to create only the directories they need, reducing overwhelm and keeping staging areas focused.

## The Problem

Creating all 48 WoW 3.3.5a directories can be overwhelming when users only need a few specific types:
- UI modders only need `Interface/` directories
- Sound modders only need `Sound/` directories
- DBC modders only need `DBFilesClient/`

## The Solution

### Category Flags

Users can now specify which categories of directories to create:

```bash
# Create only Interface directories (27 dirs instead of 48)
build-mpq create ./ui-patch --interface

# Create multiple categories (37 dirs)
build-mpq create ./custom-patch --dbc --interface --sound

# Create all (default behavior - 48 dirs)
build-mpq create ./full-patch
```

### Available Categories

| Flag | Directories Created | Count | Use Case |
|------|-------------------|-------|----------|
| `--dbc` | DBFilesClient/ | 1 | Game data tables |
| `--interface` | Interface/* | 27 | UI, icons, addons |
| `--fonts` | Fonts/ | 1 | Custom fonts |
| `--sound` | Sound/* | 9 | Music, effects, voices |
| `--textures` | Textures/* | 2 | Environment textures |
| `--models` | Character/, Creature/, Item/, Spells/ | 4 | 3D models |
| `--world` | World/* | 3 | Map data (ADT, WDT, WMO) |
| `--cameras` | Cameras/ | 1 | Camera files |

### Empty Directory Handling

**Important:** Empty directories are automatically excluded during MPQ packaging.

The `package_mpq()` function only adds files:

```python
files_to_add: list[Path] = []
for item in staging_path.rglob("*"):
    if item.is_file() and item.name != "README.txt":
        files_to_add.append(item)
```

This means:
- ✅ No bloat in final MPQ files
- ✅ Safe to create all directories (default behavior)
- ✅ But users can still choose categories for cleaner staging areas

## Implementation

### 1. Structure Module (`structure.py`)

Reorganized directories into a `CATEGORIES` dictionary:

```python
CATEGORIES: Final[dict[str, list[str]]] = {
    "dbc": ["DBFilesClient"],
    "interface": ["Interface/AddOns", "Interface/Icons", ...],
    "sound": ["Sound/Music", "Sound/Spells", ...],
    ...
}
```

Added functions:
- `get_valid_directories(categories: list[str] | None)` - Get directories for specific categories
- `get_available_categories()` - List all available category names

### 2. Operations Module (`operations.py`)

Updated `create_staging_area()`:
- Added `categories` parameter
- Validates category names
- Creates only specified directories
- Updates README with selected categories

```python
def create_staging_area(
    base_path: Path,
    *,
    force: bool = False,
    categories: list[str] | None = None,
) -> None:
    ...
```

### 3. CLI Module (`cli.py`)

Added category flags to `create` command:
- Individual flags: `--dbc`, `--interface`, `--fonts`, etc.
- Updated help text with examples
- Maps flags to category list

### 4. Tests

Added new tests:
- `test_categories_not_empty()` - Verify categories dictionary
- `test_get_available_categories()` - Test category listing
- `test_get_valid_directories_with_categories()` - Test filtering
- `test_create_with_categories()` - Test staging area creation
- `test_create_with_invalid_category()` - Test error handling

## Examples

### UI-Only Patch

```bash
# Create only Interface directories
build-mpq create ./ui-patch --interface

# Add UI files
cp custom_icon.blp ./ui-patch/Interface/Icons/

# Package (only Interface/Icons/custom_icon.blp is included)
build-mpq package ./ui-patch ./patch-ui-1.MPQ
```

### Multi-Category Patch

```bash
# Create DBC, Interface, and Sound directories
build-mpq create ./multi-patch --dbc --interface --sound

# Staging area has only:
# - DBFilesClient/
# - Interface/
# - Sound/

# Other directories (World/, Character/, etc.) are NOT created
```

### Full Patch (Default)

```bash
# No flags = all directories
build-mpq create ./full-patch

# All 48 directories are created
```

## Benefits

1. **Less Overwhelming** - Users see only what they need
2. **Cleaner Staging Areas** - Focused directory structure
3. **No Bloat** - Empty directories are excluded anyway
4. **Backwards Compatible** - Default behavior unchanged
5. **Flexible** - Mix and match categories as needed

## Migration

No migration needed! Existing usage continues to work:

```bash
# This still creates all directories
build-mpq create ./my-patch
```

New users can optionally use category flags for a more focused experience.

## CLI Help

```
$ build-mpq create --help

categories:
  --dbc        Create DBC directories (DBFilesClient/)
  --interface  Create Interface directories (UI, icons, addons)
  --fonts      Create Fonts directory
  --sound      Create Sound directories (music, effects, voices)
  --textures   Create Textures directories (minimaps, NPCs)
  --models     Create model directories (Character, Creature, Item, Spells)
  --world      Create World directories (maps, WMO)
  --cameras    Create Cameras directory

Examples:
  # Create full structure (all categories)
  build-mpq create ./my-patch

  # Create only Interface directories
  build-mpq create ./ui-patch --interface

  # Create multiple categories
  build-mpq create ./custom-patch --interface --sound --dbc
```

## Summary

✅ **Added category flags** to `create` command
✅ **Empty directories already excluded** during packaging (no bloat)
✅ **Backwards compatible** - default behavior unchanged
✅ **Well-tested** - added comprehensive test coverage
✅ **Documented** - updated README and QUICKSTART

Users can now choose between:
- **All directories** (default) - complete superset, safest option
- **Specific categories** - focused, less overwhelming, cleaner staging

Both approaches result in the same MPQ output when only files matter!
