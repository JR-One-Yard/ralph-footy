"""Data models for Ralph — NRL Footy Forecaster."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Game:
    """Represents a single NRL fixture."""

    home_team: str
    away_team: str
    venue: str
    kickoff: datetime
    round_number: int

    def __str__(self) -> str:
        return f"{self.home_team} vs {self.away_team} ({self.venue})"


@dataclass
class Odds:
    """Head-to-head odds from a single bookmaker source."""

    home_odds: float
    away_odds: float
    source: str

    @property
    def home_implied(self) -> float:
        """Raw implied probability for the home team (includes overround)."""
        return 1.0 / self.home_odds

    @property
    def away_implied(self) -> float:
        """Raw implied probability for the away team (includes overround)."""
        return 1.0 / self.away_odds

    @property
    def overround(self) -> float:
        """The bookmaker's margin (overround) as a percentage."""
        return (self.home_implied + self.away_implied - 1.0) * 100


@dataclass
class Tip:
    """Ralph's tip for a single game."""

    game: Game
    pick: str
    confidence: float
    rationale: str
    teaching_moment: str

    @property
    def confidence_label(self) -> str:
        """Human-readable confidence label."""
        if self.confidence >= 0.70:
            return "Lock"
        elif self.confidence >= 0.55:
            return "Lean"
        else:
            return "Coin Flip"


@dataclass
class MarketView:
    """Market consensus probabilities for a single game."""

    game: Game
    odds_sources: list[Odds]
    consensus_home_prob: float
    consensus_away_prob: float

    @property
    def favourite(self) -> str:
        """The team the market favours."""
        if self.consensus_home_prob >= self.consensus_away_prob:
            return self.game.home_team
        return self.game.away_team

    @property
    def favourite_prob(self) -> float:
        """Probability assigned to the favourite."""
        return max(self.consensus_home_prob, self.consensus_away_prob)


@dataclass
class RoundTips:
    """Collection of tips for a full NRL round."""

    round_number: int
    season: int
    tips: list[Tip] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    teaching_moment: str = ""

    @property
    def total_games(self) -> int:
        return len(self.tips)
