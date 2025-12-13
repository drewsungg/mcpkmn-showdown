"""Tests for the data loader module."""

import pytest
from mcpkmn_showdown.data_loader import PokemonDataLoader, get_loader


class TestPokemonDataLoader:
    """Tests for PokemonDataLoader class."""

    @pytest.fixture
    def loader(self):
        """Create a fresh data loader for each test."""
        return PokemonDataLoader()

    def test_load_all_loads_data(self, loader):
        """Test that load_all populates data dictionaries."""
        loader.load_all()
        assert len(loader.pokemon) > 0
        assert len(loader.moves) > 0
        assert len(loader.abilities) > 0
        assert len(loader.items) > 0
        assert len(loader.typechart) > 0

    def test_load_all_only_loads_once(self, loader):
        """Test that load_all is idempotent."""
        loader.load_all()
        first_pokemon = loader.pokemon
        loader.load_all()
        assert loader.pokemon is first_pokemon

    def test_get_pokemon_basic(self, loader):
        """Test basic Pokemon lookup."""
        poke = loader.get_pokemon("pikachu")
        assert poke is not None
        assert poke["name"] == "Pikachu"
        assert "Electric" in poke["types"]

    def test_get_pokemon_case_insensitive(self, loader):
        """Test Pokemon lookup is case-insensitive."""
        lower = loader.get_pokemon("charizard")
        upper = loader.get_pokemon("CHARIZARD")
        mixed = loader.get_pokemon("ChArIzArD")
        assert lower == upper == mixed

    def test_get_pokemon_not_found(self, loader):
        """Test Pokemon lookup returns None for invalid names."""
        assert loader.get_pokemon("notapokemon") is None

    def test_get_pokemon_mega_form(self, loader):
        """Test Mega form normalization."""
        mega = loader.get_pokemon("Mega Charizard X")
        assert mega is not None
        assert "mega" in mega["name"].lower() or "Mega" in mega.get("baseSpecies", "")

    def test_get_move_basic(self, loader):
        """Test basic move lookup."""
        move = loader.get_move("earthquake")
        assert move is not None
        assert move["name"] == "Earthquake"
        assert move["type"] == "Ground"
        assert move["basePower"] == 100

    def test_get_move_with_spaces(self, loader):
        """Test move lookup handles spaces and dashes."""
        move1 = loader.get_move("swords dance")
        move2 = loader.get_move("swords-dance")
        move3 = loader.get_move("swordsdance")
        assert move1 == move2 == move3
        assert move1 is not None

    def test_get_ability_basic(self, loader):
        """Test basic ability lookup."""
        ability = loader.get_ability("intimidate")
        assert ability is not None
        assert ability["name"] == "Intimidate"
        assert "desc" in ability or "shortDesc" in ability

    def test_get_item_basic(self, loader):
        """Test basic item lookup."""
        item = loader.get_item("choice scarf")
        assert item is not None
        assert item["name"] == "Choice Scarf"

    def test_type_effectiveness_super_effective(self, loader):
        """Test super effective calculation."""
        # Electric vs Water = 2x
        mult = loader.get_type_effectiveness("electric", ["water"])
        assert mult == 2.0

    def test_type_effectiveness_double_super(self, loader):
        """Test double super effective calculation."""
        # Electric vs Water/Flying = 4x
        mult = loader.get_type_effectiveness("electric", ["water", "flying"])
        assert mult == 4.0

    def test_type_effectiveness_immunity(self, loader):
        """Test immunity calculation."""
        # Ground vs Flying = 0x
        mult = loader.get_type_effectiveness("ground", ["flying"])
        assert mult == 0.0

    def test_type_effectiveness_neutral(self, loader):
        """Test neutral effectiveness."""
        # Normal vs Normal = 1x
        mult = loader.get_type_effectiveness("normal", ["normal"])
        assert mult == 1.0

    def test_get_pokemon_with_ability(self, loader):
        """Test finding Pokemon by ability."""
        pokemon = loader.get_pokemon_with_ability("Intimidate")
        assert len(pokemon) > 0
        # Gyarados is a well-known Intimidate user
        assert any("Gyarados" in name for name in pokemon)

    def test_search_moves_by_priority(self, loader):
        """Test searching for priority moves."""
        moves = loader.search_moves_by_priority(min_priority=1)
        assert len(moves) > 0
        # Quick Attack is a priority move
        move_names = [m["name"] for m in moves]
        assert "Quick Attack" in move_names


class TestGlobalLoader:
    """Tests for the global loader singleton."""

    def test_get_loader_returns_same_instance(self):
        """Test that get_loader returns a singleton."""
        loader1 = get_loader()
        loader2 = get_loader()
        assert loader1 is loader2

    def test_get_loader_returns_usable_loader(self):
        """Test that the global loader works."""
        loader = get_loader()
        poke = loader.get_pokemon("bulbasaur")
        assert poke is not None
        assert poke["name"] == "Bulbasaur"


class TestNameNormalization:
    """Tests for Pokemon name normalization edge cases."""

    @pytest.fixture
    def loader(self):
        return PokemonDataLoader()

    def test_normalize_alolan_form(self, loader):
        """Test Alolan form normalization."""
        poke = loader.get_pokemon("Alolan Vulpix")
        assert poke is not None

    def test_normalize_galarian_form(self, loader):
        """Test Galarian form normalization."""
        poke = loader.get_pokemon("Galarian Weezing")
        assert poke is not None

    def test_normalize_mr_mime(self, loader):
        """Test handling of Mr. Mime's period."""
        poke = loader.get_pokemon("Mr. Mime")
        assert poke is not None

    def test_normalize_farfetchd(self, loader):
        """Test handling of Farfetch'd apostrophe."""
        poke = loader.get_pokemon("Farfetch'd")
        assert poke is not None
