"""Tests for ralph.quant — quant analysis engine.

Tests the per-game and per-round analytics derived from bookmaker odds.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from ralph.models import Game, MarketView, Odds
from ralph.quant import (
    _expected_value,
    _kelly_fraction,
    _market_spread,
    _value_discrepancy,
    analyse_game,
    analyse_round,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _game(
    home: str = "Sydney Roosters",
    away: str = "Brisbane Broncos",
) -> Game:
    return Game(
        home_team=home,
        away_team=away,
        venue="Test Stadium",
        kickoff=datetime(2025, 3, 6, 20, 0),
        round_number=1,
    )


def _market_view(
    home_prob: float,
    away_prob: float,
    odds_sources: list[Odds] | None = None,
    home: str = "Sydney Roosters",
    away: str = "Brisbane Broncos",
) -> MarketView:
    game = _game(home, away)
    if odds_sources is None:
        odds_sources = [
            Odds(home_odds=1.55, away_odds=2.50, source="Sportsbet"),
            Odds(home_odds=1.52, away_odds=2.55, source="TAB"),
        ]
    return MarketView(
        game=game,
        odds_sources=odds_sources,
        consensus_home_prob=home_prob,
        consensus_away_prob=away_prob,
    )


# ===========================================================================
# Expected Value
# ===========================================================================


class TestExpectedValue:
    def test_positive_ev(self) -> None:
        """EV > 0 when probability × odds > 1."""
        # prob=0.60, odds=2.00 -> EV = 0.60×2.0 - 1 = 0.20
        assert _expected_value(0.60, 2.00) == pytest.approx(0.20)

    def test_negative_ev(self) -> None:
        """EV < 0 when probability × odds < 1."""
        # prob=0.40, odds=2.00 -> EV = 0.40×2.0 - 1 = -0.20
        assert _expected_value(0.40, 2.00) == pytest.approx(-0.20)

    def test_zero_odds(self) -> None:
        assert _expected_value(0.50, 0.0) == 0.0


# ===========================================================================
# Kelly Fraction
# ===========================================================================


class TestKellyFraction:
    def test_positive_kelly(self) -> None:
        """Kelly > 0 when there's a positive edge."""
        # prob=0.60, odds=2.50 -> b=1.5, f=(1.5×0.6-0.4)/1.5 = 0.50/1.5 = 0.333
        f = _kelly_fraction(0.60, 2.50)
        assert f == pytest.approx(1 / 3, abs=0.01)

    def test_negative_kelly_clamps_to_zero(self) -> None:
        """Kelly < 0 should be clamped to 0 (no bet)."""
        # prob=0.30, odds=2.00 -> b=1.0, f=(1.0×0.3-0.7)/1.0 = -0.4 -> 0
        assert _kelly_fraction(0.30, 2.00) == 0.0

    def test_zero_prob(self) -> None:
        assert _kelly_fraction(0.0, 2.00) == 0.0

    def test_odds_at_one(self) -> None:
        assert _kelly_fraction(0.50, 1.00) == 0.0


# ===========================================================================
# Market Spread
# ===========================================================================


class TestMarketSpread:
    def test_spread_with_two_bookmakers(self) -> None:
        """Spread between two bookmakers with different home odds."""
        mv = _market_view(0.62, 0.38)
        spread = _market_spread(mv)
        # Sportsbet home implied: 1/1.55 = 0.6452
        # TAB home implied: 1/1.52 = 0.6579
        # Spread = 0.6579 - 0.6452 = 0.0127
        assert spread == pytest.approx(0.0127, abs=0.001)

    def test_spread_with_single_bookmaker(self) -> None:
        """Single bookmaker -> spread is 0."""
        mv = _market_view(
            0.62, 0.38,
            odds_sources=[Odds(home_odds=1.55, away_odds=2.50, source="Sportsbet")],
        )
        assert _market_spread(mv) == 0.0

    def test_spread_with_no_sources(self) -> None:
        mv = _market_view(0.50, 0.50, odds_sources=[])
        assert _market_spread(mv) == 0.0


# ===========================================================================
# Value Discrepancy
# ===========================================================================


class TestValueDiscrepancy:
    def test_discrepancy_with_matching_bookmakers(self) -> None:
        """Close odds across bookmakers -> small discrepancy."""
        mv = _market_view(0.62, 0.38)
        disc, source = _value_discrepancy(mv)
        assert disc >= 0
        assert source in ("Sportsbet", "TAB")

    def test_discrepancy_with_no_sources(self) -> None:
        mv = _market_view(0.50, 0.50, odds_sources=[])
        disc, source = _value_discrepancy(mv)
        assert disc == 0.0


# ===========================================================================
# analyse_game
# ===========================================================================


class TestAnalyseGame:
    def test_returns_game_analysis(self) -> None:
        mv = _market_view(0.62, 0.38)
        ga = analyse_game(mv)
        assert ga.market_view is mv
        assert ga.market_spread >= 0
        assert isinstance(ga.ev_favourite, float)
        assert isinstance(ga.kelly_favourite, float)
        assert ga.best_odds_favourite_source in ("Sportsbet", "TAB")
        assert ga.best_odds_underdog_source in ("Sportsbet", "TAB")

    def test_overrounds_populated(self) -> None:
        mv = _market_view(0.62, 0.38)
        ga = analyse_game(mv)
        assert "Sportsbet" in ga.overrounds
        assert "TAB" in ga.overrounds
        assert all(v > 0 for v in ga.overrounds.values())

    def test_market_confidence_label_locked_in(self) -> None:
        """High spread -> Locked In."""
        odds = [
            Odds(home_odds=1.30, away_odds=3.50, source="A"),
            Odds(home_odds=1.50, away_odds=2.50, source="B"),
        ]
        mv = _market_view(0.70, 0.30, odds_sources=odds)
        ga = analyse_game(mv)
        # 1/1.30=0.769, 1/1.50=0.667 -> spread=0.103 > 0.08 -> Locked In
        assert ga.market_confidence_label == "Locked In"

    def test_market_confidence_label_split(self) -> None:
        """Tiny spread -> Split Market."""
        odds = [
            Odds(home_odds=1.91, away_odds=1.91, source="A"),
            Odds(home_odds=1.90, away_odds=1.92, source="B"),
        ]
        mv = _market_view(0.51, 0.49, odds_sources=odds)
        ga = analyse_game(mv)
        # 1/1.91=0.5236, 1/1.90=0.5263 -> spread=0.003 < 0.03 -> Split
        assert ga.market_confidence_label == "Split Market"

    def test_quant_signal_not_empty(self) -> None:
        mv = _market_view(0.62, 0.38)
        ga = analyse_game(mv)
        assert len(ga.quant_signal) > 0


# ===========================================================================
# analyse_round
# ===========================================================================


class TestAnalyseRound:
    def _make_round(self, n_games: int = 8) -> list[MarketView]:
        teams = [
            ("Sydney Roosters", "Brisbane Broncos", 0.62, 0.38),
            ("Melbourne Storm", "Penrith Panthers", 0.51, 0.49),
            ("South Sydney Rabbitohs", "Canterbury Bulldogs", 0.72, 0.28),
            ("Manly Sea Eagles", "Cronulla Sharks", 0.58, 0.42),
            ("Parramatta Eels", "North Queensland Cowboys", 0.55, 0.45),
            ("Newcastle Knights", "Gold Coast Titans", 0.65, 0.35),
            ("St George Illawarra Dragons", "Wests Tigers", 0.80, 0.20),
            ("Canberra Raiders", "New Zealand Warriors", 0.52, 0.48),
        ]
        return [_market_view(hp, ap, home=h, away=a) for h, a, hp, ap in teams[:n_games]]

    def test_round_analysis_contains_all_games(self) -> None:
        mvs = self._make_round()
        ra = analyse_round(mvs, round_number=1)
        assert len(ra.game_analyses) == 8
        assert ra.round_number == 1

    def test_round_volatility(self) -> None:
        mvs = self._make_round()
        ra = analyse_round(mvs, round_number=1)
        assert 0 <= ra.round_volatility <= 1.0

    def test_chalk_rate(self) -> None:
        mvs = self._make_round()
        ra = analyse_round(mvs, round_number=1)
        # Games with >60%: Roosters(62), Rabbitohs(72), Knights(65), Dragons(80) = 4/8 = 50%
        assert ra.chalk_rate == pytest.approx(0.5)

    def test_upset_watch_count(self) -> None:
        mvs = self._make_round()
        ra = analyse_round(mvs, round_number=1)
        # All games use same 2 bookmakers with similar odds, so spread is small
        # Most will have spread < 5%
        assert ra.upset_watch_count >= 0

    def test_difficulty_score_range(self) -> None:
        mvs = self._make_round()
        ra = analyse_round(mvs, round_number=1)
        assert 0 <= ra.round_difficulty_score <= 1.0

    def test_difficulty_label(self) -> None:
        mvs = self._make_round()
        ra = analyse_round(mvs, round_number=1)
        assert ra.difficulty_label in (
            "Straightforward", "Mixed Bag", "Treacherous", "Minefield"
        )

    def test_portfolio_warning_when_all_favourites(self) -> None:
        """All clear favourites -> portfolio warning."""
        mvs = [_market_view(0.70, 0.30, home=f"Team {i}", away=f"Team {i+10}") for i in range(8)]
        ra = analyse_round(mvs, round_number=1)
        assert ra.portfolio_warning is not None
        assert "favourites" in ra.portfolio_warning

    def test_no_portfolio_warning_with_mixed_picks(self) -> None:
        """Mix of favourites and coin flips -> no warning."""
        mvs = [
            _market_view(0.70, 0.30, home="A", away="B"),
            _market_view(0.51, 0.49, home="C", away="D"),
            _market_view(0.52, 0.48, home="E", away="F"),
            _market_view(0.50, 0.50, home="G", away="H"),
        ]
        ra = analyse_round(mvs, round_number=1)
        assert ra.portfolio_warning is None

    def test_empty_round(self) -> None:
        ra = analyse_round([], round_number=1)
        assert len(ra.game_analyses) == 0
        assert ra.round_volatility == 0.0
        assert ra.chalk_rate == 0.0
        assert ra.round_difficulty_score == 0.0


