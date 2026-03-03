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
        """The team the market favours.

        Includes a 1.5% home-advantage buffer: if the away team's edge
        is less than 1.5%, prefer the home team.  This reflects real
        NRL home advantage (~55-57% win rate historically).
        """
        away_edge = self.consensus_away_prob - self.consensus_home_prob
        if away_edge < 0.015:
            return self.game.home_team
        return self.game.away_team

    @property
    def favourite_prob(self) -> float:
        """Probability assigned to the favourite."""
        return max(self.consensus_home_prob, self.consensus_away_prob)


@dataclass
class GameAnalysis:
    """Quant-derived analytics for a single game, computed from bookmaker odds."""

    market_view: MarketView

    # Bookmaker disagreement: max - min implied prob across sources
    market_spread: float
    # Per-bookmaker overround percentages {source: overround%}
    overrounds: dict[str, float]
    # Expected value: (consensus_prob × best_odds) - 1
    ev_favourite: float
    ev_underdog: float
    # Kelly fraction: f* = (bp - q) / b
    kelly_favourite: float
    kelly_underdog: float
    # Largest discrepancy between any single bookie and consensus
    max_value_discrepancy: float
    discrepancy_source: str  # which bookie disagrees most
    # Best odds for each side and their source
    best_odds_favourite: float
    best_odds_favourite_source: str
    best_odds_underdog: float
    best_odds_underdog_source: str

    @property
    def market_confidence_label(self) -> str:
        """Richer market confidence label derived from spread."""
        if self.market_spread < 0.03:
            return "Split Market"
        elif self.market_spread < 0.08:
            return "Contested"
        else:
            return "Locked In"

    @property
    def quant_signal(self) -> str:
        """One-line quant signal for the game."""
        if self.ev_underdog > 0:
            return (
                f"+EV on the upset at {self.best_odds_underdog_source}"
                f" (EV: {self.ev_underdog:+.1%})"
            )
        if self.ev_favourite > 0.05:
            return (
                f"Strong +EV on {self.market_view.favourite} at"
                f" {self.best_odds_favourite_source} (EV: {self.ev_favourite:+.1%})"
            )
        if self.market_spread < 0.03:
            return "Market split — genuine coin flip, no edge here"
        if self.market_spread >= 0.08:
            return "Market locked in — no edge here"
        if self.max_value_discrepancy > 0.05:
            return (
                f"{self.discrepancy_source} disagrees with the field"
                f" (Δ{self.max_value_discrepancy:.1%})"
            )
        return "Market aligned — follow the consensus"


@dataclass
class RoundAnalysis:
    """Quant-derived analytics for an entire round."""

    round_number: int
    game_analyses: list[GameAnalysis]

    @property
    def round_volatility(self) -> float:
        """Average market spread — how uncertain is this round overall."""
        if not self.game_analyses:
            return 0.0
        return sum(ga.market_spread for ga in self.game_analyses) / len(self.game_analyses)

    @property
    def chalk_rate(self) -> float:
        """Percentage of games with a clear favourite (>60%)."""
        if not self.game_analyses:
            return 0.0
        chalk = sum(1 for ga in self.game_analyses if ga.market_view.favourite_prob > 0.60)
        return chalk / len(self.game_analyses)

    @property
    def upset_watch_count(self) -> int:
        """Games with genuine uncertainty (spread < 5%)."""
        return sum(1 for ga in self.game_analyses if ga.market_spread < 0.05)

    @property
    def round_difficulty_score(self) -> float:
        """Entropy-based difficulty: 1.0 = all coin flips, 0.0 = all certainties."""
        import math

        if not self.game_analyses:
            return 0.0
        total_entropy = 0.0
        for ga in self.game_analyses:
            p = ga.market_view.favourite_prob
            q = 1 - p
            if 0 < p < 1 and 0 < q < 1:
                # Normalised binary entropy (max entropy = 1.0 at p=0.5)
                h = -(p * math.log2(p) + q * math.log2(q))
                total_entropy += h
        return total_entropy / len(self.game_analyses)

    @property
    def difficulty_label(self) -> str:
        """Human-readable difficulty label."""
        score = self.round_difficulty_score
        if score >= 0.90:
            return "Minefield"
        elif score >= 0.75:
            return "Treacherous"
        elif score >= 0.55:
            return "Mixed Bag"
        else:
            return "Straightforward"

    @property
    def favourites_backed_count(self) -> int:
        """How many games have a clear favourite (>55%)."""
        return sum(1 for ga in self.game_analyses if ga.market_view.favourite_prob > 0.55)

    @property
    def portfolio_warning(self) -> str | None:
        """Warning when backing too many favourites."""
        total = len(self.game_analyses)
        if total == 0:
            return None
        backed = self.favourites_backed_count
        ratio = backed / total
        if ratio >= 0.875:  # 7/8 or higher
            return (
                f"You're backing {backed}/{total} favourites — one bad week kills you."
                " Consider a value upset pick."
            )
        return None


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
