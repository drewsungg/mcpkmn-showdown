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
| `get_smogon_usage`          | Top Pokemon by usage in a format      | `format: string`              |
| `get_smogon_sets`           | Competitive sets (moves, items, EVs)  | `pokemon`, `format`           |
| `get_pokemon_counters`      | What checks/counters a Pokemon        | `pokemon`, `format`           |
| `get_pokemon_teammates`     | Best teammates by co-occurrence       | `pokemon`, `format`           |
| `search_pokemon_by_stat`    | Filter Pokemon by base stats          | `stat`, `min_value`, `max_value` |
| `search_moves_by_effect`    | Find moves by strategic category      | `effect: string`              |
| `get_format_info`           | Format rules and meta characteristics | `format: string`              |

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

### `get_smogon_usage`

Get the most-used Pokemon in a competitive format from Smogon stats.

**Schema:**

```json
{
  "format": "string",  // Format ID (e.g., "gen9ou", "gen9vgc2025")
  "top_n": 20          // Number of results (default: 20)
}
```

**Example:**

```
Input:  {"format": "gen9ou", "top_n": 5}
Output:
  1. Great Tusk (usage count: 619,002) — Top moves: Rapid Spin, Headlong Rush, Ice Spinner
  2. Darkrai (usage count: 500,000) — Top moves: Dark Void, Dark Pulse
  ...
```

---

### `get_smogon_sets`

Get competitive sets for a specific Pokemon: moves, items, abilities, EV spreads, Tera types, and teammates.

**Schema:**

```json
{
  "pokemon": "string",  // Pokemon name (e.g., "Great Tusk")
  "format": "string"    // Format ID (e.g., "gen9ou")
}
```

---

### `get_pokemon_counters`

Get what checks and counters a Pokemon in competitive play, with KO and switch-out rates.

**Schema:**

```json
{
  "pokemon": "string",  // Pokemon name
  "format": "string"    // Format ID
}
```

---

### `get_pokemon_teammates`

Get the best teammates for a Pokemon based on co-occurrence in competitive teams.

**Schema:**

```json
{
  "pokemon": "string",  // Pokemon name
  "format": "string"    // Format ID
}
```

---

### `search_pokemon_by_stat`

Find Pokemon filtered by base stat ranges. Useful for building teams around specific stat requirements (e.g., slow Pokemon for Trick Room, fast sweepers, bulky walls).

**Schema:**

```json
{
  "stat": "string",     // Stat: "hp", "atk", "def", "spa", "spd", "spe"
  "min_value": 0,       // Minimum value (default: 0)
  "max_value": 999,     // Maximum value (default: 999)
  "types": ["string"],  // Optional type filter
  "tier": "string"      // Optional tier filter (e.g., "OU")
}
```

**Example:**

```
Input:  {"stat": "spe", "max_value": 30, "types": ["Steel"]}
Output: Ferrothorn (Grass/Steel, Spe: 20), Stakataka (Rock/Steel, Spe: 13), ...
```

---

### `search_moves_by_effect`

Find moves by strategic category for team building.

**Schema:**

```json
{
  "effect": "string",    // Category (see below)
  "move_type": "string"  // Optional type filter
}
```

**Categories:** `spread`, `priority`, `recovery`, `setup`, `hazard`, `hazard_removal`, `weather`, `terrain`, `screen`, `pivot`, `speed_control`, `redirection`, `protect`

---

### `get_format_info`

Get rules, clauses, bans, and meta characteristics for a competitive format.

**Schema:**

```json
{
  "format": "string"  // Format name (e.g., "gen9ou", "gen9vgc2025")
}
```

**Supported formats:** gen9ou, gen9uu, gen9ubers, gen9vgc2025, gen9doublesou, gen9randombattle

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

For reference data (stats, moves, abilities), local is the right call. The data only changes with new games/DLC. Smogon usage stats are fetched live on first request and cached for 30 days (stats update monthly).

**Data sources:**

- [Pokemon Showdown](https://github.com/smogon/pokemon-showdown) — `pokedex.json`, `moves_showdown.json`, `abilities_full.json`, `items.json`, `typechart.json`
- [Smogon Stats](https://www.smogon.com/stats/) — Usage statistics, movesets, teammates, counters (fetched on demand, cached locally)

To refresh the static data: `python -m mcpkmn_showdown.data_fetcher`

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
- [x] ~~Format-specific tier lists and banlists~~ (`get_format_info`)
- [x] ~~Usage statistics from Smogon~~ (`get_smogon_usage`, `get_smogon_sets`)

**Help wanted — good first issues:**

- [ ] Add `search_pokemon_by_type` tool
- [ ] Improve form normalization (regional forms, Gigantamax, etc.)
- [ ] Add more test coverage
- [ ] Support more formats in `get_format_info`

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
- [@drewsungg](https://github.com/drewsungg)
- [drewsung@stanford.edu](mailto:drewsung@stanford.edu)
