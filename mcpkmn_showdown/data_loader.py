"""
Data Loader for Pokemon MCP Server

Loads and indexes Pokemon data from cache files for efficient lookups.
"""

import json
from pathlib import Path
from typing import Any


CACHE_DIR = Path(__file__).parent / "cache"


class PokemonDataLoader:
    """
    Loads and provides access to Pokemon game data.

    Data sources:
    - pokedex.json: Pokemon stats, types, abilities
    - moves_showdown.json: Move data with effects
    - abilities_full.json: Ability descriptions
    - items.json: Item descriptions
    - typechart.json: Type effectiveness
    """

    def __init__(self):
        self.pokemon: dict[str, Any] = {}
        self.moves: dict[str, Any] = {}
        self.abilities: dict[str, Any] = {}
        self.items: dict[str, Any] = {}
        self.typechart: dict[str, Any] = {}
        self._loaded = False

    def load_all(self) -> None:
        """Load all data files."""
        if self._loaded:
            return

        self.pokemon = self._load_json("pokedex.json")
        self.moves = self._load_json("moves_showdown.json")
        self.abilities = self._load_json("abilities_full.json")
        self.items = self._load_json("items.json")
        self.typechart = self._load_json("typechart.json")

        self._loaded = True

    def _load_json(self, filename: str) -> dict:
        """Load a JSON file from cache directory."""
        filepath = CACHE_DIR / filename
        if not filepath.exists():
            print(f"Warning: {filename} not found")
            return {}

        with open(filepath) as f:
            return json.load(f)

    # Prefix -> suffix mapping for Pokemon forms
    FORM_PREFIXES = {
        "mega": "mega",
        "primal": "primal",
        "alolan": "alola",
        "alola": "alola",
        "galarian": "galar",
        "galar": "galar",
        "hisuian": "hisui",
        "hisui": "hisui",
        "paldean": "paldea",
        "paldea": "paldea",
        "gigantamax": "gmax",
        "gmax": "gmax",
        "black": "black",
        "white": "white",
        "origin": "origin",
        "shadow": "shadow",
    }

    def _normalize_pokemon_name(self, name: str) -> str:
        """Normalize Pokemon name, handling forms like 'Mega Charizard Y'."""
        name_lower = name.lower().strip()
        # Remove periods and other punctuation (for Mr. Mime, etc.)
        name_lower = name_lower.replace(".", "").replace("'", "").replace(":", "")
        words = name_lower.replace("-", " ").split()

        if not words:
            return ""

        # Check if first word is a form prefix
        if words[0] in self.FORM_PREFIXES:
            suffix = self.FORM_PREFIXES[words[0]]

            if len(words) == 1:
                return suffix

            pokemon_name = words[1]
            extra_parts = "".join(words[2:]) if len(words) > 2 else ""

            # Special case: "mega X Y" -> "xmegay" (for Charizard/Mewtwo forms)
            if suffix == "mega" and extra_parts and extra_parts in ('x', 'y'):
                return pokemon_name + "mega" + extra_parts

            # Format: pokemon + suffix + extra (e.g., "tauros" + "paldea" + "combat")
            return pokemon_name + suffix + extra_parts

        # Default normalization
        return name_lower.replace(" ", "").replace("-", "")

    def get_pokemon(self, name: str) -> dict | None:
        """
        Get Pokemon data by name.

        Args:
            name: Pokemon name (case-insensitive, handles forms like "Mega Charizard Y")

        Returns:
            Pokemon data dict or None if not found
        """
        self.load_all()
        key = self._normalize_pokemon_name(name)
        return self.pokemon.get(key)

    def _normalize_name(self, name: str) -> str:
        """Basic normalization for moves, abilities, items."""
        return name.lower().replace(" ", "").replace("-", "").replace(".", "").replace("'", "")

    def get_move(self, name: str) -> dict | None:
        """
        Get move data by name.

        Args:
            name: Move name (case-insensitive)

        Returns:
            Move data dict or None if not found
        """
        self.load_all()
        key = self._normalize_name(name)
        return self.moves.get(key)

    def get_ability(self, name: str) -> dict | None:
        """
        Get ability data by name.

        Args:
            name: Ability name (case-insensitive)

        Returns:
            Ability data dict or None if not found
        """
        self.load_all()
        key = self._normalize_name(name)
        return self.abilities.get(key)

    def get_item(self, name: str) -> dict | None:
        """
        Get item data by name.

        Args:
            name: Item name (case-insensitive)

        Returns:
            Item data dict or None if not found
        """
        self.load_all()
        key = self._normalize_name(name)
        return self.items.get(key)

    def get_type_effectiveness(
        self, attack_type: str, defend_types: list[str]
    ) -> float:
        """
        Calculate type effectiveness multiplier.

        Args:
            attack_type: The attacking move's type
            defend_types: List of defending Pokemon's types

        Returns:
            Effectiveness multiplier (0, 0.25, 0.5, 1, 2, 4)
        """
        self.load_all()

        attack_type = attack_type.lower()
        defend_types = [t.lower() for t in defend_types]

        multiplier = 1.0

        # Type chart maps defending type -> attacking type -> multiplier
        for defend_type in defend_types:
            type_data = self.typechart.get(defend_type, {})
            eff = type_data.get(attack_type, 1.0)
            multiplier *= eff

        return multiplier

    def get_pokemon_with_ability(self, ability_name: str) -> list[str]:
        """Find all Pokemon that can have a specific ability."""
        self.load_all()
        ability_lower = ability_name.lower()
        result = []

        for poke_id, poke_data in self.pokemon.items():
            abilities = poke_data.get("abilities", {})
            for ability in abilities.values():
                if ability.lower() == ability_lower:
                    result.append(poke_data.get("name", poke_id))
                    break

        return result

    def search_moves_by_type(self, move_type: str) -> list[dict]:
        """Find all moves of a specific type."""
        self.load_all()
        type_lower = move_type.lower()
        return [
            {"id": k, **v}
            for k, v in self.moves.items()
            if v.get("type", "").lower() == type_lower
        ]

    def search_moves_by_priority(self, min_priority: int = 1) -> list[dict]:
        """Find all priority moves."""
        self.load_all()
        return [
            {"id": k, **v}
            for k, v in self.moves.items()
            if v.get("priority", 0) >= min_priority
        ]

    def search_pokemon_by_stat(
        self,
        stat: str,
        min_value: int = 0,
        max_value: int = 999,
        types: list[str] | None = None,
        tier: str | None = None,
    ) -> list[dict]:
        """
        Search Pokemon by base stat ranges and optional type/tier filters.

        Args:
            stat: Stat name (hp, atk, def, spa, spd, spe)
            min_value: Minimum base stat value
            max_value: Maximum base stat value
            types: Optional list of types to filter by (Pokemon must have at least one)
            tier: Optional tier filter (e.g., "OU", "UU")

        Returns:
            List of matching Pokemon dicts with id and name
        """
        self.load_all()
        stat = stat.lower()
        stat_key_map = {
            "hp": "hp", "atk": "atk", "attack": "atk",
            "def": "def", "defense": "def",
            "spa": "spa", "spatk": "spa", "special_attack": "spa",
            "spd": "spd", "spdef": "spd", "special_defense": "spd",
            "spe": "spe", "speed": "spe",
        }
        stat_key = stat_key_map.get(stat, stat)
        types_lower = [t.lower() for t in types] if types else None

        results = []
        for poke_id, poke_data in self.pokemon.items():
            base_stats = poke_data.get("baseStats", {})
            stat_val = base_stats.get(stat_key, 0)

            if not (min_value <= stat_val <= max_value):
                continue

            if types_lower:
                poke_types = [t.lower() for t in poke_data.get("types", [])]
                if not any(t in poke_types for t in types_lower):
                    continue

            if tier:
                poke_tier = poke_data.get("tier", "").lower()
                if poke_tier != tier.lower():
                    continue

            results.append({
                "id": poke_id,
                "name": poke_data.get("name", poke_id),
                "types": poke_data.get("types", []),
                "tier": poke_data.get("tier", ""),
                stat_key: stat_val,
                "baseStats": base_stats,
            })

        results.sort(key=lambda p: p.get(stat_key, 0), reverse=(stat_key != "spe" or min_value > 50))
        return results

    # Move effect categories for search_moves_by_effect
    MOVE_EFFECT_CATEGORIES: dict[str, dict[str, list[str]]] = {
        "spread": {
            "desc": "Moves that hit multiple targets",
            "flags": [],
            "targets": ["allAdjacentFoes", "allAdjacent", "all"],
        },
        "priority": {
            "desc": "Moves with increased priority",
            "flags": [],
            "targets": [],
        },
        "recovery": {
            "desc": "Moves that restore HP",
            "keywords": ["heal", "recover", "restore", "drain"],
            "moves": [
                "recover", "softboiled", "roost", "moonlight", "morningsun",
                "synthesis", "shoreup", "slackoff", "milkdrink", "wish",
                "healorder", "junglehealing", "lunarblessing", "lifedew",
                "strengthsap",
            ],
        },
        "setup": {
            "desc": "Stat-boosting moves",
            "moves": [
                "swordsdance", "nastyplot", "calmmind", "dragondance",
                "bulkup", "irondefense", "amnesia", "agility", "rockpolish",
                "shellsmash", "quiverdance", "coil", "curse",
                "tailglow", "geomancy", "shiftgear", "tidyup",
                "victorydance", "clangoroussoul", "noretreat",
                "bellydrum", "filletaway",
            ],
        },
        "hazard": {
            "desc": "Entry hazard moves",
            "moves": [
                "stealthrock", "spikes", "toxicspikes", "stickyweb",
                "caltrop",
            ],
        },
        "hazard_removal": {
            "desc": "Moves that remove entry hazards",
            "moves": ["rapidspin", "defog", "courtchange", "tidyup", "mortalspin"],
        },
        "weather": {
            "desc": "Weather-setting moves",
            "moves": [
                "sunnyday", "raindance", "sandstorm", "snowscape", "hail",
            ],
        },
        "terrain": {
            "desc": "Terrain-setting moves",
            "moves": [
                "electricterrain", "grassyterrain", "mistyterrain",
                "psychicterrain",
            ],
        },
        "screen": {
            "desc": "Damage-reducing screens",
            "moves": ["reflect", "lightscreen", "auroraveil"],
        },
        "pivot": {
            "desc": "Moves that switch the user out",
            "moves": [
                "uturn", "voltswitch", "flipturn", "partingshot",
                "batonpass", "teleport", "shedtail", "chillyreception",
            ],
        },
        "speed_control": {
            "desc": "Moves that affect speed order",
            "moves": [
                "tailwind", "trickroom", "icywind", "electroweb",
                "stringshot", "stickyweb", "thunderwave", "glare",
                "bulldoze", "rockslide", "scaryface",
            ],
        },
        "redirection": {
            "desc": "Moves that redirect attacks in doubles",
            "moves": ["followme", "ragepowder", "spotlight", "allyswitch"],
        },
        "protect": {
            "desc": "Protection moves",
            "moves": [
                "protect", "detect", "spikyshield", "kingsshield",
                "banefulbunker", "obstruct", "silktrap", "burningbulwark",
                "wideguard", "quickguard", "matblock",
            ],
        },
    }

    def search_moves_by_effect(
        self, effect: str, move_type: str | None = None
    ) -> list[dict]:
        """
        Search for moves by strategic effect category.

        Args:
            effect: Effect category (spread, priority, recovery, setup, hazard,
                    hazard_removal, weather, terrain, screen, pivot, speed_control,
                    redirection, protect)
            move_type: Optional type filter (e.g., "fire")

        Returns:
            List of matching move dicts
        """
        self.load_all()
        effect = effect.lower().replace(" ", "_")
        category = self.MOVE_EFFECT_CATEGORIES.get(effect)
        if category is None:
            return []

        type_lower = move_type.lower() if move_type else None
        results = []

        # For priority, use the priority field
        if effect == "priority":
            for move_id, move_data in self.moves.items():
                if move_data.get("priority", 0) > 0:
                    if type_lower and move_data.get("type", "").lower() != type_lower:
                        continue
                    results.append({"id": move_id, **move_data})
            results.sort(key=lambda m: m.get("priority", 0), reverse=True)
            return results

        # For spread moves, check target field
        if "targets" in category and category["targets"]:
            for move_id, move_data in self.moves.items():
                target = move_data.get("target", "")
                if target in category["targets"]:
                    if type_lower and move_data.get("type", "").lower() != type_lower:
                        continue
                    results.append({"id": move_id, **move_data})
            results.sort(key=lambda m: m.get("basePower", 0), reverse=True)
            return results

        # For named move lists
        move_ids = set(category.get("moves", []))
        if not move_ids:
            return []

        for move_id, move_data in self.moves.items():
            if move_id in move_ids:
                if type_lower and move_data.get("type", "").lower() != type_lower:
                    continue
                results.append({"id": move_id, **move_data})

        return results


# Global instance
_loader: PokemonDataLoader | None = None


def get_loader() -> PokemonDataLoader:
    """Get the global data loader instance."""
    global _loader
    if _loader is None:
        _loader = PokemonDataLoader()
    return _loader
