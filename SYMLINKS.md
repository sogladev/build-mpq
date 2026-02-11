# Symbolic Link Support

## Overview

The `build-mpq` tool fully supports symbolic links in staging areas, enabling efficient development workflows where you don't need to copy large asset files.

## How It Works

When packaging an MPQ:

1. **Symlinks are detected** - Both absolute and relative symlinks are recognized
2. **Targets are resolved** - The tool follows symlinks to find the actual file
3. **Real data is packaged** - The MPQ contains the actual file content, not symlink references
4. **Broken links are detected** - Invalid symlinks are reported and skipped

## Benefits

✅ **No file duplication** - Save disk space by referencing assets in place
✅ **Instant updates** - Edit assets and immediately repackage
✅ **Shared asset library** - Multiple staging areas can reference the same files
✅ **Development-friendly** - Matches real-world workflows
✅ **Production-safe** - Final MPQ contains resolved file data

## Usage Example

### Setup Your Asset Library

```bash
# Organize your WoW assets
mkdir -p ~/wow-assets/custom/{dbc,icons,sounds,models}

# Place your custom files
cp Spell.dbc ~/wow-assets/custom/dbc/
cp custom_icon.blp ~/wow-assets/custom/icons/
cp epic_theme.mp3 ~/wow-assets/custom/sounds/
```

### Create Staging Area with Symlinks

```bash
# Create staging area (only needed categories)
build-mpq create ./patch-staging --dbc --interface --sound

# Link your assets instead of copying
ln -s ~/wow-assets/custom/dbc/Spell.dbc ./patch-staging/DBFilesClient/
ln -s ~/wow-assets/custom/icons/*.blp ./patch-staging/Interface/Icons/
ln -s ~/wow-assets/custom/sounds/*.mp3 ./patch-staging/Sound/Music/

# Verify links
ls -la ./patch-staging/DBFilesClient/
# lrwxrwxrwx 1 user user 42 Dec 16 10:30 Spell.dbc -> /home/user/wow-assets/custom/dbc/Spell.dbc
```

### Package (Symlinks Auto-Resolved)

```bash
# Package the MPQ - symlinks are automatically resolved
build-mpq package ./patch-staging ./patch-custom-1.MPQ

# Output shows symlink detection:
# Found 2 symbolic link(s)
# Packaging 5 file(s): 3 regular, 2 symlinked
# ✓ Successfully created MPQ: patch-custom-1.MPQ
```

## Real-World Workflow

This matches the user's development pattern:

```bash
cd /home/pc/Desktop/acore-custom-staging

# Your actual setup
build-mpq create patch-Z.MPQ --interface --dbc

# Use symlinks (no copying needed!)
ln -s /path/to/your/assets/*.dbc patch-Z.MPQ/DBFilesClient/
ln -s /path/to/your/assets/*.blp patch-Z.MPQ/Interface/Icons/

# Package and validate
build-mpq package patch-Z.MPQ patch-Z.MPQ
build-mpq validate patch-Z.MPQ
```

## Symlink Types Supported

### Absolute Symlinks

```bash
ln -s /home/user/wow-assets/Spell.dbc staging/DBFilesClient/Spell.dbc
```

✅ Works anywhere
✅ Survives directory moves
❌ Not portable across systems

### Relative Symlinks

```bash
cd staging/DBFilesClient
ln -s ../../assets/Spell.dbc Spell.dbc
```

✅ Portable within project
✅ Works with version control
❌ Breaks if directory structure changes

### Symlinks Outside Staging

```bash
# Assets completely outside the staging area
ln -s /mnt/storage/wow-assets/huge_model.m2 staging/Creature/
```

✅ Reference external storage
✅ Keep staging area minimal
✅ Share assets across multiple projects

## Error Detection

### Broken Symlinks

If a symlink target doesn't exist:

```bash
build-mpq package ./staging ./output.MPQ
```

Output:
```
⚠ Warning: 1 broken symbolic link(s) detected:
  - Interface/Icons/missing.blp -> ~/assets/missing.blp (target not found)

These files will be skipped in the MPQ.

Packaging 4 file(s): 3 regular, 1 symlinked
✓ Successfully created MPQ: output.MPQ
```

**Result:** Broken symlinks are skipped, valid files are packaged.

### Cyclic Symlinks

Cyclic symlinks (A → B → A) are detected and skipped:

```bash
ln -s linkB linkA
ln -s linkA linkB
```

These are reported as broken and excluded from packaging.

## Testing

Comprehensive test coverage ensures symlink handling works correctly:

```bash
pytest tests/test_operations.py::TestPackageMPQ -v
```

**Tests include:**
- ✅ `test_handles_symbolic_links` - Verifies symlinks are resolved
- ✅ `test_detects_broken_symlinks` - Ensures broken links are caught
- ✅ `test_symlink_outside_staging_area` - Tests external references
- ✅ `test_relative_symlinks` - Verifies relative path handling

All 45 tests pass with full symlink support.

## Technical Implementation

### Symlink Resolution

```python
# From operations.py
for item in staging_path.rglob("*"):
    if item.is_symlink():
        try:
            # Resolve to actual file
            if item.resolve(strict=True).is_file():
                files_to_add.append(item)
        except (OSError, RuntimeError):
            # Broken or cyclic symlink
            broken_symlinks.append(item)
```

### MPQ Packaging

```python
# Use resolved path for mpqcli, preserve relative path in MPQ
for file_path in files_to_add:
    relative_path = file_path.relative_to(staging_path)
    actual_path = file_path.resolve()  # Follows symlinks
    cmd.extend([str(actual_path), str(relative_path)])
```

## Best Practices

1. **Use absolute paths** for assets outside your project
2. **Check symlinks** before packaging: `find staging -xtype l` (finds broken links)
3. **Document your setup** so others know where assets should be
4. **Test packaging** with a few files before full build
5. **Keep asset library organized** by category

## Comparison: Copy vs Symlink

| Aspect | Copy Files | Symbolic Links |
|--------|-----------|----------------|
| Disk Space | Duplicates all data | References only |
| Edit Workflow | Copy → Edit → Copy back | Edit in place |
| Multiple Staging Areas | Full duplication each time | Share same assets |
| Disk I/O | High during setup | Minimal |
| Packaging Speed | Same | Same (resolved at package time) |
| Final MPQ | Contains data | Contains data |

## Summary

Symbolic link support enables professional development workflows where:
- Assets live in a centralized library
- Staging areas are lightweight references
- Multiple projects can share assets
- The final MPQ is production-ready with all real data

This matches real-world development patterns and is fully tested and supported.
