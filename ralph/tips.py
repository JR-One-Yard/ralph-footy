"""Tip generation — picks the team with the higher market consensus probability.

Takes MarketView objects (market consensus probabilities) and generates
deterministic tips with confidence levels.  After generating each tip,
the rationale is populated using template-driven generation from
:mod:`ralph.rationale`.  Teaching content is left as an empty string
to be filled by later pipeline stages.
"""

from __future__ import annotations

from ralph.models import MarketView, RoundTips, Tip
from ralph.rationale import generate_rationale


def generate_tip(market_view: MarketView, game_index: int = 0) -> Tip:
    """Generate Ralph's tip for a single game.

    Picks the team with the higher consensus probability.  When
    probabilities are exactly equal (50/50), the home team wins as a
    tie-break (home advantage is real in NRL).

    When called with a *market_view* and *game_index*, the rationale
    field is populated using :func:`ralph.rationale.generate_rationale`.

    Parameters
    ----------
    market_view:
        A :class:`MarketView` containing the consensus probabilities
        for the game.
    game_index:
        0-based position of the game in the round fixture list.
        Used for deterministic template rotation in rationale
        generation.

    Returns
    -------
    A :class:`Tip` with ``pick`` set to the favoured team,
    ``confidence`` set to the favourite's probability, a populated
    ``rationale``, and ``teaching_moment`` as an empty string.
    """
    tip = Tip(
        game=market_view.game,
        pick=market_view.favourite,
        confidence=market_view.favourite_prob,
        rationale="",
        teaching_moment="",
    )
    tip.rationale = generate_rationale(tip, market_view, game_index)
    return tip


def generate_round_tips(
    market_views: list[MarketView],
    round_number: int,
    season: int,
) -> RoundTips:
    """Generate tips for a full NRL round.

    Calls :func:`generate_tip` for each :class:`MarketView` and
    assembles the results into a :class:`RoundTips`.  Each tip's
    rationale is populated using deterministic template rotation.

    Parameters
    ----------
    market_views:
        One :class:`MarketView` per game in the round.
    round_number:
        The round number (e.g. 1).
    season:
        The season year (e.g. 2025).

    Returns
    -------
    A :class:`RoundTips` with one :class:`Tip` per game (each with
    a populated rationale) and ``teaching_moment`` as an empty string.
    """
    tips = [generate_tip(mv, game_index=i) for i, mv in enumerate(market_views)]
    return RoundTips(
        round_number=round_number,
        season=season,
        tips=tips,
        teaching_moment="",
    )
