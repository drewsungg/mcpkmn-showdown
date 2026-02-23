# mcpkmn-showdown

[![PyPI version](https://badge.fury.io/py/mcpkmn-showdown.svg)](https://pypi.org/project/mcpkmn-showdown/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

**An MCP server that gives AI assistants complete knowledge of competitive Pokemon.**

Give Claude (or any MCP-compatible LLM) instant access to Pokemon stats, moves, abilities, items, and type matchups—no API keys, no rate limits, works offline.

![Claude Desktop using mcpkmn-showdown](https://raw.githubusercontent.com/drewsungg/mcpkmn-showdown/main/content/claude_desktop.png)

---

## Why This Exists

Without this MCP server, getting accurate Pokemon battle data into an LLM is painful:

- **Hallucination city** — LLMs frequently make up stats, forget abilities, or miscalculate type matchups
- **No structured data** — You're stuck copy-pasting from Bulbapedia or Serebii
- **Can't build agents** — No programmatic way for an AI to query battle mechanics

With mcpkmn-showdown:

- **Zero hallucination** — Data comes directly from [Pokemon Showdown](https://pokemonshowdown.com/), the competitive standard
- **Structured responses** — Tools return formatted data ready for reasoning
- **Agent-ready** — Build bots that analyze replays, suggest teams, or play battles

---

## Quickstart (5 minutes)

### 1. Install

```bash
pip install mcpkmn-showdown
```

### 2. Configure Claude Desktop

Add to your config file:

| OS      | Path                                                              |
| ------- | ----------------------------------------------------------------- |
| macOS   | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json`                     |

```json
{
  "mcpServers": {
    "pokemon": {
      "command": "mcpkmn-showdown"
    }
  }
}
```

### 3. Restart Claude Desktop

### 4. Try it

Ask Claude: _"What's the best ability for Garchomp and why?"_

---

## What You Can Do

Here are concrete workflows this MCP enables:

| Workflow            | Example Prompt                                                |
| ------------------- | ------------------------------------------------------------- |
| **Team Analysis**   | "Analyze this team's type coverage and suggest improvements"  |
| **Matchup Calc**    | "Is Choice Scarf Garchomp fast enough to outspeed Dragapult?" |
| **Set Building**    | "Build a Trick Room sweeper that can handle Fairy types"      |
| **Replay Analysis** | "What went wrong in this battle? [paste replay log]"          |
| **Learning**        | "Explain how Intimidate affects damage calculations"          |

---

## API Reference

### Tools Overview

| Tool                        | Purpose                               | Key Input                     |
| --------------------------- | ------------------------------------- | ----------------------------- |
| `get_pokemon`               | Pokemon stats, types, abilities       | `name: string`                |
| `get_move`                  | Move power, accuracy, effects         | `name: string`                |
| `get_ability`               | What an ability does in battle        | `name: string`                |
| `get_item`                  | Held item effects                     | `name: string`                |
| `get_type_effectiveness`    | Damage multiplier calculation         | `attack_type`, `defend_types` |
| `search_priority_moves`     | Find priority moves                   | `min_priority: int`           |
| `search_pokemon_by_ability` | Pokemon with a specific ability       | `ability: string`             |
| `list_dangerous_abilities`  | Battle-critical abilities by category | `category: string`            |

---

### `get_pokemon`

Look up complete Pokemon data.

**Schema:**

```json
{
  "name": "string" // Pokemon name (e.g., "garchomp", "Mega Charizard X")
}
```

**Example:**

```
Input:  {"name": "garchomp"}
Output:
  Garchomp
  Types: Ground/Dragon
  Stats: HP 108 | Atk 130 | Def 95 | SpA 80 | SpD 85 | Spe 102
  Abilities: Sand Veil / Rough Skin (Hidden)
  Weight: 95 kg
  Tier: OU
```

---

### `get_move`

Look up move details including effects and priority.

**Schema:**

```json
{
  "name": "string" // Move name (e.g., "earthquake", "swords-dance")
}
```

**Example:**

```
Input:  {"name": "earthquake"}
Output:
  Earthquake
  Type: Ground | Category: Physical
  Power: 100 | Accuracy: 100%
  PP: 10 | Priority: 0
  Effect: Hits all adjacent Pokemon. Double damage on Dig.
```

---

### `get_ability`

Look up what an ability does in battle.

**Schema:**

```json
{
  "name": "string" // Ability name (e.g., "levitate", "protean")
}
```

**Example:**

```
Input:  {"name": "protean"}
Output:
  Protean: This Pokemon's type changes to match the type of the move
  it is about to use. This effect comes after all effects that change
  a move's type.
```

---

### `get_item`

Look up held item battle effects.

**Schema:**

```json
{
  "name": "string" // Item name (e.g., "choice-scarf", "leftovers")
}
```

**Example:**

```
Input:  {"name": "choice-scarf"}
Output:
  Choice Scarf: Holder's Speed is 1.5x, but it can only use the first
  move it selects.
```

---

### `get_type_effectiveness`

Calculate type matchup multipliers.

**Schema:**

```json
{
  "attack_type": "string", // Attacking type (e.g., "electric")
  "defend_types": ["string"] // Defending types (e.g., ["water", "flying"])
}
```

**Example:**

```
Input:  {"attack_type": "electric", "defend_types": ["water", "flying"]}
Output: 4x - Super effective!
```

---

### `search_priority_moves`

Find moves that act before normal speed order.

**Schema:**

```json
{
  "min_priority": 1 // Minimum priority level (default: 1)
}
```

**Example:**

```
Input:  {"min_priority": 1}
Output:
  +1 Priority: Aqua Jet, Bullet Punch, Ice Shard, Mach Punch,
               Quick Attack, Shadow Sneak, Sucker Punch...
  +2 Priority: Extreme Speed, Feint...
  +3 Priority: Fake Out...
```

---

### `search_pokemon_by_ability`

Find all Pokemon with a specific ability.

**Schema:**

```json
{
  "ability": "string" // Ability name (e.g., "intimidate")
}
```

**Example:**

```
Input:  {"ability": "levitate"}
Output: Azelf, Bronzong, Cresselia, Eelektross, Flygon, Gengar,
        Hydreigon, Latias, Latios, Mismagius, Rotom, Uxie, Vikavolt...
```

---

### `list_dangerous_abilities`

List abilities that significantly impact battle outcomes.

**Schema:**

```json
{
  "category": "string" // One of: immunity, defense, reflect, offense,
  // priority, contact, or "all"
}
```

**Categories:**

- `immunity` — Levitate, Flash Fire, Volt Absorb, Water Absorb, etc.
- `defense` — Multiscale, Fur Coat, Fluffy, Marvel Scale, etc.
- `reflect` — Magic Bounce
- `offense` — Huge Power, Pure Power, Gorilla Tactics, etc.
- `priority` — Prankster, Gale Wings
- `contact` — Rough Skin, Iron Barbs, Flame Body, Static, etc.

---

## Architecture

```
┌─────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│                 │     │                     │     │                  │
│  Claude/LLM     │────▶│  mcpkmn-showdown    │────▶│  Local JSON      │
│                 │ MCP │  (MCP Server)       │     │  Cache           │
│                 │◀────│                     │◀────│                  │
└─────────────────┘     └─────────────────────┘     └──────────────────┘
                                                            │
                                                            │ (manual update)
                                                            ▼
                                                    ┌──────────────────┐
                                                    │  Pokemon         │
                                                    │  Showdown        │
                                                    │  Data Files      │
                                                    └──────────────────┘
```

**Why MCP?**

LLMs hallucinate Pokemon data — wrong stats, forgotten abilities, botched type calculations. MCP tools let the model query authoritative data instead of guessing from training.

**Why local JSON instead of connecting to Pokemon Showdown?**

Pokemon Showdown doesn't have a REST API. Their data is served as minified JavaScript for their web client. Connecting live would mean parsing JS on every query, network latency, rate limiting concerns, and breaking if they change formats.

| Approach            | Tradeoff                                            |
| ------------------- | --------------------------------------------------- |
| **Local JSON**      | Instant, offline, reliable — but data can go stale  |
| **Live connection** | Always fresh — but slow, fragile, requires internet |

For reference data (stats, moves, abilities), local is the right call. The data only changes with new games/DLC. For live features (ladder stats, ongoing battles), we'd need WebSocket connections — that's on the roadmap.

**Data sources** (from [Pokemon Showdown](https://github.com/smogon/pokemon-showdown)):

- `pokedex.json` — 1,500+ Pokemon with stats, types, abilities
- `moves_showdown.json` — 950+ moves with effects
- `abilities_full.json` — 300+ abilities with descriptions
- `items.json` — 580+ items with effects
- `typechart.json` — Complete type effectiveness matrix

To refresh the data: `python -m mcpkmn_showdown.data_fetcher`

---

## Safety & Limits

| Concern                 | How It's Handled                                     |
| ----------------------- | ---------------------------------------------------- |
| **Rate limits**         | None — all data is local, no external API calls      |
| **Data freshness**      | Ships with latest Showdown data; manually updateable |
| **Input validation**    | Names normalized and validated before lookup         |
| **Error handling**      | Returns helpful "not found" messages, never crashes  |
| **Credential handling** | No credentials needed, no auth, no API keys          |

---

## Roadmap

**Planned features:**

- [ ] Live battle integration (connect to a running Showdown battle)
- [ ] Team import/export (paste Showdown format, get structured data)
- [ ] Damage calculator integration
- [ ] Format-specific tier lists and banlists
- [ ] Usage statistics from Smogon

**Help wanted — good first issues:**

- [ ] Add `get_format` tool to explain format rules (OU, UU, etc.)
- [ ] Add `search_pokemon_by_type` tool
- [ ] Add `search_moves_by_type` tool
- [ ] Improve form normalization (regional forms, Gigantamax, etc.)
- [ ] Add more test coverage

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to get started.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines. Quick start:

```bash
git clone https://github.com/drewsungg/mcpkmn-showdown.git
cd mcpkmn-showdown
pip install -e ".[dev]"
pytest                    # Run tests
npx @modelcontextprotocol/inspector mcpkmn-showdown  # Interactive testing
```

![MCP Inspector](https://raw.githubusercontent.com/drewsungg/mcpkmn-showdown/main/content/mcp_inspector.png)

---

## I Want Your Feedback!

If you try this out, please let me know:

1. **Is the tool naming/schema intuitive for an agent?** Would different boundaries help?
2. **What's missing for your use case?** Teambuilding? Laddering? Replay analysis? Eval harness?
3. **Any security/abuse concerns?** Anything that could be misused?
4. **Does it behave well under load?** Concurrent requests? Long sessions?

Open an issue or reach out: [@drewsungg](https://github.com/drewsungg)

---

## Related Projects

- [pokemon-llm-battle-bot](https://github.com/drewsungg/pokemon-llm-battle-bot) — LLM-powered Pokemon battle bot using this MCP
- [Pokemon Showdown](https://pokemonshowdown.com/) — The competitive battle simulator
- [Model Context Protocol](https://modelcontextprotocol.io/) — The MCP specification

---

## License

MIT License — see [LICENSE](LICENSE) for details.

## Author

**Andrew Sung** 

— [@drewsungg](https://github.com/drewsungg)
- [drewsung@stanford.edu](mailto:drewsung@stanford.edu)
