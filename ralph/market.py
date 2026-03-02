"""Market consensus engine — odds to implied probabilities.

Converts bookmaker H2H odds into implied probabilities, removes
the overround, and averages across multiple sources to derive
a market consensus view.
"""

from __future__ import annotations

from ralph.models import Game, MarketView, Odds
from ralph.team_names import build_game_key


def odds_to_implied_probability(odds: float) -> float:
    """Convert decimal odds to raw implied probability.

    Parameters
    ----------
    odds:
        Decimal (Australian) odds.  Must be > 1.0.

    Returns
    -------
    The raw implied probability (1 / odds).

    Raises
    ------
    ValueError
        If *odds* is <= 1.0 (impossible in decimal format).
    """
    if odds <= 1.0:
        raise ValueError(
            f"Decimal odds must be greater than 1.0, got {odds!r}. "
            "Odds of 1.0 or below are impossible in decimal format."
        )
    return 1.0 / odds


def remove_overround(home_implied: float, away_implied: float) -> tuple[float, float]:
    """Remove the bookmaker's margin (overround) via multiplicative normalisation.

    Parameters
    ----------
    home_implied:
        Raw implied probability for the home team (0 < p <= 1).
    away_implied:
        Raw implied probability for the away team (0 < p <= 1).

    Returns
    -------
    A tuple of ``(true_home_prob, true_away_prob)`` that sums to 1.0.

    Raises
    ------
    ValueError
        If either implied probability is not in the range (0, 1].
    """
    for label, value in [("home_implied", home_implied), ("away_implied", away_implied)]:
        if value <= 0 or value > 1:
            raise ValueError(f"{label} must be > 0 and <= 1, got {value!r}")

    total = home_implied + away_implied
    return home_implied / total, away_implied / total


def market_consensus(odds_list: list[Odds]) -> tuple[float, float]:
    """Derive market consensus probabilities from one or more bookmaker sources.

    For each bookmaker:
    1. Convert decimal odds to raw implied probabilities.
    2. Remove the overround to get true implied probabilities.

    Then average the true probabilities across all bookmakers and
    re-normalise so the result sums to exactly 1.0.

    Parameters
    ----------
    odds_list:
        A list of ``Odds`` objects (one per bookmaker).  Must contain at
        least one entry.

    Returns
    -------
    A tuple of ``(consensus_home_prob, consensus_away_prob)``.

    Raises
    ------
    ValueError
        If *odds_list* is empty or any bookmaker has invalid odds.
    """
    if not odds_list:
        raise ValueError("odds_list must contain at least one bookmaker source")

    home_probs: list[float] = []
    away_probs: list[float] = []

    for odds in odds_list:
        home_implied = odds_to_implied_probability(odds.home_odds)
        away_implied = odds_to_implied_probability(odds.away_odds)
        true_home, true_away = remove_overround(home_implied, away_implied)
        home_probs.append(true_home)
        away_probs.append(true_away)

    # Average across bookmakers
    n = len(odds_list)
    avg_home = sum(home_probs) / n
    avg_away = sum(away_probs) / n

    # Re-normalise to guarantee the pair sums to exactly 1.0
    total = avg_home + avg_away
    return avg_home / total, avg_away / total


def build_market_views(games: list[Game], odds_map: dict[str, list[Odds]]) -> list[MarketView]:
    """Build a :class:`MarketView` for each game using the odds map.

    Parameters
    ----------
    games:
        List of games for the round (from :func:`ralph.fixtures.load_fixtures`).
    odds_map:
        Dict mapping game keys (``"HomeTeam v AwayTeam"``) to lists of
        ``Odds`` objects (also from :func:`ralph.fixtures.load_fixtures`).

    Returns
    -------
    A list of ``MarketView`` objects, one per game.  Games that have no
    odds in the map receive a default 50/50 consensus.
    """
    views: list[MarketView] = []
    for game in games:
        game_key = build_game_key(game.home_team, game.away_team)
        odds_list = odds_map.get(game_key, [])

        if odds_list:
            home_prob, away_prob = market_consensus(odds_list)
        else:
            # No odds available — default to a coin flip.
            home_prob, away_prob = 0.5, 0.5

        views.append(
            MarketView(
                game=game,
                odds_sources=odds_list,
                consensus_home_prob=home_prob,
                consensus_away_prob=away_prob,
            )
        )
    return views
