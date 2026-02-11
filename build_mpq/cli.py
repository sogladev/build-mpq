"""Command-line interface for WoW 3.3.5a MPQ patch builder."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .operations import (
    MPQCliNotFoundError,
    MPQError,
    ValidationError,
    create_staging_area,
    package_mpq,
    validate_mpq,
)

def cmd_create(args: argparse.Namespace) -> int:
    """Handle the 'create' command."""
    staging_path = Path(args.path).resolve()

    # Build list of categories from flags
    categories: list[str] | None = None
    if any([args.dbc, args.interface, args.fonts, args.sound, args.textures,
            args.models, args.world, args.cameras]):
        categories = []
        if args.dbc:
            categories.append("dbc")
        if args.interface:
            categories.append("interface")
        if args.fonts:
            categories.append("fonts")
        if args.sound:
            categories.append("sound")
        if args.textures:
            categories.append("textures")
        if args.models:
            categories.append("models")
        if args.world:
            categories.append("world")
        if args.cameras:
            categories.append("cameras")

    try:
        create_staging_area(staging_path, force=args.force, categories=categories)
        return 0
    except FileExistsError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error creating staging area: {e}", file=sys.stderr)
        return 1


def cmd_package(args: argparse.Namespace) -> int:
    """Handle the 'package' command."""
    staging_path = Path(args.staging).resolve()
    output_path = Path(args.output).resolve()

    try:
        package_mpq(
            staging_path,
            output_path,
            compression=args.compression,
            dereference_symlinks=args.dereference,
        )
        return 0
    except MPQCliNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except MPQError as e:
        print(f"Error packaging MPQ: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def cmd_validate(args: argparse.Namespace) -> int:
    """Handle the 'validate' command."""
    mpq_path = Path(args.mpq).resolve()

    try:
        validate_mpq(mpq_path, verbose=args.verbose)
        return 0
    except ValidationError as e:
        print(f"\n✗ Validation failed: {e}", file=sys.stderr)
        return 1
    except MPQCliNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except MPQError as e:
        print(f"Error validating MPQ: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="build-mpq",
        description="Build and validate WoW 3.3.5a client patch MPQ files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create full staging area (all categories)
  build-mpq create patch-Z.MPQ

  # Create staging area for specific categories
  build-mpq create ./ui-patch --interface --fonts
  build-mpq create ./sound-patch --sound

  # Package the staging area into an MPQ
  build-mpq package patch-Z.MPQ patch-Z.mpq

  # Validate the MPQ structure
  build-mpq validate patch-Z.mpq

  # Validate with verbose output
  build-mpq validate patch-Z.mpq --verbose

Note: Empty directories are automatically excluded during packaging.

For more information, visit: https://github.com/sogladev/azerothcore-dev
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Available commands",
    )

    # Create command
    create_parser = subparsers.add_parser(
        "create",
        help="Create a new WoW 3.3.5a patch staging directory structure",
        description="Create the canonical WoW 3.3.5a directory structure for patch files.",
        epilog="""
Category flags (optional - creates all if none specified):
  --dbc         DBC files (DBFilesClient/)
  --interface   UI, icons, addons (Interface/*)
  --fonts       Font files (Fonts/)
  --sound       Audio files (Sound/*)
  --textures    Environment textures (Textures/*)
  --models      Character, creature, item models (Character/, Creature/, Item/, Spells/)
  --world       Map data (World/*)
  --cameras     Camera files (Cameras/)

Examples:
  # Create full structure (all categories)
  build-mpq create ./my-patch

  # Create only Interface directories
  build-mpq create ./ui-patch --interface

  # Create multiple categories
  build-mpq create ./custom-patch --interface --sound --dbc
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    create_parser.add_argument(
        "path",
        type=str,
        help="Path where the staging area will be created (example: build-mpq create patch-Z.mpq)",
    )
    create_parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Force recreation if staging area already exists",
    )

    # Category flags
    category_group = create_parser.add_argument_group("categories")
    category_group.add_argument(
        "--dbc",
        action="store_true",
        help="Create DBC directories (DBFilesClient/)",
    )
    category_group.add_argument(
        "--interface",
        action="store_true",
        help="Create Interface directories (UI, icons, addons)",
    )
    category_group.add_argument(
        "--fonts",
        action="store_true",
        help="Create Fonts directory",
    )
    category_group.add_argument(
        "--sound",
        action="store_true",
        help="Create Sound directories (music, effects, voices)",
    )
    category_group.add_argument(
        "--textures",
        action="store_true",
        help="Create Textures directories (minimaps, NPCs)",
    )
    category_group.add_argument(
        "--models",
        action="store_true",
        help="Create model directories (Character, Creature, Item, Spells)",
    )
    category_group.add_argument(
        "--world",
        action="store_true",
        help="Create World directories (maps, WMO)",
    )
    category_group.add_argument(
        "--cameras",
        action="store_true",
        help="Create Cameras directory",
    )

    create_parser.set_defaults(func=cmd_create)

    # Package command
    package_parser = subparsers.add_parser(
        "package",
        help="Package a staging area into an MPQ file",
        description="Create an MPQ file from the staging directory using mpqcli.",
    )
    package_parser.add_argument(
        "staging",
        type=str,
        help="Path to the staging area directory",
    )
    package_parser.add_argument(
        "output",
        type=str,
        help="Output MPQ file path (e.g., patch-1.MPQ)",
    )
    package_parser.add_argument(
        "-c", "--compression",
        type=str,
        choices=["z", "b", "n"],
        default="z",
        help="Compression method: z=zlib (default), b=bzip2, n=none",
    )
    package_parser.add_argument(
        "--no-dereference",
        dest="dereference",
        action="store_false",
        help="Disable dereferencing of symbolic links (by default symlinks are dereferenced and copied into a temporary staging tree)",
    )
    package_parser.set_defaults(func=cmd_package)

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate an MPQ file structure",
        description="Check that all files in the MPQ are in valid WoW 3.3.5a directories.",
    )
    validate_parser.add_argument(
        "mpq",
        type=str,
        help="Path to the MPQ file to validate",
    )
    validate_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed validation output for each file",
    )
    validate_parser.set_defaults(func=cmd_validate)

    # Parse arguments
    args = parser.parse_args()

    # Execute the appropriate command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
