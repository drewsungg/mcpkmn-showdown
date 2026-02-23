"""
Data accuracy validation tests.

These tests verify that the MCP server returns correct, canonical Pokemon data
rather than hallucinated values. Each test case uses known-correct values from
the official Pokemon games (verified against Bulbapedia/Serebii/Showdown source).

This is the core claim: structured tools beat LLM memory for precise data.
"""

import pytest
from mcpkmn_showdown.data_loader import PokemonDataLoader


@pytest.fixture
def loader():
    """Create a data loader for tests."""
    return PokemonDataLoader()


# ============================================================================
# Pokemon Base Stat Accuracy
# ============================================================================

class TestPokemonBaseStats:
    """
    Verify exact base stats for well-known Pokemon.

    These are the stats LLMs commonly get wrong. Garchomp's base speed (102)
    is the example from the LinkedIn post — models often guess 98, 100, or 105.
    """

    @pytest.fixture
    def loader(self):
        return PokemonDataLoader()

    # Canonical base stats: {pokemon: {stat: value}}
    # Source: Pokemon Showdown / Bulbapedia
    CANONICAL_STATS = {
        "garchomp": {
            "hp": 108, "atk": 130, "def": 95,
            "spa": 80, "spd": 85, "spe": 102,
        },
        "pikachu": {
            "hp": 35, "atk": 55, "def": 40,
            "spa": 50, "spd": 50, "spe": 90,
        },
        "charizard": {
            "hp": 78, "atk": 84, "def": 78,
            "spa": 109, "spd": 85, "spe": 100,
        },
        "mewtwo": {
            "hp": 106, "atk": 110, "def": 90,
            "spa": 154, "spd": 90, "spe": 130,
        },
        "snorlax": {
            "hp": 160, "atk": 110, "def": 65,
            "spa": 65, "spd": 110, "spe": 30,
        },
        "dragonite": {
            "hp": 91, "atk": 134, "def": 95,
            "spa": 100, "spd": 100, "spe": 80,
        },
        "gengar": {
            "hp": 60, "atk": 65, "def": 60,
            "spa": 130, "spd": 75, "spe": 110,
        },
        "tyranitar": {
            "hp": 100, "atk": 134, "def": 110,
            "spa": 95, "spd": 100, "spe": 61,
        },
        "blissey": {
            "hp": 255, "atk": 10, "def": 10,
            "spa": 75, "spd": 135, "spe": 55,
        },
        "scizor": {
            "hp": 70, "atk": 130, "def": 100,
            "spa": 55, "spd": 80, "spe": 65,
        },
        "rotomwash": {
            "hp": 50, "atk": 65, "def": 107,
            "spa": 105, "spd": 107, "spe": 86,
        },
        "ferrothorn": {
            "hp": 74, "atk": 94, "def": 131,
            "spa": 54, "spd": 116, "spe": 20,
        },
    }

    @pytest.mark.parametrize("pokemon_name,expected_stats", list(CANONICAL_STATS.items()))
    def test_base_stats_exact(self, loader, pokemon_name, expected_stats):
        """Verify each Pokemon's base stats are exactly correct."""
        poke = loader.get_pokemon(pokemon_name)
        assert poke is not None, f"{pokemon_name} not found in database"
        stats = poke["baseStats"]
        for stat, expected_val in expected_stats.items():
            assert stats[stat] == expected_val, (
                f"{pokemon_name} {stat}: got {stats[stat]}, expected {expected_val}"
            )


class TestPokemonTypes:
    """Verify Pokemon type assignments are correct."""

    @pytest.fixture
    def loader(self):
        return PokemonDataLoader()

    CANONICAL_TYPES = {
        "garchomp": ["Dragon", "Ground"],
        "pikachu": ["Electric"],
        "charizard": ["Fire", "Flying"],
        "gyarados": ["Water", "Flying"],
        "snorlax": ["Normal"],
        "gengar": ["Ghost", "Poison"],
        "scizor": ["Bug", "Steel"],
        "gardevoir": ["Psychic", "Fairy"],
        "lucario": ["Fighting", "Steel"],
        "mimikyu": ["Ghost", "Fairy"],
        "dragapult": ["Dragon", "Ghost"],
        "toxapex": ["Poison", "Water"],
    }

    @pytest.mark.parametrize("pokemon_name,expected_types", list(CANONICAL_TYPES.items()))
    def test_types_exact(self, loader, pokemon_name, expected_types):
        """Verify each Pokemon's types are exactly correct."""
        poke = loader.get_pokemon(pokemon_name)
        assert poke is not None, f"{pokemon_name} not found"
        assert poke["types"] == expected_types, (
            f"{pokemon_name}: got {poke['types']}, expected {expected_types}"
        )


# ============================================================================
# Type Effectiveness Chart Accuracy
# ============================================================================

class TestTypeChartAccuracy:
    """
    Verify the complete type effectiveness chart is correct.

    This is another area where LLMs frequently hallucinate. The full type chart
    has 18x18 = 324 matchups (plus immunities, double types, etc.).
    """

    @pytest.fixture
    def loader(self):
        return PokemonDataLoader()

    def test_all_18_types_present(self, loader):
        """Verify all 18 standard types exist in the chart."""
        loader.load_all()
        expected_types = {
            "bug", "dark", "dragon", "electric", "fairy", "fighting",
            "fire", "flying", "ghost", "grass", "ground", "ice",
            "normal", "poison", "psychic", "rock", "steel", "water",
        }
        actual_types = set(loader.typechart.keys()) - {"stellar"}
        assert expected_types == actual_types

    # === Immunities (0x) - the most critical to get right ===

    IMMUNITIES = [
        ("normal", ["ghost"], 0.0),
        ("fighting", ["ghost"], 0.0),
        ("ghost", ["normal"], 0.0),
        ("ground", ["flying"], 0.0),
        ("electric", ["ground"], 0.0),
        ("poison", ["steel"], 0.0),
        ("psychic", ["dark"], 0.0),
        ("dragon", ["fairy"], 0.0),
    ]

    @pytest.mark.parametrize("atk,def_types,expected", IMMUNITIES)
    def test_immunities(self, loader, atk, def_types, expected):
        """Verify all type immunities return 0x."""
        result = loader.get_type_effectiveness(atk, def_types)
        assert result == expected, f"{atk} vs {def_types}: got {result}x, expected {expected}x"

    # === Super effective (2x) ===

    SUPER_EFFECTIVE = [
        ("fire", ["grass"], 2.0),
        ("fire", ["ice"], 2.0),
        ("fire", ["bug"], 2.0),
        ("fire", ["steel"], 2.0),
        ("water", ["fire"], 2.0),
        ("water", ["ground"], 2.0),
        ("water", ["rock"], 2.0),
        ("electric", ["water"], 2.0),
        ("electric", ["flying"], 2.0),
        ("grass", ["water"], 2.0),
        ("grass", ["ground"], 2.0),
        ("grass", ["rock"], 2.0),
        ("ice", ["grass"], 2.0),
        ("ice", ["ground"], 2.0),
        ("ice", ["flying"], 2.0),
        ("ice", ["dragon"], 2.0),
        ("fighting", ["normal"], 2.0),
        ("fighting", ["ice"], 2.0),
        ("fighting", ["rock"], 2.0),
        ("fighting", ["dark"], 2.0),
        ("fighting", ["steel"], 2.0),
        ("ground", ["fire"], 2.0),
        ("ground", ["electric"], 2.0),
        ("ground", ["poison"], 2.0),
        ("ground", ["rock"], 2.0),
        ("ground", ["steel"], 2.0),
        ("flying", ["grass"], 2.0),
        ("flying", ["fighting"], 2.0),
        ("flying", ["bug"], 2.0),
        ("psychic", ["fighting"], 2.0),
        ("psychic", ["poison"], 2.0),
        ("bug", ["grass"], 2.0),
        ("bug", ["psychic"], 2.0),
        ("bug", ["dark"], 2.0),
        ("rock", ["fire"], 2.0),
        ("rock", ["ice"], 2.0),
        ("rock", ["flying"], 2.0),
        ("rock", ["bug"], 2.0),
        ("ghost", ["ghost"], 2.0),
        ("ghost", ["psychic"], 2.0),
        ("dragon", ["dragon"], 2.0),
        ("dark", ["ghost"], 2.0),
        ("dark", ["psychic"], 2.0),
        ("steel", ["ice"], 2.0),
        ("steel", ["rock"], 2.0),
        ("steel", ["fairy"], 2.0),
        ("fairy", ["fighting"], 2.0),
        ("fairy", ["dragon"], 2.0),
        ("fairy", ["dark"], 2.0),
        ("poison", ["grass"], 2.0),
        ("poison", ["fairy"], 2.0),
    ]

    @pytest.mark.parametrize("atk,def_types,expected", SUPER_EFFECTIVE)
    def test_super_effective(self, loader, atk, def_types, expected):
        """Verify all super effective matchups return 2x."""
        result = loader.get_type_effectiveness(atk, def_types)
        assert result == expected, f"{atk} vs {def_types}: got {result}x, expected {expected}x"

    # === Double super effective (4x) - dual type weaknesses ===

    DOUBLE_SUPER_EFFECTIVE = [
        ("electric", ["water", "flying"], 4.0),   # Gyarados
        ("ice", ["dragon", "flying"], 4.0),        # Dragonite
        ("rock", ["fire", "flying"], 4.0),         # Charizard
        ("grass", ["water", "ground"], 4.0),       # Swampert
        ("fighting", ["rock", "steel"], 4.0),      # Aggron
        ("ground", ["fire", "steel"], 4.0),        # Heatran (ignoring Flash Fire)
        ("fire", ["grass", "ice"], 4.0),           # Abomasnow
        ("ice", ["grass", "ground"], 4.0),         # Torterra
        ("ground", ["electric", "steel"], 4.0),    # Magnezone
        ("fire", ["grass", "bug"], 4.0),           # Parasect
    ]

    @pytest.mark.parametrize("atk,def_types,expected", DOUBLE_SUPER_EFFECTIVE)
    def test_double_super_effective(self, loader, atk, def_types, expected):
        """Verify 4x weaknesses on dual-typed Pokemon."""
        result = loader.get_type_effectiveness(atk, def_types)
        assert result == expected, f"{atk} vs {def_types}: got {result}x, expected {expected}x"

    # === Not very effective (0.5x) ===

    NOT_VERY_EFFECTIVE = [
        ("fire", ["fire"], 0.5),
        ("fire", ["water"], 0.5),
        ("fire", ["rock"], 0.5),
        ("fire", ["dragon"], 0.5),
        ("water", ["water"], 0.5),
        ("water", ["grass"], 0.5),
        ("water", ["dragon"], 0.5),
        ("electric", ["electric"], 0.5),
        ("electric", ["grass"], 0.5),
        ("electric", ["dragon"], 0.5),
        ("grass", ["fire"], 0.5),
        ("grass", ["grass"], 0.5),
        ("grass", ["poison"], 0.5),
        ("grass", ["flying"], 0.5),
        ("grass", ["bug"], 0.5),
        ("grass", ["dragon"], 0.5),
        ("grass", ["steel"], 0.5),
        ("fighting", ["flying"], 0.5),
        ("fighting", ["psychic"], 0.5),
        ("fighting", ["bug"], 0.5),
        ("fighting", ["fairy"], 0.5),
        ("steel", ["fire"], 0.5),
        ("steel", ["water"], 0.5),
        ("steel", ["electric"], 0.5),
        ("steel", ["steel"], 0.5),
        ("fairy", ["fire"], 0.5),
        ("fairy", ["poison"], 0.5),
        ("fairy", ["steel"], 0.5),
        ("poison", ["poison"], 0.5),
        ("poison", ["ground"], 0.5),
        ("poison", ["rock"], 0.5),
        ("poison", ["ghost"], 0.5),
    ]

    @pytest.mark.parametrize("atk,def_types,expected", NOT_VERY_EFFECTIVE)
    def test_not_very_effective(self, loader, atk, def_types, expected):
        """Verify all not-very-effective matchups return 0.5x."""
        result = loader.get_type_effectiveness(atk, def_types)
        assert result == expected, f"{atk} vs {def_types}: got {result}x, expected {expected}x"

    # === Double resistance (0.25x) ===

    DOUBLE_RESIST = [
        ("fire", ["fire", "water"], 0.25),     # Fire resists Fire, Water resists Fire
        ("grass", ["fire", "flying"], 0.25),   # Charizard double resists Grass
        ("fighting", ["ghost", "fairy"], 0.0), # Immune due to Ghost
        ("bug", ["fire", "flying"], 0.25),     # Both resist Bug
    ]

    @pytest.mark.parametrize("atk,def_types,expected", DOUBLE_RESIST)
    def test_double_resistance(self, loader, atk, def_types, expected):
        """Verify 0.25x resistances on dual types."""
        result = loader.get_type_effectiveness(atk, def_types)
        assert result == expected, f"{atk} vs {def_types}: got {result}x, expected {expected}x"


# ============================================================================
# Move Data Accuracy
# ============================================================================

class TestMoveDataAccuracy:
    """Verify exact move data for well-known competitive moves."""

    @pytest.fixture
    def loader(self):
        return PokemonDataLoader()

    CANONICAL_MOVES = {
        "earthquake": {
            "basePower": 100, "type": "Ground", "category": "Physical",
            "accuracy": 100, "pp": 10,
        },
        "thunderbolt": {
            "basePower": 90, "type": "Electric", "category": "Special",
            "accuracy": 100, "pp": 15,
        },
        "icebeam": {
            "basePower": 90, "type": "Ice", "category": "Special",
            "accuracy": 100, "pp": 10,
        },
        "flamethrower": {
            "basePower": 90, "type": "Fire", "category": "Special",
            "accuracy": 100, "pp": 15,
        },
        "closecombat": {
            "basePower": 120, "type": "Fighting", "category": "Physical",
            "accuracy": 100, "pp": 5,
        },
        "dracometeor": {
            "basePower": 130, "type": "Dragon", "category": "Special",
            "accuracy": 90, "pp": 5,
        },
        "stealthrock": {
            "basePower": 0, "type": "Rock", "category": "Status",
        },
        "swordsdance": {
            "basePower": 0, "type": "Normal", "category": "Status",
        },
        "uturn": {
            "basePower": 70, "type": "Bug", "category": "Physical",
            "accuracy": 100,
        },
        "scald": {
            "basePower": 80, "type": "Water", "category": "Special",
            "accuracy": 100,
        },
        "knockoff": {
            "basePower": 65, "type": "Dark", "category": "Physical",
            "accuracy": 100,
        },
    }

    @pytest.mark.parametrize("move_name,expected", list(CANONICAL_MOVES.items()))
    def test_move_data_exact(self, loader, move_name, expected):
        """Verify each move's data is exactly correct."""
        move = loader.get_move(move_name)
        assert move is not None, f"Move {move_name} not found"
        for field, val in expected.items():
            assert move[field] == val, (
                f"{move_name} {field}: got {move[field]}, expected {val}"
            )


class TestPriorityMoveAccuracy:
    """Verify priority move values are correct."""

    @pytest.fixture
    def loader(self):
        return PokemonDataLoader()

    PRIORITY_MOVES = {
        "extremespeed": 2,
        "aquajet": 1,
        "bulletpunch": 1,
        "machpunch": 1,
        "quickattack": 1,
        "shadowsneak": 1,
        "suckerpunch": 1,
        "iceshard": 1,
        "fakeout": 3,
        "protect": 4,
        "detect": 4,
    }

    @pytest.mark.parametrize("move_name,expected_priority", list(PRIORITY_MOVES.items()))
    def test_priority_values(self, loader, move_name, expected_priority):
        """Verify priority move priority values."""
        move = loader.get_move(move_name)
        assert move is not None, f"Move {move_name} not found"
        assert move["priority"] == expected_priority, (
            f"{move_name}: got priority {move['priority']}, expected {expected_priority}"
        )


# ============================================================================
# Ability Data Accuracy
# ============================================================================

class TestAbilityDataAccuracy:
    """Verify ability lookup returns meaningful descriptions."""

    @pytest.fixture
    def loader(self):
        return PokemonDataLoader()

    ABILITIES_EXIST = [
        "intimidate", "levitate", "flashfire", "drizzle", "drought",
        "sandstream", "snowwarning", "multiscale", "hugepower",
        "protean", "regenerator", "magicguard", "technician",
        "adaptability", "wonderguard", "prankster", "unaware",
        "magicbounce", "moldbreaker", "contrary", "speedboost",
    ]

    @pytest.mark.parametrize("ability_name", ABILITIES_EXIST)
    def test_ability_exists_with_description(self, loader, ability_name):
        """Verify abilities exist and have descriptions."""
        ability = loader.get_ability(ability_name)
        assert ability is not None, f"Ability {ability_name} not found"
        assert ability.get("desc") or ability.get("shortDesc"), (
            f"Ability {ability_name} has no description"
        )
        assert ability.get("name"), f"Ability {ability_name} has no name"


# ============================================================================
# Item Data Accuracy
# ============================================================================

class TestItemDataAccuracy:
    """Verify item lookup returns correct data."""

    @pytest.fixture
    def loader(self):
        return PokemonDataLoader()

    ITEMS_EXIST = [
        "choicescarf", "choiceband", "choicespecs", "leftovers",
        "lifeorb", "focussash", "heavydutyboots", "assaultvest",
        "rockyhelmet", "eviolite", "shedshell",
    ]

    @pytest.mark.parametrize("item_name", ITEMS_EXIST)
    def test_item_exists_with_description(self, loader, item_name):
        """Verify items exist and have descriptions."""
        item = loader.get_item(item_name)
        assert item is not None, f"Item {item_name} not found"
        assert item.get("desc") or item.get("shortDesc"), (
            f"Item {item_name} has no description"
        )


# ============================================================================
# Data Completeness
# ============================================================================

class TestDataCompleteness:
    """Verify the dataset is sufficiently complete for competitive use."""

    @pytest.fixture
    def loader(self):
        loader = PokemonDataLoader()
        loader.load_all()
        return loader

    def test_minimum_pokemon_count(self, loader):
        """Verify we have enough Pokemon (1000+ expected for Gen 9)."""
        assert len(loader.pokemon) >= 1000, (
            f"Only {len(loader.pokemon)} Pokemon loaded, expected 1000+"
        )

    def test_minimum_move_count(self, loader):
        """Verify we have enough moves (900+ expected)."""
        assert len(loader.moves) >= 900, (
            f"Only {len(loader.moves)} moves loaded, expected 900+"
        )

    def test_minimum_ability_count(self, loader):
        """Verify we have enough abilities (300+ expected)."""
        assert len(loader.abilities) >= 300, (
            f"Only {len(loader.abilities)} abilities loaded, expected 300+"
        )

    def test_minimum_item_count(self, loader):
        """Verify we have enough items (500+ expected)."""
        assert len(loader.items) >= 500, (
            f"Only {len(loader.items)} items loaded, expected 500+"
        )

    def test_type_chart_complete(self, loader):
        """Verify all 18 standard types have full type chart data."""
        standard_types = {
            "bug", "dark", "dragon", "electric", "fairy", "fighting",
            "fire", "flying", "ghost", "grass", "ground", "ice",
            "normal", "poison", "psychic", "rock", "steel", "water",
        }
        for type_name in standard_types:
            assert type_name in loader.typechart, f"Type {type_name} missing from chart"
            type_data = loader.typechart[type_name]
            # Each type should have matchup data against all 18 types
            for atk_type in standard_types:
                assert atk_type in type_data, (
                    f"Type chart missing {atk_type} vs {type_name}"
                )

    def test_all_gen9_ou_staples_exist(self, loader):
        """Verify all Gen 9 OU staple Pokemon are in the database."""
        ou_staples = [
            "greattusk", "gholdengo", "dragapult", "kingambit",
            "ironvaliant", "landorustherian", "gliscor", "heatran",
            "toxapex", "ferrothorn", "corviknight", "clefable",
        ]
        for name in ou_staples:
            poke = loader.get_pokemon(name)
            assert poke is not None, f"OU staple {name} not found in database"

    def test_all_pokemon_have_required_fields(self, loader):
        """Verify all non-cosmetic Pokemon entries have the minimum required fields."""
        required_fields = {"name", "types", "baseStats"}
        required_stats = {"hp", "atk", "def", "spa", "spd", "spe"}

        for poke_id, poke_data in loader.pokemon.items():
            # Cosmetic formes (e.g. Burmy-Sandy) inherit data from base species
            if poke_data.get("isCosmeticForme"):
                continue
            for field in required_fields:
                assert field in poke_data, f"{poke_id} missing field '{field}'"
            stats = poke_data.get("baseStats", {})
            for stat in required_stats:
                assert stat in stats, f"{poke_id} missing stat '{stat}'"

    def test_all_moves_have_required_fields(self, loader):
        """Verify all move entries have minimum required fields."""
        for move_id, move_data in loader.moves.items():
            assert "type" in move_data, f"Move {move_id} missing 'type'"
            assert "category" in move_data, f"Move {move_id} missing 'category'"
            assert move_data["category"] in {"Physical", "Special", "Status"}, (
                f"Move {move_id} has invalid category: {move_data['category']}"
            )


# ============================================================================
# Name Normalization Edge Cases
# ============================================================================

class TestNameNormalizationComprehensive:
    """Test that various name formats all resolve correctly."""

    @pytest.fixture
    def loader(self):
        return PokemonDataLoader()

    def test_mega_charizard_x(self, loader):
        poke = loader.get_pokemon("Mega Charizard X")
        assert poke is not None
        assert "Fire" in poke["types"]

    def test_mega_charizard_y(self, loader):
        poke = loader.get_pokemon("Mega Charizard Y")
        assert poke is not None

    def test_alolan_ninetales(self, loader):
        poke = loader.get_pokemon("Alolan Ninetales")
        assert poke is not None
        assert "Ice" in poke["types"]

    def test_galarian_darmanitan(self, loader):
        poke = loader.get_pokemon("Galarian Darmanitan")
        assert poke is not None
        assert "Ice" in poke["types"]

    def test_hisuian_zoroark(self, loader):
        poke = loader.get_pokemon("Hisuian Zoroark")
        assert poke is not None

    def test_mr_mime_with_period(self, loader):
        poke = loader.get_pokemon("Mr. Mime")
        assert poke is not None

    def test_farfetchd_with_apostrophe(self, loader):
        poke = loader.get_pokemon("Farfetch'd")
        assert poke is not None

    def test_move_name_with_spaces(self, loader):
        """Swords Dance should work with any format."""
        m1 = loader.get_move("Swords Dance")
        m2 = loader.get_move("swords dance")
        m3 = loader.get_move("swords-dance")
        m4 = loader.get_move("swordsdance")
        assert m1 == m2 == m3 == m4
        assert m1 is not None

    def test_item_name_with_dashes(self, loader):
        """Choice Scarf should work with any format."""
        i1 = loader.get_item("Choice Scarf")
        i2 = loader.get_item("choice scarf")
        i3 = loader.get_item("choice-scarf")
        i4 = loader.get_item("choicescarf")
        assert i1 == i2 == i3 == i4
        assert i1 is not None

    def test_ability_with_spaces(self, loader):
        """Magic Guard should work with any format."""
        a1 = loader.get_ability("Magic Guard")
        a2 = loader.get_ability("magic guard")
        a3 = loader.get_ability("magicguard")
        assert a1 == a2 == a3
        assert a1 is not None
