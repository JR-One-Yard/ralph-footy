"""Calibration and accuracy tracking — Brier score and beyond.

Tracks Ralph's tips against actual NRL results to measure
forecast quality. The Brier score is the primary metric:
a perfect forecaster scores 0.0; a coin-flipper scores 0.25.

Ralph's target: Brier score < 0.20 (consistently better than
a naive 50/50 baseline).
"""

from __future__ import annotations

from ralph.models import RoundTips


def brier_score(predicted_prob: float, actual_outcome: int) -> float:
    """Calculate Brier score for a single prediction.

    Args:
        predicted_prob: Ralph's predicted probability for the chosen team.
        actual_outcome: 1 if the chosen team won, 0 otherwise.

    Returns:
        Brier score (lower is better; 0.0 = perfect, 0.25 = coin flip).
    """
    raise NotImplementedError("Brier score tracking coming in Iteration 5")


def season_calibration(round_tips_history: list[RoundTips]) -> dict:
    """Analyse calibration across the season.

    Returns a dict with:
        - overall_brier: float (average Brier score)
        - accuracy: float (percentage of correct picks)
        - calibration_curve: dict (confidence bucket -> actual win rate)
    """
    raise NotImplementedError("Season calibration coming in Iteration 5")
