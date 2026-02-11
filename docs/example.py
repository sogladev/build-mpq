"""Example workflow script for building a WoW 3.3.5a patch.

This demonstrates how to use the build_mpq module programmatically.
"""

from pathlib import Path

from build_mpq.operations import create_staging_area, package_mpq, validate_mpq


def main() -> None:
    """Example workflow for creating a custom patch."""
    # Define paths
    staging_dir = Path("./example-patch-staging")
    output_mpq = Path("./patch-example-1.MPQ")

    print("=== WoW 3.3.5a Patch Builder Example ===\n")

    # Step 1: Create staging area
    print("Step 1: Creating staging area...")
    try:
        create_staging_area(staging_dir, force=True)
        print("✓ Staging area created\n")
    except Exception as e:
        print(f"✗ Failed to create staging area: {e}")
        return

    # Step 2: Add example files (in a real workflow, you'd copy actual files)
    print("Step 2: Adding example files...")
    example_dbc = staging_dir / "DBFilesClient" / "Example.dbc"
    example_dbc.write_text("This is example DBC data")

    example_icon = staging_dir / "Interface" / "Icons" / "example_spell.blp"
    example_icon.write_text("This is example icon data")

    print(f"  Added: {example_dbc.relative_to(staging_dir)}")
    print(f"  Added: {example_icon.relative_to(staging_dir)}")
    print("✓ Files added\n")

    # Step 3: Package into MPQ
    print("Step 3: Packaging MPQ...")
    try:
        package_mpq(staging_dir, output_mpq, compression="z")
        print("✓ MPQ packaged\n")
    except Exception as e:
        print(f"✗ Failed to package MPQ: {e}")
        print("  Make sure mpqcli is installed and in your PATH")
        return

    # Step 4: Validate MPQ
    print("Step 4: Validating MPQ structure...")
    try:
        validate_mpq(output_mpq, verbose=False)
        print("✓ Validation passed\n")
    except Exception as e:
        print(f"✗ Validation failed: {e}\n")
        return

    print("=== Workflow Complete ===")
    print(f"\nYour patch is ready: {output_mpq.absolute()}")
    print(f"Copy it to your WoW Data/ folder to use it.")


if __name__ == "__main__":
    main()
