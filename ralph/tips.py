"""Tip generation — combines market consensus and sentiment into picks.

Takes the market consensus probabilities, applies LLM sentiment
adjustments, and generates final picks with confidence levels.
"""

from __future__ import annotations

from ralph.models import Game, RoundTips, Tip


def generate_tip(game: Game) -> Tip:
    """Generate Ralph's tip for a single game."""
    raise NotImplementedError("Tip generation coming in Iteration 4")


def generate_round_tips(games: list[Game], round_number: int, season: int) -> RoundTips:
    """Generate tips for a full NRL round."""
    raise NotImplementedError("Tip generation coming in Iteration 4")
