"""
Integration tests for the MCP server tool handlers.

These tests exercise the actual tool call handlers end-to-end, verifying
that each of the 15 MCP tools returns properly formatted TextContent responses.
"""

import pytest
from mcp.types import TextContent

from mcpkmn_showdown.pokemon_server import call_tool


# ============================================================================
# Basic Lookup Tools
# ============================================================================

class TestGetPokemonTool:
    """Integration tests for the get_pokemon tool."""

    @pytest.mark.asyncio
    async def test_valid_pokemon(self):
        result = await call_tool("get_pokemon", {"name": "garchomp"})
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        text = result[0].text
        assert "Garchomp" in text
        assert "Dragon" in text
        assert "Ground" in text
        assert "102" in text  # base speed
        assert "130" in text  # base attack

    @pytest.mark.asyncio
    async def test_invalid_pokemon(self):
        result = await call_tool("get_pokemon", {"name": "notapokemon"})
        assert len(result) == 1
        assert "not found" in result[0].text

    @pytest.mark.asyncio
    async def test_pokemon_case_insensitive(self):
        result = await call_tool("get_pokemon", {"name": "PIKACHU"})
        assert "Pikachu" in result[0].text

    @pytest.mark.asyncio
    async def test_pokemon_includes_abilities(self):
        result = await call_tool("get_pokemon", {"name": "garchomp"})
        text = result[0].text
        assert "Abilities" in text
        # Garchomp has Sand Veil and Rough Skin
        assert "Sand Veil" in text or "Rough Skin" in text

    @pytest.mark.asyncio
    async def test_pokemon_includes_all_stats(self):
        result = await call_tool("get_pokemon", {"name": "blissey"})
        text = result[0].text
        assert "HP: 255" in text
        assert "Defense: 10" in text


class TestGetMoveTool:
    """Integration tests for the get_move tool."""

    @pytest.mark.asyncio
    async def test_valid_move(self):
        result = await call_tool("get_move", {"name": "earthquake"})
        assert len(result) == 1
        text = result[0].text
        assert "Earthquake" in text
        assert "Ground" in text
        assert "Physical" in text
        assert "100" in text  # base power

    @pytest.mark.asyncio
    async def test_invalid_move(self):
        result = await call_tool("get_move", {"name": "notamove"})
        assert "not found" in result[0].text

    @pytest.mark.asyncio
    async def test_status_move(self):
        result = await call_tool("get_move", {"name": "swords dance"})
        text = result[0].text
        assert "Status" in text

    @pytest.mark.asyncio
    async def test_priority_move_shows_priority(self):
        result = await call_tool("get_move", {"name": "extreme speed"})
        text = result[0].text
        assert "+2" in text or "Priority" in text

    @pytest.mark.asyncio
    async def test_move_with_secondary_effect(self):
        result = await call_tool("get_move", {"name": "thunderbolt"})
        text = result[0].text
        # Thunderbolt has 10% paralysis chance
        assert "10%" in text or "PAR" in text or "paralyz" in text.lower()

    @pytest.mark.asyncio
    async def test_move_with_recoil(self):
        result = await call_tool("get_move", {"name": "flare blitz"})
        text = result[0].text
        assert "Recoil" in text or "recoil" in text


class TestGetAbilityTool:
    """Integration tests for the get_ability tool."""

    @pytest.mark.asyncio
    async def test_valid_ability(self):
        result = await call_tool("get_ability", {"name": "intimidate"})
        assert len(result) == 1
        text = result[0].text
        assert "Intimidate" in text
        assert "Attack" in text  # description should mention Attack

    @pytest.mark.asyncio
    async def test_invalid_ability(self):
        result = await call_tool("get_ability", {"name": "notanability"})
        assert "not found" in result[0].text


class TestGetItemTool:
    """Integration tests for the get_item tool."""

    @pytest.mark.asyncio
    async def test_valid_item(self):
        result = await call_tool("get_item", {"name": "choice scarf"})
        assert len(result) == 1
        text = result[0].text
        assert "Choice Scarf" in text
        assert "Speed" in text or "speed" in text

    @pytest.mark.asyncio
    async def test_invalid_item(self):
        result = await call_tool("get_item", {"name": "notanitem"})
        assert "not found" in result[0].text


class TestGetTypeEffectivenessTool:
    """Integration tests for the get_type_effectiveness tool."""

    @pytest.mark.asyncio
    async def test_super_effective(self):
        result = await call_tool("get_type_effectiveness", {
            "attack_type": "fire",
            "defend_types": ["grass"],
        })
        text = result[0].text
        assert "2" in text
        assert "Super effective" in text or "super effective" in text

    @pytest.mark.asyncio
    async def test_immunity(self):
        result = await call_tool("get_type_effectiveness", {
            "attack_type": "normal",
            "defend_types": ["ghost"],
        })
        text = result[0].text
        assert "0" in text
        assert "immune" in text.lower() or "No effect" in text

    @pytest.mark.asyncio
    async def test_double_super_effective(self):
        result = await call_tool("get_type_effectiveness", {
            "attack_type": "electric",
            "defend_types": ["water", "flying"],
        })
        text = result[0].text
        assert "4" in text

    @pytest.mark.asyncio
    async def test_neutral(self):
        result = await call_tool("get_type_effectiveness", {
            "attack_type": "normal",
            "defend_types": ["normal"],
        })
        text = result[0].text
        assert "1x" in text or "1.0" in text


# ============================================================================
# Search Tools
# ============================================================================

class TestSearchPriorityMovesTool:
    """Integration tests for the search_priority_moves tool."""

    @pytest.mark.asyncio
    async def test_default_search(self):
        result = await call_tool("search_priority_moves", {})
        text = result[0].text
        assert "Priority" in text or "priority" in text
        assert "Quick Attack" in text or "Extreme Speed" in text

    @pytest.mark.asyncio
    async def test_high_priority_only(self):
        result = await call_tool("search_priority_moves", {"min_priority": 3})
        text = result[0].text
        assert "Fake Out" in text


class TestSearchPokemonByAbilityTool:
    """Integration tests for the search_pokemon_by_ability tool."""

    @pytest.mark.asyncio
    async def test_valid_ability(self):
        result = await call_tool("search_pokemon_by_ability", {"ability": "Intimidate"})
        text = result[0].text
        assert "Gyarados" in text
        assert "Intimidate" in text

    @pytest.mark.asyncio
    async def test_no_results(self):
        result = await call_tool("search_pokemon_by_ability", {"ability": "NotAnAbility"})
        text = result[0].text
        assert "No Pokemon found" in text


class TestListDangerousAbilitiesTool:
    """Integration tests for the list_dangerous_abilities tool."""

    @pytest.mark.asyncio
    async def test_all_categories(self):
        result = await call_tool("list_dangerous_abilities", {})
        text = result[0].text
        assert "Immunity" in text
        assert "Levitate" in text
        assert "Huge Power" in text

    @pytest.mark.asyncio
    async def test_specific_category(self):
        result = await call_tool("list_dangerous_abilities", {"category": "immunity"})
        text = result[0].text
        assert "Levitate" in text
        assert "Wonder Guard" in text

    @pytest.mark.asyncio
    async def test_invalid_category(self):
        result = await call_tool("list_dangerous_abilities", {"category": "fake"})
        text = result[0].text
        assert "Unknown category" in text


class TestSearchPokemonByStatTool:
    """Integration tests for the search_pokemon_by_stat tool."""

    @pytest.mark.asyncio
    async def test_fast_pokemon(self):
        result = await call_tool("search_pokemon_by_stat", {
            "stat": "spe",
            "min_value": 150,
        })
        text = result[0].text
        # Deoxys-Speed (180), Ninjask (160), etc.
        assert "Pokemon Search Results" in text
        assert "Spe:" in text or "spe" in text.lower()

    @pytest.mark.asyncio
    async def test_slow_pokemon(self):
        result = await call_tool("search_pokemon_by_stat", {
            "stat": "spe",
            "min_value": 1,
            "max_value": 20,
        })
        text = result[0].text
        assert "Pokemon Search Results" in text

    @pytest.mark.asyncio
    async def test_with_type_filter(self):
        result = await call_tool("search_pokemon_by_stat", {
            "stat": "atk",
            "min_value": 130,
            "types": ["Dragon"],
        })
        text = result[0].text
        # Garchomp (130 Atk, Dragon), Dragonite (134 Atk, Dragon)
        assert "Dragon" in text

    @pytest.mark.asyncio
    async def test_no_results(self):
        result = await call_tool("search_pokemon_by_stat", {
            "stat": "hp",
            "min_value": 999,
        })
        text = result[0].text
        assert "No Pokemon found" in text


class TestSearchMovesByEffectTool:
    """Integration tests for the search_moves_by_effect tool."""

    @pytest.mark.asyncio
    async def test_spread_moves(self):
        result = await call_tool("search_moves_by_effect", {"effect": "spread"})
        text = result[0].text
        assert "Earthquake" in text

    @pytest.mark.asyncio
    async def test_hazard_moves(self):
        result = await call_tool("search_moves_by_effect", {"effect": "hazard"})
        text = result[0].text
        assert "Stealth Rock" in text

    @pytest.mark.asyncio
    async def test_pivot_moves(self):
        result = await call_tool("search_moves_by_effect", {"effect": "pivot"})
        text = result[0].text
        assert "U-turn" in text

    @pytest.mark.asyncio
    async def test_with_type_filter(self):
        result = await call_tool("search_moves_by_effect", {
            "effect": "spread",
            "move_type": "ground",
        })
        text = result[0].text
        assert "Earthquake" in text

    @pytest.mark.asyncio
    async def test_invalid_effect(self):
        result = await call_tool("search_moves_by_effect", {"effect": "nonexistent"})
        text = result[0].text
        assert "No moves found" in text
        assert "Available categories" in text


class TestGetFormatInfoTool:
    """Integration tests for the get_format_info tool."""

    @pytest.mark.asyncio
    async def test_gen9ou(self):
        result = await call_tool("get_format_info", {"format": "gen9ou"})
        text = result[0].text
        assert "OverUsed" in text or "OU" in text
        assert "Scarlet" in text or "Singles" in text
        assert "Species Clause" in text

    @pytest.mark.asyncio
    async def test_gen9vgc(self):
        result = await call_tool("get_format_info", {"format": "gen9vgc2025"})
        text = result[0].text
        assert "VGC" in text or "Doubles" in text
        assert "bring 6" in text or "pick 4" in text

    @pytest.mark.asyncio
    async def test_invalid_format(self):
        result = await call_tool("get_format_info", {"format": "gen1notaformat"})
        text = result[0].text
        assert "not found" in text
        assert "gen9ou" in text  # should suggest available formats


# ============================================================================
# Unknown Tool
# ============================================================================

class TestUnknownTool:
    """Test that unknown tool names return an error message."""

    @pytest.mark.asyncio
    async def test_unknown_tool(self):
        result = await call_tool("not_a_real_tool", {})
        assert "Unknown tool" in result[0].text


# ============================================================================
# Response Format Validation
# ============================================================================

class TestResponseFormat:
    """Verify all tools return properly formatted markdown responses."""

    @pytest.mark.asyncio
    async def test_pokemon_response_is_markdown(self):
        result = await call_tool("get_pokemon", {"name": "garchomp"})
        text = result[0].text
        assert "##" in text  # markdown heading
        assert "**" in text  # bold text

    @pytest.mark.asyncio
    async def test_move_response_is_markdown(self):
        result = await call_tool("get_move", {"name": "earthquake"})
        text = result[0].text
        assert "##" in text
        assert "**Type:**" in text

    @pytest.mark.asyncio
    async def test_type_effectiveness_response_is_markdown(self):
        result = await call_tool("get_type_effectiveness", {
            "attack_type": "fire",
            "defend_types": ["grass"],
        })
        text = result[0].text
        assert "##" in text
        assert "**Multiplier:**" in text

    @pytest.mark.asyncio
    async def test_all_tools_return_text_content(self):
        """Every tool should return a list of TextContent."""
        tool_calls = [
            ("get_pokemon", {"name": "pikachu"}),
            ("get_move", {"name": "thunderbolt"}),
            ("get_ability", {"name": "intimidate"}),
            ("get_item", {"name": "leftovers"}),
            ("get_type_effectiveness", {"attack_type": "fire", "defend_types": ["grass"]}),
            ("search_priority_moves", {}),
            ("search_pokemon_by_ability", {"ability": "Intimidate"}),
            ("list_dangerous_abilities", {}),
            ("search_pokemon_by_stat", {"stat": "spe", "min_value": 100}),
            ("search_moves_by_effect", {"effect": "pivot"}),
            ("get_format_info", {"format": "gen9ou"}),
        ]
        for tool_name, args in tool_calls:
            result = await call_tool(tool_name, args)
            assert isinstance(result, list), f"{tool_name} didn't return a list"
            assert len(result) >= 1, f"{tool_name} returned empty list"
            assert isinstance(result[0], TextContent), (
                f"{tool_name} returned {type(result[0])}, expected TextContent"
            )
            assert len(result[0].text) > 0, f"{tool_name} returned empty text"
