#!/usr/bin/env python3
"""
Pokemon Data MCP Server

Provides tools for looking up Pokemon, moves, abilities, items, type effectiveness,
competitive usage statistics, and team-building data via Smogon stats.

Tools:
- get_pokemon: Look up Pokemon stats, types, and abilities
- get_move: Look up move details and effects
- get_ability: Look up ability descriptions
- get_item: Look up held item effects
- get_type_effectiveness: Calculate type matchup multipliers
- search_priority_moves: Find all priority moves
- search_pokemon_by_ability: Find Pokemon with a specific ability
- list_dangerous_abilities: List battle-critical abilities
- get_smogon_usage: Top Pokemon by usage in a format
- get_smogon_sets: Competitive sets for a Pokemon
- get_pokemon_counters: What checks/counters a Pokemon
- get_pokemon_teammates: Best teammates for a Pokemon
- search_pokemon_by_stat: Filter Pokemon by base stats
- search_moves_by_effect: Find moves by strategic category
- get_format_info: Format rules and meta characteristics
"""

from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

try:
    from mcpkmn_showdown.data_loader import get_loader
    from mcpkmn_showdown.smogon_stats import get_stats_loader
except ImportError:
    from .data_loader import get_loader
    from .smogon_stats import get_stats_loader


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
        Tool(
            name="get_smogon_usage",
            description="Get the top Pokemon by usage in a competitive format. Shows which Pokemon are most popular and viable.",
            inputSchema={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "description": "Format identifier (e.g., 'gen9ou', 'gen9vgc2025', 'gen9uu', 'gen9ubers', 'gen9doublesou')"
                    },
                    "top_n": {
                        "type": "integer",
                        "description": "Number of top Pokemon to return (default 20)",
                        "default": 20
                    }
                },
                "required": ["format"]
            }
        ),
        Tool(
            name="get_smogon_sets",
            description="Get competitive sets for a Pokemon in a format: common moves, items, abilities, EV spreads, Tera types, and teammates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pokemon": {
                        "type": "string",
                        "description": "Pokemon name (e.g., 'Great Tusk', 'Dragapult')"
                    },
                    "format": {
                        "type": "string",
                        "description": "Format identifier (e.g., 'gen9ou')"
                    }
                },
                "required": ["pokemon", "format"]
            }
        ),
        Tool(
            name="get_pokemon_counters",
            description="Get checks and counters for a Pokemon in a format. Shows what beats it, with KO and switch-out rates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pokemon": {
                        "type": "string",
                        "description": "Pokemon name to find counters for"
                    },
                    "format": {
                        "type": "string",
                        "description": "Format identifier (e.g., 'gen9ou')"
                    }
                },
                "required": ["pokemon", "format"]
            }
        ),
        Tool(
            name="get_pokemon_teammates",
            description="Get the best teammates for a Pokemon based on competitive usage data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pokemon": {
                        "type": "string",
                        "description": "Pokemon name to find teammates for"
                    },
                    "format": {
                        "type": "string",
                        "description": "Format identifier (e.g., 'gen9ou')"
                    }
                },
                "required": ["pokemon", "format"]
            }
        ),
        Tool(
            name="search_pokemon_by_stat",
            description="Find Pokemon filtered by base stat ranges. Useful for finding slow Pokemon for Trick Room, fast sweepers, bulky walls, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "stat": {
                        "type": "string",
                        "description": "Stat to filter by: 'hp', 'atk', 'def', 'spa', 'spd', 'spe'"
                    },
                    "min_value": {
                        "type": "integer",
                        "description": "Minimum base stat value (default 0)",
                        "default": 0
                    },
                    "max_value": {
                        "type": "integer",
                        "description": "Maximum base stat value (default 999)",
                        "default": 999
                    },
                    "types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional type filter (Pokemon must have at least one of these types)"
                    },
                    "tier": {
                        "type": "string",
                        "description": "Optional tier filter (e.g., 'OU', 'UU', 'Uber')"
                    }
                },
                "required": ["stat"]
            }
        ),
        Tool(
            name="search_moves_by_effect",
            description="Find moves by strategic effect category: spread, priority, recovery, setup, hazard, hazard_removal, weather, terrain, screen, pivot, speed_control, redirection, protect.",
            inputSchema={
                "type": "object",
                "properties": {
                    "effect": {
                        "type": "string",
                        "description": "Effect category: 'spread' (multi-target), 'priority', 'recovery', 'setup' (stat boost), 'hazard', 'hazard_removal', 'weather', 'terrain', 'screen', 'pivot' (switch moves), 'speed_control', 'redirection', 'protect'"
                    },
                    "move_type": {
                        "type": "string",
                        "description": "Optional type filter (e.g., 'fire', 'ground')"
                    }
                },
                "required": ["effect"]
            }
        ),
        Tool(
            name="get_format_info",
            description="Get information about a competitive format: rules, common bans, and meta characteristics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "description": "Format name (e.g., 'gen9ou', 'gen9vgc2025', 'gen9uu', 'gen9ubers', 'gen9doublesou')"
                    }
                },
                "required": ["format"]
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

    elif name == "get_smogon_usage":
        format_id = arguments["format"]
        top_n = arguments.get("top_n", 20)
        stats_loader = get_stats_loader()
        top_pokemon = stats_loader.get_top_pokemon(format_id, top_n)

        if not top_pokemon:
            return [TextContent(type="text", text=f"No usage data found for format '{format_id}'. Try formats like 'gen9ou', 'gen9vgc2025', 'gen9uu'.")]

        lines = [f"## Top {len(top_pokemon)} Pokemon in {format_id}\n"]
        for i, poke in enumerate(top_pokemon, 1):
            top_moves = list(poke.moves.keys())[:4]
            moves_str = ", ".join(top_moves) if top_moves else "N/A"
            lines.append(f"{i}. **{poke.name}** (usage count: {poke.raw_count:,})")
            lines.append(f"   Top moves: {moves_str}")

        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "get_smogon_sets":
        pokemon_name = arguments["pokemon"]
        format_id = arguments["format"]
        stats_loader = get_stats_loader()
        poke = stats_loader.get_pokemon(pokemon_name, format_id)

        if poke is None:
            return [TextContent(type="text", text=f"No data found for '{pokemon_name}' in {format_id}.")]

        lines = [f"## {poke.name} — Competitive Data ({format_id})\n"]

        if poke.abilities:
            lines.append("### Abilities")
            for ability, pct in sorted(poke.abilities.items(), key=lambda x: -x[1]):
                lines.append(f"- {ability}: {pct:.1f}%")
            lines.append("")

        if poke.items:
            lines.append("### Items")
            for item, pct in sorted(poke.items.items(), key=lambda x: -x[1]):
                lines.append(f"- {item}: {pct:.1f}%")
            lines.append("")

        if poke.moves:
            lines.append("### Moves")
            for move, pct in sorted(poke.moves.items(), key=lambda x: -x[1]):
                lines.append(f"- {move}: {pct:.1f}%")
            lines.append("")

        if poke.spreads:
            lines.append("### EV Spreads")
            for spread, pct in sorted(poke.spreads.items(), key=lambda x: -x[1])[:5]:
                lines.append(f"- {spread}: {pct:.1f}%")
            lines.append("")

        if poke.tera_types:
            lines.append("### Tera Types")
            for tera, pct in sorted(poke.tera_types.items(), key=lambda x: -x[1]):
                lines.append(f"- {tera}: {pct:.1f}%")
            lines.append("")

        if poke.teammates:
            lines.append("### Common Teammates")
            for teammate, pct in sorted(poke.teammates.items(), key=lambda x: -x[1])[:10]:
                lines.append(f"- {teammate}: {pct:.1f}%")

        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "get_pokemon_counters":
        pokemon_name = arguments["pokemon"]
        format_id = arguments["format"]
        stats_loader = get_stats_loader()
        counters = stats_loader.get_counters(pokemon_name, format_id)

        if not counters:
            return [TextContent(type="text", text=f"No counter data found for '{pokemon_name}' in {format_id}.")]

        lines = [f"## Checks and Counters for {pokemon_name} ({format_id})\n"]
        for counter in counters:
            name_str = counter["name"]
            score = counter.get("score", 0)
            koed = counter.get("koed_pct", 0)
            switched = counter.get("switched_pct", 0)
            lines.append(f"- **{name_str}** (score: {score:.1f})")
            lines.append(f"  KOed {pokemon_name}: {koed:.1f}% | Forced switch: {switched:.1f}%")

        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "get_pokemon_teammates":
        pokemon_name = arguments["pokemon"]
        format_id = arguments["format"]
        stats_loader = get_stats_loader()
        teammates = stats_loader.get_teammates(pokemon_name, format_id)

        if not teammates:
            return [TextContent(type="text", text=f"No teammate data found for '{pokemon_name}' in {format_id}.")]

        lines = [f"## Best Teammates for {pokemon_name} ({format_id})\n"]
        for teammate, pct in sorted(teammates.items(), key=lambda x: -x[1]):
            lines.append(f"- **{teammate}**: {pct:.1f}% co-occurrence")

        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "search_pokemon_by_stat":
        stat = arguments["stat"]
        min_val = arguments.get("min_value", 0)
        max_val = arguments.get("max_value", 999)
        types = arguments.get("types")
        tier = arguments.get("tier")

        results = loader.search_pokemon_by_stat(stat, min_val, max_val, types, tier)

        if not results:
            return [TextContent(type="text", text="No Pokemon found matching the criteria.")]

        # Limit output
        shown = results[:30]
        lines = [f"## Pokemon Search Results ({len(results)} found, showing top {len(shown)})\n"]
        lines.append(f"**Filter:** {stat} between {min_val}-{max_val}")
        if types:
            lines.append(f"**Types:** {', '.join(types)}")
        if tier:
            lines.append(f"**Tier:** {tier}")
        lines.append("")

        for poke in shown:
            stats = poke.get("baseStats", {})
            stat_line = f"HP:{stats.get('hp','?')} Atk:{stats.get('atk','?')} Def:{stats.get('def','?')} SpA:{stats.get('spa','?')} SpD:{stats.get('spd','?')} Spe:{stats.get('spe','?')}"
            types_str = "/".join(poke.get("types", []))
            lines.append(f"- **{poke['name']}** ({types_str}) [{poke.get('tier', '?')}] — {stat_line}")

        if len(results) > 30:
            lines.append(f"\n... and {len(results) - 30} more.")

        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "search_moves_by_effect":
        effect = arguments["effect"]
        move_type = arguments.get("move_type")

        results = loader.search_moves_by_effect(effect, move_type)

        if not results:
            categories = list(loader.MOVE_EFFECT_CATEGORIES.keys())
            return [TextContent(type="text", text=f"No moves found for effect '{effect}'. Available categories: {', '.join(categories)}")]

        lines = [f"## {effect.replace('_', ' ').title()} Moves ({len(results)} found)\n"]
        if move_type:
            lines.append(f"**Type filter:** {move_type}\n")

        for move in results[:30]:
            power = move.get("basePower", 0)
            mtype = move.get("type", "")
            cat = move.get("category", "")
            priority = move.get("priority", 0)
            mname = move.get("name", move.get("id", ""))

            extras = []
            if power > 0:
                extras.append(f"{power} BP")
            if priority > 0:
                extras.append(f"+{priority} priority")
            target = move.get("target", "")
            if target in ("allAdjacentFoes", "allAdjacent"):
                extras.append("spread")

            extra_str = f" ({', '.join(extras)})" if extras else ""
            lines.append(f"- **{mname}** — {mtype} {cat}{extra_str}")

        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "get_format_info":
        format_id = arguments["format"].lower()

        FORMAT_INFO = {
            "gen9ou": {
                "name": "Generation 9 OverUsed (OU)",
                "game": "Scarlet & Violet",
                "type": "Singles (6v6, bring 6 pick 6)",
                "level": 100,
                "clauses": ["Species Clause", "Sleep Clause", "Evasion Clause", "OHKO Clause", "Moody Clause"],
                "key_bans": ["Uber-tier Pokemon (Koraidon, Miraidon, etc.)", "Arena Trap", "Shadow Tag", "Baton Pass"],
                "meta_notes": "The standard competitive singles format. Terastallization available. Heavy emphasis on hazard control, pivoting, and offensive pressure.",
            },
            "gen9uu": {
                "name": "Generation 9 UnderUsed (UU)",
                "game": "Scarlet & Violet",
                "type": "Singles (6v6)",
                "level": 100,
                "clauses": ["Species Clause", "Sleep Clause", "Evasion Clause", "OHKO Clause"],
                "key_bans": ["OU and above Pokemon by usage", "Arena Trap", "Shadow Tag"],
                "meta_notes": "Pokemon that don't see enough play in OU. Often features creative sets and underrated threats.",
            },
            "gen9ubers": {
                "name": "Generation 9 Ubers",
                "game": "Scarlet & Violet",
                "type": "Singles (6v6)",
                "level": 100,
                "clauses": ["Species Clause", "Sleep Clause", "Evasion Clause"],
                "key_bans": ["Mega Rayquaza (AG only)"],
                "meta_notes": "Legendary and mythical Pokemon dominate. Extremely high power level. Koraidon, Miraidon, and Calyrex forms are staples.",
            },
            "gen9vgc2025": {
                "name": "VGC 2025 (Regulation H)",
                "game": "Scarlet & Violet",
                "type": "Doubles (bring 6, pick 4)",
                "level": 50,
                "clauses": ["Species Clause", "Item Clause"],
                "key_bans": ["Restricted legends limited (check current regulation)"],
                "meta_notes": "Official doubles format. Level 50, bring 6 pick 4. Speed control (Tailwind, Trick Room), redirection, Fake Out, and spread moves are critical. Protect is almost mandatory.",
            },
            "gen9doublesou": {
                "name": "Generation 9 Doubles OU",
                "game": "Scarlet & Violet",
                "type": "Doubles (6v6, bring 6 pick 6)",
                "level": 100,
                "clauses": ["Species Clause", "Sleep Clause", "Evasion Clause"],
                "key_bans": ["Uber-tier doubles Pokemon"],
                "meta_notes": "Smogon doubles format. Level 100, bring all 6. More Pokemon variety than VGC. Spread moves, positioning, and speed control are key.",
            },
            "gen9randombattle": {
                "name": "Generation 9 Random Battle",
                "game": "Scarlet & Violet",
                "type": "Singles (random teams)",
                "level": "Varies (scaled by BST)",
                "clauses": ["Random teams assigned"],
                "key_bans": [],
                "meta_notes": "Random teams with pre-built sets. Tests adaptability and game knowledge. Popular for casual play.",
            },
        }

        info = FORMAT_INFO.get(format_id)
        if info is None:
            available = ", ".join(sorted(FORMAT_INFO.keys()))
            return [TextContent(type="text", text=f"Format '{format_id}' not found. Available formats: {available}")]

        lines = [f"## {info['name']}\n"]
        lines.append(f"**Game:** {info['game']}")
        lines.append(f"**Type:** {info['type']}")
        lines.append(f"**Level:** {info['level']}")
        lines.append("")

        if info["clauses"]:
            lines.append("### Clauses")
            for clause in info["clauses"]:
                lines.append(f"- {clause}")
            lines.append("")

        if info["key_bans"]:
            lines.append("### Key Bans")
            for ban in info["key_bans"]:
                lines.append(f"- {ban}")
            lines.append("")

        lines.append("### Meta Notes")
        lines.append(info["meta_notes"])

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
