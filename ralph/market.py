"""Market consensus engine — odds to implied probabilities.

Converts bookmaker H2H odds into implied probabilities, removes
the overround, and averages across multiple sources to derive
a market consensus view.
"""

from __future__ import annotations

from ralph.models import Game, Odds


def odds_to_implied_probability(odds: float) -> float:
    """Convert decimal odds to raw implied probability."""
    raise NotImplementedError("Market consensus engine coming in Iteration 1")


def remove_overround(home_implied: float, away_implied: float) -> tuple[float, float]:
    """Remove the bookmaker's margin to get true implied probabilities."""
    raise NotImplementedError("Market consensus engine coming in Iteration 1")


def market_consensus(odds_list: list[Odds]) -> tuple[float, float]:
    """Average implied probabilities across multiple bookmaker sources."""
    raise NotImplementedError("Market consensus engine coming in Iteration 1")
