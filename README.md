# mcpkmn-showdown

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

A **Model Context Protocol (MCP) server** that provides Pokemon Showdown data to LLMs. Enables AI assistants like Claude to look up Pokemon stats, moves, abilities, items, and type matchups during conversations.

## What is MCP?

[Model Context Protocol](https://modelcontextprotocol.io/) is an open standard that allows AI assistants to securely access external tools and data sources. This server exposes Pokemon game data as MCP tools that Claude and other compatible LLMs can call.

## Features

- **Pokemon Lookup** - Stats, types, abilities for any Pokemon
- **Move Database** - Power, accuracy, effects, priority, descriptions
- **Ability Info** - Full descriptions of what abilities do in battle
- **Item Effects** - Held item descriptions and battle effects
- **Type Calculator** - Calculate type effectiveness multipliers
- **Priority Moves** - Search for moves with priority (Quick Attack, etc.)
- **Ability Search** - Find all Pokemon with a specific ability
- **Dangerous Abilities** - List battle-critical abilities (immunities, etc.)

## Installation

### Option 1: Using uvx (Recommended)

The easiest way to use mcpkmn-showdown is with [uvx](https://docs.astral.sh/uv/):

```bash
uvx mcpkmn-showdown
```

### Option 2: Using pip

```bash
pip install mcpkmn-showdown
```

Then run:
```bash
mcpkmn-showdown
```

### Option 3: From Source

```bash
git clone https://github.com/drewsungg/mcpkmn-showdown.git
cd mcpkmn-showdown
pip install .
mcpkmn-showdown
```

## Usage with Claude Desktop

Add to your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pokemon": {
      "command": "uvx",
      "args": ["mcpkmn-showdown"]
    }
  }
}
```

Or if installed via pip:

```json
{
  "mcpServers": {
    "pokemon": {
      "command": "mcpkmn-showdown"
    }
  }
}
```

Restart Claude Desktop after updating the config.

## Available Tools

### `get_pokemon`
Look up a Pokemon by name. Returns base stats, types, abilities with descriptions, weight, and competitive tier.

```
Input: {"name": "garchomp"}
Output: Pokemon stats, types, abilities, etc.
```

### `get_move`
Look up a move by name. Returns power, accuracy, type, category, priority, effects, and full description.

```
Input: {"name": "earthquake"}
Output: Move details including damage, accuracy, effects
```

### `get_ability`
Look up an ability by name. Returns full description of what the ability does in battle.

```
Input: {"name": "levitate"}
Output: "This Pokemon is immune to Ground-type moves."
```

### `get_item`
Look up a held item by name. Returns full description of what the item does in battle.

```
Input: {"name": "choice-scarf"}
Output: Item effect description
```

### `get_type_effectiveness`
Calculate type effectiveness multiplier for an attack against a Pokemon's types.

```
Input: {"attack_type": "electric", "defend_types": ["water", "flying"]}
Output: "4x - Super effective!"
```

### `search_priority_moves`
Find all moves with priority (moves that go before normal moves).

```
Input: {"min_priority": 1}
Output: List of priority moves (Quick Attack, Mach Punch, etc.)
```

### `search_pokemon_by_ability`
Find all Pokemon that can have a specific ability.

```
Input: {"ability": "levitate"}
Output: List of Pokemon with Levitate
```

### `list_dangerous_abilities`
List abilities that can significantly affect battle outcomes.

```
Input: {"category": "immunity"}
Output: Levitate, Flash Fire, Volt Absorb, etc.
```

## Example Conversations

Once configured, you can ask Claude things like:

- *"What are Garchomp's stats and abilities?"*
- *"Is Earthquake effective against Rotom-Wash?"*
- *"What does the ability Protean do?"*
- *"What priority moves can hit Ghost types?"*
- *"Which Pokemon have the ability Intimidate?"*

## Data Sources

Pokemon data is sourced from [Pokemon Showdown](https://pokemonshowdown.com/), the popular competitive Pokemon battle simulator. Data includes:

- `pokedex.json` - Pokemon stats, types, abilities
- `moves_showdown.json` - Move data with effects
- `abilities_full.json` - Ability descriptions
- `items.json` - Item descriptions
- `typechart.json` - Type effectiveness chart

## Development

### Running Locally

```bash
git clone https://github.com/drewsungg/mcpkmn-showdown.git
cd mcpkmn-showdown
pip install -e ".[dev]"
python -m src.pokemon_server
```

### Updating Pokemon Data

The cache data can be refreshed using the data fetcher:

```bash
python -m src.data_fetcher
```

## Related Projects

- [pokemon-llm-battle-bot](https://github.com/drewsungg/pokemon-llm-battle-bot) - An LLM-powered Pokemon battle bot that uses this MCP server
- [Pokemon Showdown](https://pokemonshowdown.com/) - The source of Pokemon data
- [Model Context Protocol](https://modelcontextprotocol.io/) - The protocol specification

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

**Andrew Sung** - [@drewsungg](https://github.com/drewsungg)
