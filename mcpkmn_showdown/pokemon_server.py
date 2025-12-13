#!/usr/bin/env python3
"""
Pokemon Data MCP Server

Provides tools for looking up Pokemon, moves, abilities, items, and type effectiveness.
Designed to help LLMs make informed decisions during Pokemon battles.

Tools:
- get_pokemon: Look up Pokemon stats, types, and abilities
- get_move: Look up move details and effects
- get_ability: Look up ability descriptions
- get_item: Look up held item effects
- get_type_effectiveness: Calculate type matchup multipliers
- search_priority_moves: Find all priority moves
- search_pokemon_by_ability: Find Pokemon with a specific ability
"""

import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

try:
    from mcpkmn_showdown.data_loader import get_loader
except ImportError:
    from .data_loader import get_loader


# Create server instance
server = Server("pokemon-data")


def format_pokemon_response(pokemon: dict) -> str:
    """Format Pokemon data into a readable response."""
    name = pokemon.get("name", "Unknown")
    types = pokemon.get("types", [])
    stats = pokemon.get("baseStats", {})
    abilities = pokemon.get("abilities", {})
    weight = pokemon.get("weightkg", 0)
    tier = pokemon.get("tier", "Unknown")

    # Get ability descriptions
    loader = get_loader()
    ability_details = []
    for key, ability_name in abilities.items():
        ability_data = loader.get_ability(ability_name)
        if ability_data:
            desc = ability_data.get("shortDesc") or ability_data.get("desc", "")
            slot = "Hidden" if key == "H" else f"Slot {int(key) + 1}"
            ability_details.append(f"  - {ability_name} ({slot}): {desc}")
        else:
            slot = "Hidden" if key == "H" else f"Slot {int(key) + 1}"
            ability_details.append(f"  - {ability_name} ({slot})")

    response = f"""## {name}

**Types:** {', '.join(types)}
**Tier:** {tier}
**Weight:** {weight}kg

### Base Stats
- HP: {stats.get('hp', '?')}
- Attack: {stats.get('atk', '?')}
- Defense: {stats.get('def', '?')}
- Sp. Attack: {stats.get('spa', '?')}
- Sp. Defense: {stats.get('spd', '?')}
- Speed: {stats.get('spe', '?')}
- **Total:** {sum(stats.values())}

### Abilities
{chr(10).join(ability_details)}
"""
    return response


def format_move_response(move: dict) -> str:
    """Format move data into a readable response."""
    name = move.get("name", "Unknown")
    move_type = move.get("type", "Normal")
    category = move.get("category", "Status")
    power = move.get("basePower", 0)
    accuracy = move.get("accuracy", 100)
    pp = move.get("pp", 0)
    priority = move.get("priority", 0)
    desc = move.get("desc", move.get("shortDesc", "No description."))

    # Handle accuracy = true (never misses)
    if accuracy is True:
        accuracy_str = "Never misses"
    else:
        accuracy_str = f"{accuracy}%"

    priority_str = ""
    if priority > 0:
        priority_str = f"\n**Priority:** +{priority} (moves before normal moves)"
    elif priority < 0:
        priority_str = f"\n**Priority:** {priority} (moves after normal moves)"

    # Secondary effects
    secondary = move.get("secondary")
    secondary_str = ""
    if secondary:
        chance = secondary.get("chance", 100)
        effect = []
        if secondary.get("status"):
            effect.append(f"{secondary['status'].upper()}")
        if secondary.get("boosts"):
            boosts = [f"{k} {v:+d}" for k, v in secondary["boosts"].items()]
            effect.append(f"stat change: {', '.join(boosts)}")
        if secondary.get("volatileStatus"):
            effect.append(secondary["volatileStatus"])
        if effect:
            secondary_str = f"\n**Secondary Effect ({chance}% chance):** {', '.join(effect)}"

    # Self effects
    self_effect = move.get("self", {})
    self_str = ""
    if self_effect.get("boosts"):
        boosts = [f"{k} {v:+d}" for k, v in self_effect["boosts"].items()]
        self_str = f"\n**Self Effect:** {', '.join(boosts)}"

    # Drain/recoil
    drain_str = ""
    if move.get("drain"):
        drain_pct = int(move["drain"][0] / move["drain"][1] * 100)
        drain_str = f"\n**Drain:** Heals {drain_pct}% of damage dealt"
    if move.get("recoil"):
        recoil_pct = int(move["recoil"][0] / move["recoil"][1] * 100)
        drain_str = f"\n**Recoil:** Takes {recoil_pct}% of damage dealt"

    response = f"""## {name}

**Type:** {move_type}
**Category:** {category}
**Power:** {power if power > 0 else '-'}
**Accuracy:** {accuracy_str}
**PP:** {pp}{priority_str}{secondary_str}{self_str}{drain_str}

### Description
{desc}
"""
    return response


def format_ability_response(ability: dict) -> str:
    """Format ability data into a readable response."""
    name = ability.get("name", "Unknown")
    desc = ability.get("desc", ability.get("shortDesc", "No description."))
    short_desc = ability.get("shortDesc", "")

    response = f"""## {name}

### Effect
{desc}
"""
    if short_desc and short_desc != desc:
        response += f"\n### Summary\n{short_desc}\n"

    return response


def format_item_response(item: dict) -> str:
    """Format item data into a readable response."""
    name = item.get("name", "Unknown")
    desc = item.get("desc", item.get("shortDesc", "No description."))
    short_desc = item.get("shortDesc", "")

    response = f"""## {name}

### Effect
{desc}
"""
    if short_desc and short_desc != desc:
        response += f"\n### Summary\n{short_desc}\n"

    return response


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Pokemon data tools."""
    return [
        Tool(
            name="get_pokemon",
            description="Look up a Pokemon by name. Returns base stats, types, abilities with descriptions, weight, and competitive tier.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Pokemon name (e.g., 'pikachu', 'slaking', 'charizard')"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="get_move",
            description="Look up a move by name. Returns power, accuracy, type, category, priority, effects, and full description.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Move name (e.g., 'thunderbolt', 'earthquake', 'swords-dance')"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="get_ability",
            description="Look up an ability by name. Returns full description of what the ability does in battle.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Ability name (e.g., 'truant', 'intimidate', 'levitate')"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="get_item",
            description="Look up a held item by name. Returns full description of what the item does in battle.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Item name (e.g., 'choice-scarf', 'leftovers', 'life-orb')"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="get_type_effectiveness",
            description="Calculate type effectiveness multiplier for an attack against a Pokemon's types.",
            inputSchema={
                "type": "object",
                "properties": {
                    "attack_type": {
                        "type": "string",
                        "description": "The attacking move's type (e.g., 'electric', 'fire')"
                    },
                    "defend_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of the defending Pokemon's types (e.g., ['water', 'flying'])"
                    }
                },
                "required": ["attack_type", "defend_types"]
            }
        ),
        Tool(
            name="search_priority_moves",
            description="Find all moves with priority (moves that go before normal moves). Useful for finding options when you need to outspeed an opponent.",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_priority": {
                        "type": "integer",
                        "description": "Minimum priority value (default 1)",
                        "default": 1
                    }
                }
            }
        ),
        Tool(
            name="search_pokemon_by_ability",
            description="Find all Pokemon that can have a specific ability.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ability": {
                        "type": "string",
                        "description": "Ability name to search for"
                    }
                },
                "required": ["ability"]
            }
        ),
        Tool(
            name="list_dangerous_abilities",
            description="List abilities that can significantly affect battle outcomes (immunities, damage reduction, status reflection, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Category of abilities: 'immunity' (type immunities), 'defense' (damage reduction), 'reflect' (status reflection), 'offense' (damage boosts), 'priority' (move order), 'all' (default)",
                        "default": "all"
                    }
                }
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    loader = get_loader()

    if name == "get_pokemon":
        pokemon = loader.get_pokemon(arguments["name"])
        if pokemon:
            return [TextContent(type="text", text=format_pokemon_response(pokemon))]
        return [TextContent(type="text", text=f"Pokemon '{arguments['name']}' not found.")]

    elif name == "get_move":
        move = loader.get_move(arguments["name"])
        if move:
            return [TextContent(type="text", text=format_move_response(move))]
        return [TextContent(type="text", text=f"Move '{arguments['name']}' not found.")]

    elif name == "get_ability":
        ability = loader.get_ability(arguments["name"])
        if ability:
            return [TextContent(type="text", text=format_ability_response(ability))]
        return [TextContent(type="text", text=f"Ability '{arguments['name']}' not found.")]

    elif name == "get_item":
        item = loader.get_item(arguments["name"])
        if item:
            return [TextContent(type="text", text=format_item_response(item))]
        return [TextContent(type="text", text=f"Item '{arguments['name']}' not found.")]

    elif name == "get_type_effectiveness":
        attack_type = arguments["attack_type"]
        defend_types = arguments["defend_types"]
        multiplier = loader.get_type_effectiveness(attack_type, defend_types)

        # Describe the effectiveness
        if multiplier == 0:
            desc = "No effect (immune)"
        elif multiplier == 0.25:
            desc = "Not very effective (0.25x)"
        elif multiplier == 0.5:
            desc = "Not very effective (0.5x)"
        elif multiplier == 1:
            desc = "Normal effectiveness (1x)"
        elif multiplier == 2:
            desc = "Super effective (2x)"
        elif multiplier == 4:
            desc = "Super effective (4x)"
        else:
            desc = f"{multiplier}x"

        response = f"""## Type Effectiveness

**{attack_type.capitalize()}** vs **{'/'.join(t.capitalize() for t in defend_types)}**

**Multiplier:** {multiplier}x
**Result:** {desc}
"""
        return [TextContent(type="text", text=response)]

    elif name == "search_priority_moves":
        min_priority = arguments.get("min_priority", 1)
        moves = loader.search_moves_by_priority(min_priority)

        if not moves:
            return [TextContent(type="text", text="No priority moves found.")]

        # Sort by priority descending
        moves.sort(key=lambda m: m.get("priority", 0), reverse=True)

        lines = [f"## Priority Moves (priority >= {min_priority})\n"]
        for move in moves[:30]:  # Limit to 30
            priority = move.get("priority", 0)
            power = move.get("basePower", 0)
            move_type = move.get("type", "")
            name = move.get("name", move.get("id", ""))
            lines.append(f"- **{name}** (+{priority}): {move_type}, {power} power")

        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "search_pokemon_by_ability":
        ability = arguments["ability"]
        pokemon_list = loader.get_pokemon_with_ability(ability)

        if not pokemon_list:
            return [TextContent(type="text", text=f"No Pokemon found with ability '{ability}'.")]

        response = f"""## Pokemon with {ability.title()}

Found {len(pokemon_list)} Pokemon:
{', '.join(sorted(pokemon_list)[:50])}
"""
        if len(pokemon_list) > 50:
            response += f"\n... and {len(pokemon_list) - 50} more."

        return [TextContent(type="text", text=response)]

    elif name == "list_dangerous_abilities":
        category = arguments.get("category", "all").lower()

        DANGEROUS_ABILITIES = {
            "immunity": {
                "Levitate": "Immune to Ground moves",
                "Flash Fire": "Immune to Fire moves, boosts own Fire attacks",
                "Volt Absorb": "Immune to Electric, heals instead",
                "Water Absorb": "Immune to Water, heals instead",
                "Dry Skin": "Immune to Water (heals), weak to Fire",
                "Lightning Rod": "Immune to Electric, boosts Sp.Atk",
                "Motor Drive": "Immune to Electric, boosts Speed",
                "Storm Drain": "Immune to Water, boosts Sp.Atk",
                "Sap Sipper": "Immune to Grass, boosts Attack",
                "Earth Eater": "Immune to Ground, heals instead",
                "Wonder Guard": "Only super effective moves deal damage!",
            },
            "defense": {
                "Fur Coat": "Doubles Defense (halves physical damage)",
                "Ice Scales": "Halves Special damage",
                "Fluffy": "Halves contact damage (but 2x Fire damage)",
                "Multiscale": "Halves damage at full HP",
                "Shadow Shield": "Halves damage at full HP",
                "Sturdy": "Survives any hit at full HP with 1 HP",
                "Filter": "Reduces super effective damage by 25%",
                "Solid Rock": "Reduces super effective damage by 25%",
                "Prism Armor": "Reduces super effective damage by 25%",
                "Thick Fat": "Halves Fire and Ice damage",
                "Heatproof": "Halves Fire damage",
                "Water Bubble": "Halves Fire damage, doubles Water attacks",
                "Unaware": "Ignores opponent's stat boosts",
                "Marvel Scale": "1.5x Defense when statused",
            },
            "reflect": {
                "Magic Bounce": "Reflects status moves (Stealth Rock, Thunder Wave, etc.)",
            },
            "offense": {
                "Huge Power": "Doubles Attack stat!",
                "Pure Power": "Doubles Attack stat!",
                "Adaptability": "STAB becomes 2x instead of 1.5x",
                "Technician": "1.5x boost to moves with 60 BP or less",
                "Tinted Lens": "Doubles 'not very effective' damage",
                "Protean": "Changes type to match used move (always STAB)",
                "Libero": "Changes type to match used move (always STAB)",
            },
            "priority": {
                "Prankster": "+1 priority to status moves",
                "Gale Wings": "+1 priority to Flying moves at full HP",
            },
            "contact": {
                "Rough Skin": "1/8 damage to attacker on contact",
                "Iron Barbs": "1/8 damage to attacker on contact",
                "Flame Body": "30% chance to burn on contact",
                "Static": "30% chance to paralyze on contact",
                "Poison Point": "30% chance to poison on contact",
            }
        }

        lines = ["## Dangerous Abilities\n"]
        categories_to_show = [category] if category != "all" else list(DANGEROUS_ABILITIES.keys())

        for cat in categories_to_show:
            if cat in DANGEROUS_ABILITIES:
                lines.append(f"### {cat.title()}\n")
                for ability_name, desc in DANGEROUS_ABILITIES[cat].items():
                    lines.append(f"- **{ability_name}**: {desc}")
                lines.append("")

        if len(lines) == 1:
            return [TextContent(type="text", text=f"Unknown category: {category}. Use 'immunity', 'defense', 'reflect', 'offense', 'priority', 'contact', or 'all'.")]

        return [TextContent(type="text", text="\n".join(lines))]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def _async_main():
    """Async entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Run the MCP server (synchronous entry point)."""
    import asyncio
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
