# Quick Start Guide

## Installation

```bash
cd /path/to/build_mpq
pip install -e ".[dev]"
```

## Basic Workflow

### 1. Create Staging Area (One-Time)

```bash
# Create full structure (all 48 directories)
python -m build_mpq.cli create ./my-custom-patch

# OR create only specific categories
python -m build_mpq.cli create ./ui-patch --interface
python -m build_mpq.cli create ./sound-patch --sound --dbc
```

Categories: `--dbc`, `--interface`, `--fonts`, `--sound`, `--textures`, `--models`, `--world`, `--cameras`

**Note:** Empty directories are automatically excluded during packaging.

### 2. Add Your Custom Files

```bash
# Example: Add a custom spell icon
cp my_custom_spell.blp ./my-custom-patch/Interface/Icons/

# Example: Add modified DBC
cp Spell.dbc ./my-custom-patch/DBFilesClient/

# Example: Add custom music
cp epic_theme.mp3 ./my-custom-patch/Sound/Music/
```

### 3. Package into MPQ

```bash
python -m build_mpq.cli package ./my-custom-patch ./patch-custom-1.MPQ
```

### 4. Validate Structure

```bash
python -m build_mpq.cli validate ./patch-custom-1.MPQ
```

### 5. Deploy to WoW Client

```bash
# Copy to your WoW Data folder
cp ./patch-custom-1.MPQ /path/to/wow/Data/
```

The patch will be automatically loaded by the client on startup!

## Testing Your Module

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=build_mpq

# Run specific test file
pytest tests/test_structure.py -v
```

## Using as a Python Module

```python
from pathlib import Path
from build_mpq.operations import create_staging_area, package_mpq, validate_mpq

# Create staging area
staging = Path("./my-patch")
create_staging_area(staging)

# Add files programmatically
(staging / "DBFilesClient" / "MyData.dbc").write_bytes(dbc_data)

# Package
output = Path("patch-Z.mpq")
package_mpq(staging, output)

# Validate
validate_mpq(output, verbose=True)
```

## Command Reference

### Create Command

```bash
python -m build_mpq.cli create <path> [--force]
```

- `path`: Where to create the staging area
- `--force`: Recreate if already exists

### Package Command

```bash
python -m build_mpq.cli package <staging> <output> [-c {z,b,n}]
```

- `staging`: Path to staging directory
- `output`: Output MPQ filename
- `-c`: Compression (z=zlib, b=bzip2, n=none)

### Validate Command

```bash
python -m build_mpq.cli validate <mpq> [--verbose]
```

- `mpq`: MPQ file to validate
- `--verbose`: Show detailed output for each file

## Help

```bash
python -m build_mpq.cli --help
python -m build_mpq.cli create --help
python -m build_mpq.cli package --help
python -m build_mpq.cli validate --help
```
