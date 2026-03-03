"""Tip generation — picks the team with the higher market consensus probability.

Takes MarketView objects (market consensus probabilities) and generates
tips with confidence levels.  After generating each tip, the rationale
is populated using either Claude API calls (online) or enriched templates
(offline).  Teaching content is left as an empty string to be filled by
later pipeline stages.
"""

from __future__ import annotations

from ralph.models import GameAnalysis, MarketView, RoundAnalysis, RoundTips, Tip
from ralph.rationale import generate_rationale


def generate_tip(
    market_view: MarketView,
    game_index: int = 0,
    game_analysis: GameAnalysis | None = None,
    offline: bool = False,
) -> Tip:
    """Generate Ralph's tip for a single game.

    Picks the team with the higher consensus probability.  When
    probabilities are exactly equal (50/50), the home team wins as a
    tie-break (home advantage is real in NRL).
    """
    tip = Tip(
        game=market_view.game,
        pick=market_view.favourite,
        confidence=market_view.favourite_prob,
        rationale="",
        teaching_moment="",
    )
    tip.rationale = generate_rationale(
        tip, market_view, game_index,
        game_analysis=game_analysis,
        offline=offline,
    )
    return tip


def generate_round_tips(
    market_views: list[MarketView],
    round_number: int,
    season: int,
    round_analysis: RoundAnalysis | None = None,
    offline: bool = False,
) -> RoundTips:
    """Generate tips for a full NRL round.

    When *round_analysis* is provided, each tip's rationale is enriched
    with quant metrics.  When *offline* is True, API calls are skipped.
    """
    game_analyses = round_analysis.game_analyses if round_analysis else None

    tips = []
    for i, mv in enumerate(market_views):
        ga = None
        if game_analyses:
            # Match by identity (same MarketView object)
            for candidate in game_analyses:
                if candidate.market_view is mv:
                    ga = candidate
                    break
        tips.append(generate_tip(mv, game_index=i, game_analysis=ga, offline=offline))

    return RoundTips(
        round_number=round_number,
        season=season,
        tips=tips,
        teaching_moment="",
    )
