"""LLM sentiment layer — secondary signal from news and narrative.

Uses Claude to search for team news (injuries, suspensions, weather),
analyse recent form, and generate a small probability adjustment
(+/- 1-5%) to the market consensus.
"""

from __future__ import annotations

from ralph.models import Game


def analyse_sentiment(game: Game) -> dict:
    """Analyse team news and sentiment for a given game.

    Returns a dict with:
        - adjustment: float (+/- probability adjustment)
        - reasoning: str (explanation of the adjustment)
        - news: list[str] (relevant news items found)
    """
    raise NotImplementedError("LLM sentiment layer coming in Iteration 3")
