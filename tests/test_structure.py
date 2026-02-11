"""Tests for directory structure definitions."""

from build_mpq.structure import (
    CATEGORIES,
    WOW_335_STRUCTURE,
    get_available_categories,
    get_valid_directories,
    is_valid_path,
)


def test_structure_is_not_empty():
    """Test that the structure list is not empty."""
    assert len(WOW_335_STRUCTURE) > 0


def test_structure_contains_expected_directories():
    """Test that key directories are present in the structure."""
    expected_dirs = [
        "DBFilesClient",
        "Interface/Icons",
        "Sound/Music",
        "World/Maps",
        "Character",
    ]

    for directory in expected_dirs:
        assert directory in WOW_335_STRUCTURE, f"{directory} not found in structure"


def test_categories_not_empty():
    """Test that categories dictionary is not empty."""
    assert len(CATEGORIES) > 0
    assert all(len(paths) > 0 for paths in CATEGORIES.values())


def test_get_available_categories():
    """Test getting available category names."""
    categories = get_available_categories()
    assert "dbc" in categories
    assert "interface" in categories
    assert "sound" in categories
    assert "world" in categories


def test_get_valid_directories_returns_copy():
    """Test that get_valid_directories returns a copy, not the original."""
    dirs1 = get_valid_directories()
    dirs2 = get_valid_directories()

    assert dirs1 is not dirs2
    assert dirs1 == dirs2


def test_get_valid_directories_with_categories():
    """Test getting directories for specific categories."""
    # Get only interface directories
    interface_dirs = get_valid_directories(["interface"])
    assert all("Interface/" in d for d in interface_dirs)
    assert len(interface_dirs) > 0
    
    # Get only DBC
    dbc_dirs = get_valid_directories(["dbc"])
    assert "DBFilesClient" in dbc_dirs
    assert len(dbc_dirs) == 1
    
    # Get multiple categories
    multi_dirs = get_valid_directories(["dbc", "fonts"])
    assert "DBFilesClient" in multi_dirs
    assert "Fonts" in multi_dirs


def test_get_valid_directories_invalid_category():
    """Test that invalid categories are silently ignored."""
    dirs = get_valid_directories(["invalid_category"])
    assert len(dirs) == 0


def test_is_valid_path_with_valid_paths():
    """Test is_valid_path with known valid paths."""
    valid_paths = [
        "DBFilesClient/Spell.dbc",
        "Interface/Icons/spell_fire_fireball.blp",
        "Sound/Music/GlueScreenMusic/wow_main_theme.mp3",
        "World/Maps/Azeroth/Azeroth.wdt",
        "Character/Human/Male/HumanMale.m2",
        "Interface/AddOns/MyAddon/MyAddon.lua",
    ]

    for path in valid_paths:
        assert is_valid_path(path), f"Path should be valid: {path}"


def test_is_valid_path_with_invalid_paths():
    """Test is_valid_path with known invalid paths."""
    invalid_paths = [
        "CustomFolder/myfile.txt",
        "Random/Path/file.dbc",
        "spell.dbc",  # Must be in DBFilesClient
        "Data/Icons/icon.blp",  # Wrong directory
    ]

    for path in invalid_paths:
        assert not is_valid_path(path), f"Path should be invalid: {path}"


def test_is_valid_path_handles_backslashes():
    """Test that is_valid_path normalizes Windows-style paths."""
    windows_path = "Interface\\Icons\\spell.blp"
    unix_path = "Interface/Icons/spell.blp"

    assert is_valid_path(windows_path)
    assert is_valid_path(unix_path)


def test_is_valid_path_with_directory_only():
    """Test is_valid_path with just a directory name (no file)."""
    assert is_valid_path("DBFilesClient")
    assert is_valid_path("Interface/Icons")
    assert not is_valid_path("InvalidDir")


def test_structure_no_duplicates():
    """Test that there are no duplicate entries in the structure."""
    assert len(WOW_335_STRUCTURE) == len(set(WOW_335_STRUCTURE))


def test_structure_uses_forward_slashes():
    """Test that all structure paths use forward slashes."""
    for directory in WOW_335_STRUCTURE:
        assert "\\" not in directory, f"Backslash found in: {directory}"
