"""Demonstration of symlink support for development workflow.

This example shows how to use symbolic links in your staging area during
development, avoiding the need to copy large asset files.
"""

from pathlib import Path
import tempfile

from build_mpq.operations import create_staging_area, package_mpq


def demo_symlink_workflow():
    """Demonstrate using symlinks in staging area (development pattern)."""

    print("=== Symlink Development Workflow Demo ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Step 1: Create your actual asset directory (outside staging)
        print("Step 1: Creating asset library...")
        asset_library = tmp_path / "asset_library"
        asset_library.mkdir()

        # Simulate large asset files
        spell_dbc = asset_library / "Spell.dbc"
        spell_dbc.write_bytes(b"DBC_FILE_" + b"X" * 1000)  # Simulated large file

        icon_blp = asset_library / "spell_custom_fireball.blp"
        icon_blp.write_bytes(b"BLP_ICON_" + b"Y" * 2000)

        music_mp3 = asset_library / "epic_theme.mp3"
        music_mp3.write_bytes(b"MP3_AUDIO_" + b"Z" * 5000)

        print(f"  Created {spell_dbc.name} ({spell_dbc.stat().st_size} bytes)")
        print(f"  Created {icon_blp.name} ({icon_blp.stat().st_size} bytes)")
        print(f"  Created {music_mp3.name} ({music_mp3.stat().st_size} bytes)")
        print()

        # Step 2: Create staging area with only needed categories
        print("Step 2: Creating staging area (dbc, interface, sound only)...")
        staging = tmp_path / "patch-staging"
        create_staging_area(staging, categories=["dbc", "interface", "sound"])
        print()

        # Step 3: Create symbolic links instead of copying files
        print("Step 3: Creating symbolic links to assets...")

        dbc_link = staging / "DBFilesClient" / "Spell.dbc"
        dbc_link.symlink_to(spell_dbc.absolute())
        print(f"  Linked: {dbc_link.relative_to(staging)} -> {spell_dbc}")

        icon_link = staging / "Interface" / "Icons" / "spell_custom_fireball.blp"
        icon_link.symlink_to(icon_blp.absolute())
        print(f"  Linked: {icon_link.relative_to(staging)} -> {icon_blp}")

        music_link = staging / "Sound" / "Music" / "epic_theme.mp3"
        music_link.symlink_to(music_mp3.absolute())
        print(f"  Linked: {music_link.relative_to(staging)} -> {music_mp3}")
        print()

        # Step 4: Verify links work
        print("Step 4: Verifying symbolic links...")
        assert dbc_link.is_symlink() and dbc_link.exists()
        assert icon_link.is_symlink() and icon_link.exists()
        assert music_link.is_symlink() and music_link.exists()
        print("  ✓ All symlinks valid and resolvable")
        print()

        # Step 5: Package MPQ (symlinks will be resolved)
        print("Step 5: Packaging MPQ (symlinks will be resolved automatically)...")
        output_mpq = tmp_path / "patch-custom-1.MPQ"

        print("\n--- Package Output ---")
        try:
            package_mpq(staging, output_mpq)
            print("--- End Package Output ---\n")

            if output_mpq.exists():
                size_kb = output_mpq.stat().st_size / 1024
                print(f"✓ MPQ created successfully: {output_mpq.name} ({size_kb:.2f} KB)")
                print(f"  Location: {output_mpq}")
            else:
                print("⚠ Note: mpqcli not installed, but workflow demonstrated")
        except Exception as e:
            print(f"⚠ mpqcli error (expected if not installed): {e}")
            print("  The workflow is correct - install mpqcli to actually create MPQs")
        print()

        # Step 6: Show the benefits
        print("=== Benefits of Symlink Workflow ===")
        print()
        print("✓ No file duplication - saves disk space")
        print("✓ Edit assets in place - changes reflected immediately")
        print("✓ Easy to manage large asset libraries")
        print("✓ Multiple staging areas can reference same assets")
        print("✓ Symlinks are resolved during packaging - MPQ contains real data")
        print()
        print("=== Real-World Usage ===")
        print()
        print("# Your actual workflow:")
        print("cd /home/pc/Desktop/acore-custom-staging")
        print()
        print("# Create staging for your patch")
        print("build-mpq create patch-Z --interface --dbc")
        print()
        print("# Link your assets (instead of copying)")
        print("ln -s ~/wow-assets/custom/Spell.dbc patch-Z/DBFilesClient/")
        print("ln -s ~/wow-assets/custom/icons/*.blp patch-Z/Interface/Icons/")
        print()
        print("# Package (symlinks auto-resolved)")
        print("build-mpq package patch-Z patch-Z.MPQ")
        print()
        print("# Validate")
        print("build-mpq validate patch-Z.MPQ")


if __name__ == "__main__":
    demo_symlink_workflow()
