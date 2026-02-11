"""WoW 3.3.5a client directory structure definitions.

This module defines the canonical directory structure that the WoW 3.3.5a client
expects for various asset types. These paths are hard-coded in the client and
must be followed exactly.
"""

from typing import Final

# Directory structure organized by category
CATEGORIES: Final[dict[str, list[str]]] = {
    "dbc": [
        "DBFilesClient",
    ],
    "interface": [
        "Interface/AddOns",
        "Interface/Buttons",
        "Interface/Cinematics",
        "Interface/Cursors",
        "Interface/DialogFrame",
        "Interface/FriendsFrame",
        "Interface/Glues",
        "Interface/GMSurveyUI",
        "Interface/GuildBankFrame",
        "Interface/Icons",
        "Interface/ItemTextFrame",
        "Interface/lfgframe",
        "Interface/MacroFrame",
        "Interface/Minimap",
        "Interface/PaperDollInfoFrame",
        "Interface/PetPaperDollFrame",
        "Interface/PVPFrame",
        "Interface/QuestFrame",
        "Interface/RaidFrame",
        "Interface/SpellBook",
        "Interface/Stationery",
        "Interface/TalentFrame",
        "Interface/TargetingFrame",
        "Interface/Tooltips",
        "Interface/TradeSkillFrame",
        "Interface/WorldMap",
        "Interface/WorldStateFrame",
    ],
    "fonts": [
        "Fonts",
    ],
    "sound": [
        "Sound/Ambience",
        "Sound/Creature",
        "Sound/Doodad",
        "Sound/EmotesVocal",
        "Sound/Events",
        "Sound/Interface",
        "Sound/Item",
        "Sound/Music",
        "Sound/Spells",
    ],
    "textures": [
        "Textures/Minimap",
        "Textures/BakedNpcTextures",
    ],
    "models": [
        "Character",
        "Creature",
        "Item",
        "Spells",
    ],
    "world": [
        "World/Maps",
        "World/Minimaps",
        "World/wmo",
    ],
    "cameras": [
        "Cameras",
    ],
}

# The complete canonical WoW 3.3.5a patch directory structure
# These are the ONLY paths the client will scan for specific asset types
WOW_335_STRUCTURE: Final[list[str]] = [
    path
    for category_paths in CATEGORIES.values()
    for path in category_paths
]


def get_valid_directories(categories: list[str] | None = None) -> list[str]:
    """Return the list of valid WoW 3.3.5a patch directories.

    Args:
        categories: Optional list of category names to filter by.
                   If None, returns all directories.
                   Valid categories: dbc, interface, fonts, sound, textures, models, world, cameras

    Returns:
        List of directory paths for the specified categories
    """
    if categories is None:
        return WOW_335_STRUCTURE.copy()

    result: list[str] = []
    for category in categories:
        if category in CATEGORIES:
            result.extend(CATEGORIES[category])

    return result


def get_available_categories() -> list[str]:
    """Return the list of available category names."""
    return list(CATEGORIES.keys())


def is_valid_path(path: str) -> bool:
    """Check if a path starts with a valid WoW 3.3.5a directory.

    Args:
        path: Relative path to check (e.g., "Interface/Icons/spell.blp")

    Returns:
        True if the path starts with a valid WoW directory structure
    """
    normalized = path.replace("\\", "/")
    return any(
        normalized.startswith(valid_dir + "/") or normalized == valid_dir
        for valid_dir in WOW_335_STRUCTURE
    )
