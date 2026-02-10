"""
Smogon Stats Fetcher and Parser

Fetches competitive usage statistics from Smogon's stats archives.
Provides Pokemon usage data, movesets, teammates, and counters for team building.
"""

import json
import re
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


SMOGON_STATS_URL = "https://www.smogon.com/stats"
STATS_CACHE_DIR = Path(__file__).parent / "cache" / "stats"
CACHE_MAX_AGE_DAYS = 30


@dataclass
class PokemonUsageData:
    """Competitive usage data for a single Pokemon in a format."""
    name: str
    raw_count: int = 0
    avg_weight: float = 0.0
    viability_ceiling: int = 0
    abilities: dict[str, float] = field(default_factory=dict)
    items: dict[str, float] = field(default_factory=dict)
    spreads: dict[str, float] = field(default_factory=dict)
    moves: dict[str, float] = field(default_factory=dict)
    tera_types: dict[str, float] = field(default_factory=dict)
    teammates: dict[str, float] = field(default_factory=dict)
    checks_and_counters: list[dict[str, Any]] = field(default_factory=list)


def _get_latest_month() -> str:
    """Get the most likely available stats month (previous month)."""
    now = datetime.now()
    # Stats are usually available for the previous month
    if now.day < 5:
        # First few days of month, stats might not be up yet - use 2 months ago
        target = now.replace(day=1) - timedelta(days=32)
    else:
        target = now.replace(day=1) - timedelta(days=1)
    return target.strftime("%Y-%m")


def _get_cache_path(format_id: str, rating: int, year_month: str) -> Path:
    """Get the cache file path for given parameters."""
    return STATS_CACHE_DIR / f"stats_{format_id}_{rating}_{year_month}.json"


def _is_cache_fresh(cache_path: Path) -> bool:
    """Check if a cache file exists and is not stale."""
    if not cache_path.exists():
        return False
    mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
    return (datetime.now() - mtime) < timedelta(days=CACHE_MAX_AGE_DAYS)


def _fetch_stats_text(format_id: str, rating: int, year_month: str) -> str | None:
    """Fetch raw stats text from Smogon."""
    url = f"{SMOGON_STATS_URL}/{year_month}/moveset/{format_id}-{rating}.txt"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "mcpkmn-showdown/1.1"})
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode("utf-8")
    except Exception:
        return None


def _parse_section_entries(lines: list[str]) -> dict[str, float]:
    """Parse lines like 'Item Name 37.651%' into a dict."""
    result = {}
    for line in lines:
        line = line.strip().strip("|").strip()
        if not line:
            continue
        # Match: name followed by percentage
        match = re.match(r'^(.+?)\s+([\d.]+)%\s*$', line)
        if match:
            name = match.group(1).strip()
            if name.lower() == "other":
                continue
            pct = float(match.group(2))
            result[name] = pct
    return result


def _parse_checks_and_counters(lines: list[str]) -> list[dict[str, Any]]:
    """Parse checks and counters section."""
    results = []
    i = 0
    while i < len(lines):
        line = lines[i].strip().strip("|").strip()
        if not line:
            i += 1
            continue

        # Match: "Pokemon Name 54.493 (78.40±5.98)"
        match = re.match(r'^(.+?)\s+([\d.]+)\s+\(([\d.]+)±([\d.]+)\)\s*$', line)
        if match:
            name = match.group(1).strip()
            score = float(match.group(2))
            mean = float(match.group(3))
            std = float(match.group(4))

            entry = {"name": name, "score": score, "mean": mean, "std": std}

            # Check next line for KO/switch details
            if i + 1 < len(lines):
                detail_line = lines[i + 1].strip().strip("|").strip()
                ko_match = re.search(r'([\d.]+)%\s*KOed', detail_line)
                sw_match = re.search(r'([\d.]+)%\s*switched out', detail_line)
                if ko_match:
                    entry["koed_pct"] = float(ko_match.group(1))
                if sw_match:
                    entry["switched_pct"] = float(sw_match.group(1))
                if ko_match or sw_match:
                    i += 1

            results.append(entry)
        i += 1
    return results


def _parse_pokemon_block(block: str) -> PokemonUsageData | None:
    """Parse a single Pokemon's stats block."""
    lines = block.strip().split("\n")

    # Extract sections by splitting on +---+ borders
    sections: list[list[str]] = []
    current_section: list[str] = []

    for line in lines:
        if re.match(r'^\s*\+[-+]+\+\s*$', line):
            if current_section:
                sections.append(current_section)
                current_section = []
        else:
            current_section.append(line)
    if current_section:
        sections.append(current_section)

    if not sections:
        return None

    # First section is the Pokemon name
    name_line = sections[0][0].strip().strip("|").strip()
    if not name_line:
        return None

    data = PokemonUsageData(name=name_line)

    # Second section is raw stats
    if len(sections) > 1:
        for line in sections[1]:
            line = line.strip().strip("|").strip()
            if line.startswith("Raw count:"):
                try:
                    data.raw_count = int(line.split(":")[1].strip())
                except (ValueError, IndexError):
                    pass
            elif line.startswith("Avg. weight:"):
                try:
                    data.avg_weight = float(line.split(":")[1].strip())
                except (ValueError, IndexError):
                    pass
            elif line.startswith("Viability Ceiling:"):
                try:
                    data.viability_ceiling = int(line.split(":")[1].strip())
                except (ValueError, IndexError):
                    pass

    # Remaining sections are keyed by header
    for section in sections[2:]:
        if not section:
            continue
        header = section[0].strip().strip("|").strip().lower()
        entries = section[1:]

        if header == "abilities":
            data.abilities = _parse_section_entries(entries)
        elif header == "items":
            data.items = _parse_section_entries(entries)
        elif header == "spreads":
            data.spreads = _parse_section_entries(entries)
        elif header == "moves":
            data.moves = _parse_section_entries(entries)
        elif header == "tera types":
            data.tera_types = _parse_section_entries(entries)
        elif header == "teammates":
            data.teammates = _parse_section_entries(entries)
        elif header == "checks and counters":
            data.checks_and_counters = _parse_checks_and_counters(entries)

    return data


def _parse_stats(raw_text: str) -> dict[str, PokemonUsageData]:
    """Parse the full Smogon stats text file into a dict of Pokemon data."""
    results = {}
    lines = raw_text.split("\n")

    # Find indices of all +---+ border lines
    border_indices = [
        i for i, line in enumerate(lines)
        if re.match(r'^\s*\+[-+]+\+\s*$', line)
    ]

    # A Pokemon entry starts with: +---+ / | Name | / +---+
    # Identify these by finding consecutive borders with exactly one line between
    # where that line is a Pokemon name (not a section header like "Abilities")
    section_headers = {
        "abilities", "items", "spreads", "moves", "tera types",
        "teammates", "checks and counters",
    }
    block_starts = []
    for idx in range(len(border_indices) - 1):
        b1 = border_indices[idx]
        b2 = border_indices[idx + 1]
        if b2 - b1 == 2:
            between = lines[b1 + 1].strip().strip("|").strip()
            if between and between.lower() not in section_headers and ":" not in between:
                block_starts.append(b1)

    # Extract each Pokemon block from its start to the next block's start
    for i, start in enumerate(block_starts):
        end = block_starts[i + 1] if i + 1 < len(block_starts) else len(lines)
        block_text = "\n".join(lines[start:end])
        pokemon = _parse_pokemon_block(block_text)
        if pokemon and pokemon.name:
            key = pokemon.name.lower().replace(" ", "").replace("-", "")
            results[key] = pokemon

    return results


def _save_to_cache(data: dict[str, PokemonUsageData], cache_path: Path) -> None:
    """Save parsed data to cache as JSON."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = {k: asdict(v) for k, v in data.items()}
    with open(cache_path, "w") as f:
        json.dump(serialized, f, indent=2)


def _load_from_cache(cache_path: Path) -> dict[str, PokemonUsageData]:
    """Load parsed data from cache JSON."""
    with open(cache_path) as f:
        raw = json.load(f)
    result = {}
    for key, val in raw.items():
        result[key] = PokemonUsageData(**val)
    return result


class SmogonStatsLoader:
    """Loads and caches Smogon competitive statistics."""

    def __init__(self):
        self._cache: dict[str, dict[str, PokemonUsageData]] = {}

    def get_stats(
        self, format_id: str, rating: int = 1825, year_month: str | None = None
    ) -> dict[str, PokemonUsageData]:
        """
        Get usage statistics for a format.

        Args:
            format_id: Format identifier (e.g., "gen9ou", "gen9vgc2025")
            rating: ELO rating cutoff (default 1825)
            year_month: Stats month in "YYYY-MM" format (default: latest available)

        Returns:
            Dict mapping normalized Pokemon name -> PokemonUsageData
        """
        if year_month is None:
            year_month = _get_latest_month()

        cache_key = f"{format_id}_{rating}_{year_month}"

        # Check memory cache
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Check file cache
        cache_path = _get_cache_path(format_id, rating, year_month)
        if _is_cache_fresh(cache_path):
            data = _load_from_cache(cache_path)
            self._cache[cache_key] = data
            return data

        # Fetch and parse
        raw_text = _fetch_stats_text(format_id, rating, year_month)
        if raw_text is None:
            # Try previous month if current month fails
            prev = _get_latest_month()
            if prev != year_month:
                raw_text = _fetch_stats_text(format_id, rating, prev)
                if raw_text:
                    year_month = prev

            if raw_text is None:
                return {}

        data = _parse_stats(raw_text)
        _save_to_cache(data, _get_cache_path(format_id, rating, year_month))
        self._cache[f"{format_id}_{rating}_{year_month}"] = data
        return data

    def get_pokemon(
        self, pokemon_name: str, format_id: str, rating: int = 1825
    ) -> PokemonUsageData | None:
        """Get usage data for a specific Pokemon."""
        stats = self.get_stats(format_id, rating)
        key = pokemon_name.lower().replace(" ", "").replace("-", "")
        return stats.get(key)

    def get_top_pokemon(
        self, format_id: str, top_n: int = 20, rating: int = 1825
    ) -> list[PokemonUsageData]:
        """Get the top N Pokemon by raw count."""
        stats = self.get_stats(format_id, rating)
        sorted_pokemon = sorted(stats.values(), key=lambda p: p.raw_count, reverse=True)
        return sorted_pokemon[:top_n]

    def get_counters(
        self, pokemon_name: str, format_id: str, rating: int = 1825
    ) -> list[dict[str, Any]]:
        """Get checks and counters for a Pokemon."""
        pokemon = self.get_pokemon(pokemon_name, format_id, rating)
        if pokemon is None:
            return []
        return pokemon.checks_and_counters

    def get_teammates(
        self, pokemon_name: str, format_id: str, rating: int = 1825
    ) -> dict[str, float]:
        """Get common teammates for a Pokemon."""
        pokemon = self.get_pokemon(pokemon_name, format_id, rating)
        if pokemon is None:
            return {}
        return pokemon.teammates


# Global instance
_stats_loader: SmogonStatsLoader | None = None


def get_stats_loader() -> SmogonStatsLoader:
    """Get the global stats loader instance."""
    global _stats_loader
    if _stats_loader is None:
        _stats_loader = SmogonStatsLoader()
    return _stats_loader
