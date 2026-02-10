"""Tests for the Smogon stats fetcher and parser."""

import pytest
from mcpkmn_showdown.smogon_stats import (
    PokemonUsageData,
    SmogonStatsLoader,
    _parse_pokemon_block,
    _parse_section_entries,
    _parse_checks_and_counters,
    _parse_stats,
)


SAMPLE_BLOCK = """
 +----------------------------------------+
 | Great Tusk                             |
 +----------------------------------------+
 | Raw count: 619002                      |
 | Avg. weight: 0.005443082201569342      |
 | Viability Ceiling: 91                  |
 +----------------------------------------+
 | Abilities                              |
 | Protosynthesis 100.000%                |
 +----------------------------------------+
 | Items                                  |
 | Heavy-Duty Boots 37.651%               |
 | Rocky Helmet 23.292%                   |
 | Other  3.941%                          |
 +----------------------------------------+
 | Spreads                                |
 | Jolly:0/252/0/0/4/252 37.138%          |
 | Other 23.132%                          |
 +----------------------------------------+
 | Moves                                  |
 | Rapid Spin 97.451%                     |
 | Headlong Rush 94.923%                  |
 | Ice Spinner 91.711%                    |
 | Other 19.314%                          |
 +----------------------------------------+
 | Tera Types                             |
 | Ice 24.192%                            |
 | Steel 21.234%                          |
 | Other  4.140%                          |
 +----------------------------------------+
 | Teammates                              |
 | Ogerpon-Wellspring 33.300%             |
 | Darkrai 24.346%                        |
 +----------------------------------------+
 | Checks and Counters                    |
 | Ogerpon-Wellspring 54.493 (78.40±5.98) |
 |   (23.2% KOed / 55.2% switched out)   |
 | Skarmory 50.035 (83.31±8.32)           |
 |   (12.1% KOed / 71.2% switched out)   |
 +----------------------------------------+
"""


class TestParseSectionEntries:
    def test_parse_items(self):
        lines = [
            " | Heavy-Duty Boots 37.651%               |",
            " | Rocky Helmet 23.292%                   |",
            " | Other  3.941%                          |",
        ]
        result = _parse_section_entries(lines)
        assert "Heavy-Duty Boots" in result
        assert abs(result["Heavy-Duty Boots"] - 37.651) < 0.01
        assert "Rocky Helmet" in result
        assert "Other" not in result  # "Other" should be excluded

    def test_parse_abilities(self):
        lines = [" | Protosynthesis 100.000%                |"]
        result = _parse_section_entries(lines)
        assert "Protosynthesis" in result
        assert abs(result["Protosynthesis"] - 100.0) < 0.01

    def test_parse_moves(self):
        lines = [
            " | Rapid Spin 97.451%                     |",
            " | Headlong Rush 94.923%                  |",
        ]
        result = _parse_section_entries(lines)
        assert len(result) == 2
        assert "Rapid Spin" in result


class TestParseChecksAndCounters:
    def test_parse_counters(self):
        lines = [
            " | Ogerpon-Wellspring 54.493 (78.40±5.98) |",
            " |   (23.2% KOed / 55.2% switched out)   |",
            " | Skarmory 50.035 (83.31±8.32)           |",
            " |   (12.1% KOed / 71.2% switched out)   |",
        ]
        result = _parse_checks_and_counters(lines)
        assert len(result) == 2
        assert result[0]["name"] == "Ogerpon-Wellspring"
        assert abs(result[0]["score"] - 54.493) < 0.01
        assert abs(result[0]["koed_pct"] - 23.2) < 0.1
        assert abs(result[0]["switched_pct"] - 55.2) < 0.1
        assert result[1]["name"] == "Skarmory"


class TestParsePokemonBlock:
    def test_parse_full_block(self):
        result = _parse_pokemon_block(SAMPLE_BLOCK)
        assert result is not None
        assert result.name == "Great Tusk"
        assert result.raw_count == 619002
        assert result.viability_ceiling == 91

    def test_parse_abilities(self):
        result = _parse_pokemon_block(SAMPLE_BLOCK)
        assert "Protosynthesis" in result.abilities
        assert abs(result.abilities["Protosynthesis"] - 100.0) < 0.01

    def test_parse_items(self):
        result = _parse_pokemon_block(SAMPLE_BLOCK)
        assert "Heavy-Duty Boots" in result.items
        assert "Rocky Helmet" in result.items

    def test_parse_moves(self):
        result = _parse_pokemon_block(SAMPLE_BLOCK)
        assert "Rapid Spin" in result.moves
        assert "Headlong Rush" in result.moves
        assert "Ice Spinner" in result.moves

    def test_parse_tera_types(self):
        result = _parse_pokemon_block(SAMPLE_BLOCK)
        assert "Ice" in result.tera_types
        assert "Steel" in result.tera_types

    def test_parse_teammates(self):
        result = _parse_pokemon_block(SAMPLE_BLOCK)
        assert "Ogerpon-Wellspring" in result.teammates
        assert "Darkrai" in result.teammates

    def test_parse_checks_and_counters(self):
        result = _parse_pokemon_block(SAMPLE_BLOCK)
        assert len(result.checks_and_counters) == 2
        assert result.checks_and_counters[0]["name"] == "Ogerpon-Wellspring"

    def test_parse_empty_block_returns_none(self):
        result = _parse_pokemon_block("")
        assert result is None


class TestParseStats:
    def test_parse_multiple_blocks(self):
        # Create a mini stats file with two Pokemon
        text = SAMPLE_BLOCK + """
 +----------------------------------------+
 | Darkrai                                |
 +----------------------------------------+
 | Raw count: 500000                      |
 | Avg. weight: 0.004                     |
 | Viability Ceiling: 89                  |
 +----------------------------------------+
 | Abilities                              |
 | Bad Dreams 100.000%                    |
 +----------------------------------------+
 | Items                                  |
 | Focus Sash 50.000%                     |
 +----------------------------------------+
 | Spreads                                |
 | Timid:0/0/0/252/4/252 60.000%          |
 +----------------------------------------+
 | Moves                                  |
 | Dark Void 95.000%                      |
 | Dark Pulse 90.000%                     |
 +----------------------------------------+
 | Tera Types                             |
 | Dark 40.000%                           |
 +----------------------------------------+
 | Teammates                              |
 | Great Tusk 30.000%                     |
 +----------------------------------------+
 | Checks and Counters                    |
 +----------------------------------------+
"""
        result = _parse_stats(text)
        assert len(result) >= 2
        assert "greattusk" in result
        assert "darkrai" in result
        assert result["darkrai"].name == "Darkrai"
        assert result["darkrai"].raw_count == 500000


class TestSmogonStatsLoader:
    def test_loader_init(self):
        loader = SmogonStatsLoader()
        assert loader._cache == {}

    def test_get_pokemon_not_found(self):
        loader = SmogonStatsLoader()
        # With empty cache, should return None
        result = loader.get_pokemon("notapokemon", "gen9ou")
        assert result is None
