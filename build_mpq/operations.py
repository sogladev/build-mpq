"""Core operations for MPQ patch building and validation."""

import shutil
import subprocess
import os
import tempfile
import errno
from shutil import copy2
from pathlib import Path

from .structure import get_available_categories, get_valid_directories, is_valid_path


class MPQError(Exception):
    """Base exception for MPQ operations."""
    pass


class MPQCliNotFoundError(MPQError):
    """Raised when mpqcli is not found in PATH."""
    pass


class ValidationError(MPQError):
    """Raised when MPQ validation fails."""
    pass


def create_staging_area(
    base_path: Path,
    *,
    force: bool = False,
    categories: list[str] | None = None,
) -> None:
    """Create the WoW 3.3.5a patch staging directory structure.

    Args:
        base_path: Root directory where staging area will be created
        force: If True, recreate the staging area even if it exists
        categories: Optional list of category names to create.
                   If None, creates all directories.
                   Valid: dbc, interface, fonts, sound, textures, models, world, cameras

    Raises:
        FileExistsError: If staging area exists and force=False
        ValueError: If invalid category names are provided
    """
    if base_path.exists() and not force:
        raise FileExistsError(
            f"Staging area already exists at {base_path}. "
            "Use --force to recreate it."
        )

    # Validate categories
    if categories:
        available = get_available_categories()
        invalid = [c for c in categories if c not in available]
        if invalid:
            raise ValueError(
                f"Invalid categories: {', '.join(invalid)}. "
                f"Valid categories: {', '.join(available)}"
            )

    if force and base_path.exists():
        print(f"Removing existing staging area at {base_path}")
        shutil.rmtree(base_path)

    print(f"Creating staging area at {base_path}")
    if categories:
        print(f"Categories: {', '.join(categories)}")

    directories = get_valid_directories(categories)

    for directory in directories:
        dir_path = base_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)

    # Create a README in the staging area
    readme_path = base_path / "README.txt"

    category_info = ""
    if categories:
        category_info = f"\nCreated categories: {', '.join(categories)}\n"

    readme_content = f"""WoW 3.3.5a Patch Staging Area
================================
{category_info}
This directory structure is required by the WoW 3.3.5a client.
Place your custom files in the appropriate directories:

- DBFilesClient/       - DBC files (game data tables)
- Interface/           - UI, icons, and interface assets
- Fonts/               - Font files
- Sound/               - Audio files (music, effects, voices)
- Textures/            - Environment textures, minimaps
- Character/           - Character models
- Creature/           - Creature models
- Item/                - Item models
- Spells/              - Spell effects and models
- World/               - Map data (ADT, WDT, WMO files)
- Cameras/             - Camera files

After placing your files, use:
  build-mpq package <staging_dir> <output.mpq>

To validate the MPQ:
  build-mpq validate <output.mpq>
"""
    readme_path.write_text(readme_content, encoding="utf-8")

    print(f"✓ Created {len(directories)} directories")


def package_mpq(
    staging_path: Path,
    output_path: Path,
    *,
    compression: str = "z",
    dereference_symlinks: bool = True,
) -> None:
    """Package the staging area into an MPQ file using mpqcli.

    Args:
        staging_path: Path to the staging area directory
        output_path: Path where the MPQ file will be created
        compression: Compression method (z=zlib, b=bzip2, n=none)

    Raises:
        MPQCliNotFoundError: If mpqcli is not found in PATH
        FileNotFoundError: If staging_path doesn't exist
        MPQError: If mpqcli fails
    """
    if not staging_path.exists():
        raise FileNotFoundError(f"Staging area not found: {staging_path}")

    if not staging_path.is_dir():
        raise NotADirectoryError(f"Staging path is not a directory: {staging_path}")

    # Check if mpqcli is available
    if not shutil.which("mpqcli"):
        raise MPQCliNotFoundError(
            "mpqcli not found in PATH. Please install mpqcli first.\n"
            "Installation instructions: https://github.com/Kanma/mpqcli"
        )

    # Remove existing MPQ if present
    if output_path.exists():
        if output_path.is_dir():
            raise IsADirectoryError(f"Output path is a directory: {output_path}")

        print(f"Removing existing MPQ: {output_path}")
        output_path.unlink()

    output_dir = output_path.parent
    if not output_dir.exists():
        print(f"Creating output directory: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Packaging {staging_path} -> {output_path}")
    print(f"Compression: {compression}")

    # Build the mpqcli command
    # Correct usage: mpqcli create --output <output.mpq> <target_dir>
    # We'll invoke mpqcli from the staging directory and pass '.' as the target
    cmd = [
        "mpqcli",
        "create",
        "--output",
        str(output_path.absolute()),
        ".",
    ]

    # Add all files from staging area (including symlink targets) for reporting only
    files_to_add: list[Path] = []
    broken_symlinks: list[Path] = []
    symlink_count = 0

    for item in staging_path.rglob("*"):
        # Skip the README.txt
        if item.name == "README.txt":
            continue

        # Handle symlinks - check if they resolve correctly
        if item.is_symlink():
            symlink_count += 1
            try:
                # Verify the symlink target exists and is a file
                if item.resolve(strict=True).is_file():
                    files_to_add.append(item)
                else:
                    broken_symlinks.append(item)
            except (OSError, RuntimeError) as e:
                # Broken or cyclic symlink
                broken_symlinks.append(item)
        elif item.is_file():
            # Regular file
            files_to_add.append(item)

    # Report findings
    if symlink_count > 0:
        print(f"Found {symlink_count} symbolic link(s)")

    if broken_symlinks:
        print(f"\n⚠ Warning: {len(broken_symlinks)} broken symbolic link(s) detected:")
        for link in broken_symlinks:
            relative = link.relative_to(staging_path)
            try:
                target = link.readlink()
                print(f"  - {relative} -> {target} (target not found)")
            except OSError:
                print(f"  - {relative} (unreadable symlink)")
        print("\nThese files will be skipped in the MPQ.")

    if not files_to_add:
        print("⚠ Warning: No valid files found in staging area")
        print("   The MPQ will be created but will be empty.")
    else:
        valid_regular = len(files_to_add) - (symlink_count - len(broken_symlinks))
        valid_symlinks = symlink_count - len(broken_symlinks)
        print(f"Packaging {len(files_to_add)} file(s): {valid_regular} regular, {valid_symlinks} symlinked")

    # Note: we do NOT pass individual files to mpqcli; we pass the staging directory as the target
    # This preserves the file paths inside the MPQ and avoids adding absolute host paths.

    # By default we dereference symlinks by creating a temporary staging copy with files copied
    temp_dir_obj = None
    run_cwd = staging_path
    if dereference_symlinks:
        temp_dir_obj = tempfile.TemporaryDirectory(prefix="build_mpq_")
        temp_root = Path(temp_dir_obj.name) / staging_path.name

        print(f"Creating dereferenced staging copy at {temp_root}")

        # Walk the staging tree and copy files; dereference symlinks by copying their targets
        for root, dirs, files in os.walk(staging_path):
            root_path = Path(root)
            rel_root = root_path.relative_to(staging_path)
            dest_root = temp_root / rel_root
            dest_root.mkdir(parents=True, exist_ok=True)

            for fname in files:
                src_file = root_path / fname
                dest_file = dest_root / fname

                if src_file.is_symlink():
                    try:
                        target = src_file.resolve(strict=True)
                        if target.is_file():
                            # Try to create a hard link to save space; fall back to copy on cross-device or permission errors
                            try:
                                os.link(target, dest_file)
                            except OSError as e:
                                if e.errno in (errno.EXDEV, errno.EPERM, errno.EACCES):
                                    # Cross-device or permission issue -> fallback to copy
                                    copy2(target, dest_file)
                                else:
                                    raise
                        else:
                            # Skip non-file symlink targets
                            print(f"Skipping non-file symlink target: {src_file}")
                    except (OSError, RuntimeError):
                        # Broken symlink; skip and warn
                        print(f"Skipping broken symlink: {src_file}")
                elif src_file.is_file():
                    # For regular files, prefer hardlinks to avoid duplicating large files
                    try:
                        os.link(src_file, dest_file)
                    except OSError as e:
                        if e.errno in (errno.EXDEV, errno.EPERM, errno.EACCES):
                            copy2(src_file, dest_file)
                        else:
                            raise

        run_cwd = temp_root

    # Print the command for easier diagnostics
    print(f"Running command: {' '.join(cmd)} (cwd={run_cwd})")

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=run_cwd,
        )

        if result.stdout:
            print(result.stdout)

        print(f"✓ Successfully created MPQ: {output_path.absolute()}")

        # Show file size
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"  Size: {size_mb:.2f} MB")

    except subprocess.CalledProcessError as e:
        # Include the invoked command and working directory to aid debugging
        error_msg = (
            f"mpqcli failed with exit code {e.returncode}\n"
            f"Command: {' '.join(cmd)}\n"
            f"Cwd: {staging_path}\n"
        )
        if e.stderr:
            error_msg += f"{e.stderr}"
        raise MPQError(error_msg) from e
    finally:
        # Cleanup temporary staging copy if created
        if temp_dir_obj is not None:
            try:
                temp_dir_obj.cleanup()
            except Exception:
                pass


def validate_mpq(mpq_path: Path, *, verbose: bool = False) -> bool:
    """Validate that an MPQ file follows the WoW 3.3.5a directory structure.

    Args:
        mpq_path: Path to the MPQ file to validate
        verbose: If True, print detailed validation information

    Returns:
        True if validation passes

    Raises:
        FileNotFoundError: If MPQ file doesn't exist
        MPQCliNotFoundError: If mpqcli is not found in PATH
        ValidationError: If validation fails
    """
    if not mpq_path.exists():
        raise FileNotFoundError(f"MPQ file not found: {mpq_path}")

    if not shutil.which("mpqcli"):
        raise MPQCliNotFoundError(
            "mpqcli not found in PATH. Please install mpqcli first."
        )

    print(f"Validating MPQ: {mpq_path}")

    # List files in the MPQ
    cmd = ["mpqcli", "list", str(mpq_path.absolute())]

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )

        file_list = result.stdout.strip().split("\n") if result.stdout.strip() else []

        if not file_list or (len(file_list) == 1 and not file_list[0]):
            print("⚠ Warning: MPQ appears to be empty")
            return True

        print(f"Found {len(file_list)} files in MPQ")

        # Validate each file path
        invalid_paths: list[str] = []
        valid_count = 0

        for file_path in file_list:
            file_path = file_path.strip()
            if not file_path:
                continue

            if is_valid_path(file_path):
                valid_count += 1
                if verbose:
                    print(f"  ✓ {file_path}")
            else:
                invalid_paths.append(file_path)
                if verbose:
                    print(f"  ✗ {file_path}")

        print(f"\nValidation Results:")
        print(f"  Valid files:   {valid_count}")
        print(f"  Invalid files: {len(invalid_paths)}")

        if invalid_paths:
            print("\n⚠ The following files are in invalid locations:")
            for path in invalid_paths:
                print(f"  - {path}")
            print("\nThese files will NOT be loaded by the WoW 3.3.5a client!")
            print("Please move them to the correct directories in your staging area.")
            raise ValidationError(
                f"{len(invalid_paths)} file(s) in invalid locations"
            )

        print("\n✓ All files are in valid WoW 3.3.5a directories")
        return True

    except subprocess.CalledProcessError as e:
        error_msg = f"mpqcli failed with exit code {e.returncode}"
        if e.stderr:
            error_msg += f"\n{e.stderr}"
        raise MPQError(error_msg) from e
