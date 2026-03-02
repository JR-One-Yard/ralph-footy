"""Teaching content — one 'Did You Know?' snippet per round.

Loads pre-written teaching topics from a JSON file, selects one per
round using modular rotation, resolves template variables from the
round's market data, and returns the finished snippet in Ralph's voice.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from ralph.models import MarketView

# Default location of the teaching topics JSON file, relative to the
# project root (two levels up from this module: ralph/ -> project root).
_DEFAULT_TOPICS_PATH = Path(__file__).resolve().parent.parent / "data" / "teaching_topics.json"

_REQUIRED_FIELDS = {"id", "title", "category", "template", "fallback"}


def load_teaching_topics(path: Path | None = None) -> list[dict]:
    """Load and validate teaching topics from the JSON file.

    Parameters
    ----------
    path:
        Path to the teaching topics JSON file.  Defaults to
        ``data/teaching_topics.json`` in the project root.

    Returns
    -------
    A list of topic dicts, each with ``id``, ``title``, ``category``,
    ``template``, and ``fallback`` keys.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the JSON is malformed or any topic is missing required fields.
    """
    path = path or _DEFAULT_TOPICS_PATH

    with open(path) as f:
        data = json.load(f)

    topics = data.get("topics")
    if not isinstance(topics, list) or len(topics) == 0:
        raise ValueError(f"Expected a non-empty 'topics' list in {path}")

    for i, topic in enumerate(topics):
        missing = _REQUIRED_FIELDS - set(topic.keys())
        if missing:
            raise ValueError(f"Topic at index {i} is missing required fields: {sorted(missing)}")

    return topics


def select_topic(round_number: int, total_topics: int) -> int:
    """Return the 0-based index of the topic for this round.

    Uses modular arithmetic so topics cycle after the library is
    exhausted.  Round 1 gets topic index 0, Round 2 gets index 1, etc.

    Parameters
    ----------
    round_number:
        The current NRL round number (1-indexed).
    total_topics:
        The total number of topics in the library.

    Returns
    -------
    A 0-based topic index.
    """
    return (round_number - 1) % total_topics


def build_teaching_context(market_views: list[MarketView]) -> dict:
    """Build a dict of template variables from the round's market data.

    Extracts summary stats that teaching snippets can reference:
    the biggest favourite, the tightest game, game counts, and
    confidence-tier counts.

    Parameters
    ----------
    market_views:
        The market consensus data for every game in the round.

    Returns
    -------
    A dict whose keys match the ``{variable}`` placeholders used in
    teaching topic templates.  Returns an empty dict if *market_views*
    is empty.
    """
    if not market_views:
        return {}

    # --- Biggest favourite ---------------------------------------------------
    biggest_fav_mv = max(market_views, key=lambda mv: mv.favourite_prob)

    # Find the best (lowest) odds offered on the biggest favourite across
    # all bookmaker sources for that game.
    fav_is_home = biggest_fav_mv.consensus_home_prob >= biggest_fav_mv.consensus_away_prob
    if biggest_fav_mv.odds_sources:
        fav_odds_values = [
            o.home_odds if fav_is_home else o.away_odds for o in biggest_fav_mv.odds_sources
        ]
        best_fav_odds = min(fav_odds_values)
    else:
        best_fav_odds = 0.0

    # Extract a short team name (last word) for readability.
    fav_name = biggest_fav_mv.favourite
    fav_short = fav_name.split()[-1] if fav_name else fav_name

    # Raw implied probability of the favourite (1/odds) before overround removal.
    example_raw_pct = f"{1.0 / best_fav_odds:.0%}" if best_fav_odds > 0 else "N/A"

    # --- Tightest game -------------------------------------------------------
    closest_mv = min(market_views, key=lambda mv: mv.favourite_prob)
    closest_fav_prob = closest_mv.favourite_prob

    # --- Confidence tier counts ----------------------------------------------
    num_locks = sum(1 for mv in market_views if mv.favourite_prob >= 0.70)
    num_coin_flips = sum(1 for mv in market_views if mv.favourite_prob < 0.55)

    return {
        # Biggest favourite variables
        "biggest_fav": fav_short,
        "biggest_fav_odds": f"${best_fav_odds:.2f}" if best_fav_odds > 0 else "N/A",
        "biggest_fav_prob": f"{biggest_fav_mv.favourite_prob:.0%}",
        "example_odds": f"${best_fav_odds:.2f}" if best_fav_odds > 0 else "$1.50",
        "example_raw_pct": example_raw_pct,
        "example_true_pct": f"{biggest_fav_mv.favourite_prob:.0%}",
        # Tightest game variables
        "closest_game_home": closest_mv.game.home_team.split()[-1],
        "closest_game_away": closest_mv.game.away_team.split()[-1],
        "closest_game_prob": f"{closest_fav_prob:.0%}",
        # Round-level counts
        "num_games": str(len(market_views)),
        "num_locks": str(num_locks),
        "num_coin_flips": str(num_coin_flips),
    }


def generate_teaching_snippet(
    round_number: int,
    market_views: list[MarketView],
    topics_path: Path | None = None,
) -> str:
    """Generate the 'Did You Know?' teaching snippet for a round.

    This is the main entry point for the teaching module.  It loads the
    topic library, selects the topic for this round, builds template
    context from the market data, and renders the snippet.

    If template rendering fails (e.g. missing variables), the topic's
    ``fallback`` text is returned instead.

    Parameters
    ----------
    round_number:
        The current NRL round number (1-indexed).
    market_views:
        Market consensus data for the round's games.
    topics_path:
        Optional override for the teaching topics JSON path.

    Returns
    -------
    A string containing the resolved teaching snippet, guaranteed to
    have no unresolved ``{variable}`` placeholders.
    """
    topics = load_teaching_topics(topics_path)
    idx = select_topic(round_number, len(topics))
    topic = topics[idx]

    template = topic["template"]
    fallback = topic["fallback"]

    # Build the context dict with a round_number entry as well.
    context = build_teaching_context(market_views)
    context["round_number"] = str(round_number)

    # Use a defaultdict so that any missing key returns a sentinel
    # value rather than raising KeyError.
    _MISSING = "???"
    safe_context: dict[str, str] = defaultdict(lambda: _MISSING, context)

    try:
        rendered = template.format_map(safe_context)
    except (KeyError, ValueError, IndexError):
        return fallback

    # If any sentinel values snuck through, or unresolved {placeholders}
    # remain, fall back to the safe version.
    if _MISSING in rendered or re.search(r"\{[a-z_]+\}", rendered):
        return fallback

    return rendered
