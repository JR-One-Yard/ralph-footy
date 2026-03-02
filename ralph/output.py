"""Formatted output and teaching content.

Produces the styled per-game output with Ralph's tip, market
breakdown, rationale, and a rotating "Did You Know?" teaching
moment about probability, markets, ML, or LLMs.
"""

from __future__ import annotations

from ralph.models import RoundTips, Tip


def format_tip(tip: Tip) -> str:
    """Format a single tip for terminal display."""
    raise NotImplementedError("Output formatting coming in Iteration 4")


def format_round(round_tips: RoundTips) -> str:
    """Format a full round of tips for terminal display."""
    raise NotImplementedError("Output formatting coming in Iteration 4")


def pick_teaching_topic(round_number: int) -> str:
    """Select a teaching topic for this round from the rotation library."""
    raise NotImplementedError("Teaching topic rotation coming in Iteration 4")
