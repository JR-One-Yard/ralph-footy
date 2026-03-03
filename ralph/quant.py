"""Quant analysis engine — rich metrics derived from bookmaker odds.

Takes MarketView objects and produces per-game and per-round analytics.
All calculations use existing 2-3 bookmaker odds — no new data sources.
"""

from __future__ import annotations

from ralph.models import GameAnalysis, MarketView, RoundAnalysis


def _best_odds_for_side(
    market_view: MarketView, is_home: bool, *, best_means_highest: bool = False
) -> tuple[float, str]:
    """Find the best odds for one side across all bookmaker sources.

    Parameters
    ----------
    market_view:
        Market data for the game.
    is_home:
        True for the home team, False for the away team.
    best_means_highest:
        If True, return the highest odds (best for a backer).
        If False, return the lowest odds (shortest price).

    Returns
    -------
    (odds_value, source_name)
    """
    if not market_view.odds_sources:
        return 0.0, "N/A"

    pick_fn = max if best_means_highest else min
    if is_home:
        best = pick_fn(market_view.odds_sources, key=lambda o: o.home_odds)
        return best.home_odds, best.source
    else:
        best = pick_fn(market_view.odds_sources, key=lambda o: o.away_odds)
        return best.away_odds, best.source


def _market_spread(market_view: MarketView) -> float:
    """Bookmaker disagreement: range of implied probs for the favourite.

    Uses the favourite's implied probability across bookmakers.
    Wide spread = bookmakers disagree = uncertainty.
    """
    if len(market_view.odds_sources) < 2:
        return 0.0

    fav_is_home = market_view.consensus_home_prob >= market_view.consensus_away_prob

    if fav_is_home:
        probs = [1.0 / o.home_odds for o in market_view.odds_sources]
    else:
        probs = [1.0 / o.away_odds for o in market_view.odds_sources]

    return max(probs) - min(probs)


def _expected_value(consensus_prob: float, best_odds: float) -> float:
    """EV = (consensus_prob × best_odds) - 1.

    Positive EV means a quant would consider the bet.
    """
    if best_odds <= 0:
        return 0.0
    return (consensus_prob * best_odds) - 1.0


def _kelly_fraction(prob: float, odds: float) -> float:
    """Kelly criterion: f* = (bp - q) / b.

    Where b = odds - 1, p = prob, q = 1 - p.
    Returns 0 if the fraction is negative (no bet).
    """
    if odds <= 1.0 or prob <= 0 or prob >= 1:
        return 0.0
    b = odds - 1.0
    q = 1.0 - prob
    f = (b * prob - q) / b
    return max(0.0, f)


def _value_discrepancy(market_view: MarketView) -> tuple[float, str]:
    """Find the largest discrepancy between any single bookie and consensus.

    Returns (max_discrepancy, source_name).
    """
    if not market_view.odds_sources:
        return 0.0, "N/A"

    fav_is_home = market_view.consensus_home_prob >= market_view.consensus_away_prob
    consensus_prob = market_view.favourite_prob

    max_disc = 0.0
    max_source = market_view.odds_sources[0].source

    for odds in market_view.odds_sources:
        if fav_is_home:
            raw = 1.0 / odds.home_odds
        else:
            raw = 1.0 / odds.away_odds
        # Normalise this bookie's implied prob (remove their overround)
        total_raw = (1.0 / odds.home_odds) + (1.0 / odds.away_odds)
        normalised = raw / total_raw

        disc = abs(normalised - consensus_prob)
        if disc > max_disc:
            max_disc = disc
            max_source = odds.source

    return max_disc, max_source


def analyse_game(market_view: MarketView) -> GameAnalysis:
    """Produce quant analytics for a single game."""
    spread = _market_spread(market_view)

    # Overrounds per bookmaker
    overrounds = {o.source: o.overround for o in market_view.odds_sources}

    # Determine favourite/underdog sides
    fav_is_home = market_view.consensus_home_prob >= market_view.consensus_away_prob
    fav_prob = market_view.favourite_prob
    dog_prob = 1.0 - fav_prob

    # Best odds for each side (highest = best value for a backer)
    best_fav_odds, best_fav_source = _best_odds_for_side(
        market_view, is_home=fav_is_home, best_means_highest=True
    )
    best_dog_odds, best_dog_source = _best_odds_for_side(
        market_view, is_home=not fav_is_home, best_means_highest=True
    )

    # EV and Kelly
    ev_fav = _expected_value(fav_prob, best_fav_odds)
    ev_dog = _expected_value(dog_prob, best_dog_odds)
    kelly_fav = _kelly_fraction(fav_prob, best_fav_odds)
    kelly_dog = _kelly_fraction(dog_prob, best_dog_odds)

    # Value discrepancy
    max_disc, disc_source = _value_discrepancy(market_view)

    return GameAnalysis(
        market_view=market_view,
        market_spread=spread,
        overrounds=overrounds,
        ev_favourite=ev_fav,
        ev_underdog=ev_dog,
        kelly_favourite=kelly_fav,
        kelly_underdog=kelly_dog,
        max_value_discrepancy=max_disc,
        discrepancy_source=disc_source,
        best_odds_favourite=best_fav_odds,
        best_odds_favourite_source=best_fav_source,
        best_odds_underdog=best_dog_odds,
        best_odds_underdog_source=best_dog_source,
    )


def analyse_round(
    market_views: list[MarketView], round_number: int
) -> RoundAnalysis:
    """Produce quant analytics for an entire round."""
    game_analyses = [analyse_game(mv) for mv in market_views]
    return RoundAnalysis(
        round_number=round_number,
        game_analyses=game_analyses,
    )
