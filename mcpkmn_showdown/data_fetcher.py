"""
Data Fetcher for Pokemon Showdown Data

Fetches and parses abilities.ts and items.ts from Pokemon Showdown
to get complete data with descriptions.
"""

import json
import re
import urllib.request
from pathlib import Path


SHOWDOWN_DATA_URL = "https://play.pokemonshowdown.com/data"
CACHE_DIR = Path(__file__).parent.parent / "bot" / "cache"


def fetch_url(url: str) -> str:
    """Fetch content from a URL."""
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode("utf-8")


def parse_typescript_object(ts_content: str, var_name: str) -> dict:
    """
    Parse a TypeScript object export into a Python dict.

    Handles the format: export const VarName: {...} = { ... };
    """
    # Find the object definition
    pattern = rf"export const {var_name}[^=]*=\s*\{{"
    match = re.search(pattern, ts_content, re.IGNORECASE)

    if not match:
        raise ValueError(f"Could not find {var_name} in TypeScript content")

    start = match.end() - 1  # Include the opening brace

    # Find matching closing brace
    brace_count = 0
    end = start
    for i, char in enumerate(ts_content[start:]):
        if char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0:
                end = start + i + 1
                break

    object_str = ts_content[start:end]

    # Convert TypeScript to JSON-like format
    # Remove trailing commas
    object_str = re.sub(r",(\s*[}\]])", r"\1", object_str)

    # Convert single quotes to double quotes
    object_str = object_str.replace("'", '"')

    # Handle unquoted keys
    object_str = re.sub(r"(\s)(\w+)(\s*:)", r'\1"\2"\3', object_str)

    # Handle template literals (backticks)
    object_str = re.sub(r"`([^`]*)`", r'"\1"', object_str)

    # Remove comments
    object_str = re.sub(r"//[^\n]*\n", "\n", object_str)
    object_str = re.sub(r"/\*.*?\*/", "", object_str, flags=re.DOTALL)

    # Handle special TypeScript features
    object_str = re.sub(r"as const", "", object_str)

    try:
        return json.loads(object_str)
    except json.JSONDecodeError as e:
        # Fall back to regex extraction
        return extract_entries_regex(ts_content, var_name)


def extract_entries_regex(ts_content: str, var_name: str) -> dict:
    """
    Extract entries using regex when JSON parsing fails.
    """
    result = {}

    # Pattern to match individual entries
    entry_pattern = r'(\w+):\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}'

    for match in re.finditer(entry_pattern, ts_content):
        entry_id = match.group(1).lower()
        entry_content = match.group(2)

        entry = {"id": entry_id}

        # Extract name
        name_match = re.search(r'name:\s*["\']([^"\']+)["\']', entry_content)
        if name_match:
            entry["name"] = name_match.group(1)

        # Extract desc
        desc_match = re.search(r'desc:\s*["\']([^"\']+)["\']', entry_content)
        if desc_match:
            entry["desc"] = desc_match.group(1)

        # Extract shortDesc
        short_match = re.search(r'shortDesc:\s*["\']([^"\']+)["\']', entry_content)
        if short_match:
            entry["shortDesc"] = short_match.group(1)

        # Extract num
        num_match = re.search(r'num:\s*(\d+)', entry_content)
        if num_match:
            entry["num"] = int(num_match.group(1))

        # For items, extract additional fields
        fling_match = re.search(r'fling:\s*\{[^}]*basePower:\s*(\d+)', entry_content)
        if fling_match:
            entry["flingBasePower"] = int(fling_match.group(1))

        if entry.get("name") or entry.get("desc"):
            result[entry_id] = entry

    return result


def fetch_abilities() -> dict:
    """
    Fetch and parse abilities from Pokemon Showdown.
    Returns dict of ability_id -> ability data with descriptions.
    """
    print("Fetching abilities from Pokemon Showdown...")
    url = f"{SHOWDOWN_DATA_URL}/abilities.js"

    try:
        content = fetch_url(url)
    except Exception as e:
        print(f"Failed to fetch abilities: {e}")
        return {}

    abilities = {}

    # The file is minified - format: abilityid:{name:"...",desc:"...",...},
    # Pattern to extract each ability entry
    pattern = r'(\w+):\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'

    for match in re.finditer(pattern, content):
        ability_id = match.group(1).lower()
        entry_content = match.group(2)

        # Extract name
        name_match = re.search(r'name:"([^"]+)"', entry_content)
        if not name_match:
            continue

        name = name_match.group(1)

        # Extract desc
        desc = ""
        desc_match = re.search(r'desc:"((?:[^"\\]|\\.)*)"', entry_content)
        if desc_match:
            desc = desc_match.group(1).replace('\\"', '"').replace("\\n", " ")

        # Extract shortDesc
        short_desc = ""
        short_match = re.search(r'shortDesc:"((?:[^"\\]|\\.)*)"', entry_content)
        if short_match:
            short_desc = short_match.group(1).replace('\\"', '"').replace("\\n", " ")

        abilities[ability_id] = {
            "id": ability_id,
            "name": name,
            "desc": desc,
            "shortDesc": short_desc or desc,
        }

    print(f"Fetched {len(abilities)} abilities")
    return abilities


def fetch_items() -> dict:
    """
    Fetch and parse items from Pokemon Showdown.
    Returns dict of item_id -> item data with descriptions.
    """
    print("Fetching items from Pokemon Showdown...")
    url = f"{SHOWDOWN_DATA_URL}/items.js"

    try:
        content = fetch_url(url)
    except Exception as e:
        print(f"Failed to fetch items: {e}")
        return {}

    items = {}

    # The file is minified - format: itemid:{name:"...",desc:"...",shortDesc:"...",...},
    # Use same approach as abilities - match individual entries
    pattern = r'(\w+):\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'

    for match in re.finditer(pattern, content):
        item_id = match.group(1).lower()
        entry_content = match.group(2)

        # Extract name
        name_match = re.search(r'name:"([^"]+)"', entry_content)
        if not name_match:
            continue

        name = name_match.group(1)

        # Extract desc
        desc = ""
        desc_match = re.search(r'desc:"((?:[^"\\]|\\.)*)"', entry_content)
        if desc_match:
            desc = desc_match.group(1).replace('\\"', '"').replace("\\n", " ")

        # Extract shortDesc
        short_desc = ""
        short_match = re.search(r'shortDesc:"((?:[^"\\]|\\.)*)"', entry_content)
        if short_match:
            short_desc = short_match.group(1).replace('\\"', '"').replace("\\n", " ")

        items[item_id] = {
            "id": item_id,
            "name": name,
            "desc": desc,
            "shortDesc": short_desc or desc,
        }

    print(f"Fetched {len(items)} items")
    return items


def save_to_cache(data: dict, filename: str) -> None:
    """Save data to cache directory."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    filepath = CACHE_DIR / filename

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(data)} entries to {filepath}")


def fetch_and_cache_all() -> None:
    """Fetch all missing data and save to cache."""
    # Fetch abilities
    abilities = fetch_abilities()
    if abilities:
        save_to_cache(abilities, "abilities_full.json")

    # Fetch items
    items = fetch_items()
    if items:
        save_to_cache(items, "items.json")

    print("\nData fetching complete!")
    print(f"  Abilities: {len(abilities)} entries")
    print(f"  Items: {len(items)} entries")


if __name__ == "__main__":
    fetch_and_cache_all()
