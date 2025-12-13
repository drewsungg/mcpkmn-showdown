# Contributing to mcpkmn-showdown

Thanks for your interest in contributing! This guide will help you get started.

## Quick Start

```bash
# Clone the repo
git clone https://github.com/drewsungg/mcpkmn-showdown.git
cd mcpkmn-showdown

# Install in development mode
pip install -e ".[dev]"

# Verify it works
mcpkmn-showdown
# (Ctrl+C to exit)

# Test with MCP Inspector
npx @modelcontextprotocol/inspector mcpkmn-showdown
```

## Project Structure

```
mcpkmn-showdown/
├── mcpkmn_showdown/
│   ├── __init__.py           # Package exports
│   ├── pokemon_server.py     # MCP server + tool definitions
│   ├── data_loader.py        # Data loading utilities
│   ├── data_fetcher.py       # Fetches fresh data from Showdown
│   └── cache/                # Pre-loaded Pokemon data (JSON)
│       ├── pokedex.json
│       ├── moves_showdown.json
│       ├── abilities_full.json
│       ├── items.json
│       └── typechart.json
├── tests/                    # Test files
├── README.md
├── CONTRIBUTING.md
├── LICENSE
└── pyproject.toml
```

## Good First Issues

Looking for something to work on? Here are beginner-friendly contributions:

### Add a new tool

1. **`search_pokemon_by_type`** — Find all Pokemon of a given type
   - Input: `{"type": "dragon"}` or `{"types": ["dragon", "flying"]}`
   - Output: List of matching Pokemon

2. **`search_moves_by_type`** — Find all moves of a given type
   - Input: `{"type": "fire", "category": "physical"}`
   - Output: List of matching moves

3. **`get_format`** — Explain format rules (OU, UU, Ubers, etc.)
   - Input: `{"format": "ou"}`
   - Output: Banned Pokemon, clauses, description

### Improve existing functionality

4. **Better form handling** — Improve normalization for:
   - Regional forms (Alolan, Galarian, Hisuian, Paldean)
   - Gigantamax forms
   - Mega evolutions
   - Special forms (Rotom-Wash, Urshifu-Rapid-Strike)

5. **Add tests** — We need more test coverage:
   - Unit tests for data_loader.py
   - Integration tests for each tool
   - Edge case tests (weird names, missing data)

## Adding a New Tool

Here's how to add a new MCP tool:

### 1. Define the tool in `pokemon_server.py`

Add your tool definition in the `list_tools()` function:

```python
Tool(
    name="your_tool_name",
    description="What this tool does (1-2 sentences)",
    inputSchema={
        "type": "object",
        "properties": {
            "param_name": {
                "type": "string",
                "description": "What this parameter is for"
            }
        },
        "required": ["param_name"]
    }
)
```

### 2. Handle the tool call

Add your handler in the `call_tool()` function:

```python
elif name == "your_tool_name":
    param = arguments.get("param_name", "")
    # Your logic here
    result = do_something(param)
    return [TextContent(type="text", text=result)]
```

### 3. Test with MCP Inspector

```bash
npx @modelcontextprotocol/inspector mcpkmn-showdown
```

### 4. Update the README

Add your tool to the API Reference section.

## Code Style

- **Python 3.10+** — Use modern Python features
- **Type hints** — Add type hints to function signatures
- **Docstrings** — Document public functions
- **Keep it simple** — This is a small, focused project

We don't have strict linting yet, but please:
- Use 4 spaces for indentation
- Keep lines under 100 characters
- Use descriptive variable names

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mcpkmn_showdown

# Run a specific test
pytest tests/test_data_loader.py -v
```

## Updating Pokemon Data

The JSON data files can be refreshed from Pokemon Showdown:

```bash
python -m mcpkmn_showdown.data_fetcher
```

This fetches the latest `abilities.js` and `items.js` from Showdown and converts them to JSON.

**Note:** The pokedex, moves, and typechart are more stable and updated less frequently. If you need to update those, fetch them manually from [smogon/pokemon-showdown](https://github.com/smogon/pokemon-showdown/tree/master/data).

## Pull Request Process

1. **Fork the repo** and create your branch from `main`
2. **Make your changes** with clear, focused commits
3. **Test your changes** with MCP Inspector
4. **Update documentation** if you added/changed functionality
5. **Open a PR** with a clear description of what and why

### PR Title Format

- `feat: add search_pokemon_by_type tool`
- `fix: handle regional form names correctly`
- `docs: improve quickstart instructions`
- `test: add tests for data_loader`

## Questions?

- Open an issue for bugs or feature requests
- Tag `@drewsungg` for questions

Thanks for contributing!
