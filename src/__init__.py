"""
mcpkmn-showdown: Pokemon Showdown MCP Server

Provides Pokemon data lookup tools for LLMs via Model Context Protocol.
"""

from .data_loader import get_loader, PokemonDataLoader
from .pokemon_server import main

__version__ = "1.0.0"
__all__ = ["get_loader", "PokemonDataLoader", "main"]
