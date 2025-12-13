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


# Global instance
_loader: PokemonDataLoader | None = None


def get_loader() -> PokemonDataLoader:
    """Get the global data loader instance."""
    global _loader
    if _loader is None:
        _loader = PokemonDataLoader()
    return _loader
