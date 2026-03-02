"""Tests for ralph.market — market consensus engine.

Each test maps to one or more acceptance criteria from spec 02_see_market_odds.md.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from ralph.market import (
    build_market_views,
    market_consensus,
    odds_to_implied_probability,
    remove_overround,
)
from ralph.models import Game, MarketView, Odds

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _game(home: str = "Sydney Roosters", away: str = "Brisbane Broncos") -> Game:
    return Game(
        home_team=home,
        away_team=away,
        venue="Test Stadium",
        kickoff=datetime(2025, 3, 6, 20, 0),
        round_number=1,
    )


# ===========================================================================
# AC-01: odds_to_implied_probability(1.55) returns 0.6452 (4dp)
# ===========================================================================


class TestAC01OddsToImpliedProbability:
    def test_home_odds_1_55(self) -> None:
        assert round(odds_to_implied_probability(1.55), 4) == 0.6452

    def test_away_odds_2_50(self) -> None:
        assert round(odds_to_implied_probability(2.50), 4) == 0.4000

    def test_even_money(self) -> None:
        """Odds of $2.00 should give exactly 0.5."""
        assert odds_to_implied_probability(2.0) == 0.5

    def test_heavy_favourite(self) -> None:
        """Odds of $1.10 should give ~0.9091."""
        assert round(odds_to_implied_probability(1.10), 4) == 0.9091

    def test_long_shot(self) -> None:
        """Odds of $10.00 should give exactly 0.1."""
        assert odds_to_implied_probability(10.0) == 0.1


# ===========================================================================
# AC-02: remove_overround(0.6452, 0.4000) returns (0.6173, 0.3827) (4dp)
# ===========================================================================


class TestAC02RemoveOverround:
    def test_spec_example(self) -> None:
        home, away = remove_overround(0.6452, 0.4000)
        assert round(home, 4) == 0.6173
        assert round(away, 4) == 0.3827

    def test_equal_implied(self) -> None:
        """When both sides have equal implied probs, result is 50/50."""
        home, away = remove_overround(0.5263, 0.5263)
        assert round(home, 4) == 0.5
        assert round(away, 4) == 0.5


# ===========================================================================
# AC-03: Output of remove_overround sums to exactly 1.0 (within 1e-9)
# ===========================================================================


class TestAC03OverroundSumsToOne:
    def test_spec_example_sums_to_one(self) -> None:
        home, away = remove_overround(0.6452, 0.4000)
        assert abs((home + away) - 1.0) < 1e-9

    def test_arbitrary_values_sum_to_one(self) -> None:
        home, away = remove_overround(0.55, 0.50)
        assert abs((home + away) - 1.0) < 1e-9

    def test_extreme_favourite_sums_to_one(self) -> None:
        home, away = remove_overround(0.95, 0.10)
        assert abs((home + away) - 1.0) < 1e-9

    def test_near_even_sums_to_one(self) -> None:
        home, away = remove_overround(0.5263, 0.5000)
        assert abs((home + away) - 1.0) < 1e-9


# ===========================================================================
# AC-04: market_consensus with two bookmakers returns mean, re-normalised
# ===========================================================================


class TestAC04ConsensusMultipleBookmakers:
    def test_two_bookmakers(self) -> None:
        """Sportsbet: $1.55/$2.50, TAB: $1.52/$2.55."""
        odds_list = [
            Odds(home_odds=1.55, away_odds=2.50, source="Sportsbet"),
            Odds(home_odds=1.52, away_odds=2.55, source="TAB"),
        ]
        home, away = market_consensus(odds_list)

        # Result should sum to 1.0
        assert abs((home + away) - 1.0) < 1e-9

        # Home should be the clear favourite (> 0.60)
        assert home > 0.60

        # Manually verify the maths:
        # Sportsbet: implied = (0.6452, 0.4000), overround removed = (0.6173, 0.3827)
        # TAB:       implied = (0.6579, 0.3922), overround removed = (0.6265, 0.3735)
        # Average:   (0.6219, 0.3781)
        # Re-normalise: already sums to 1.0
        assert round(home, 4) == 0.6219
        assert round(away, 4) == 0.3781

    def test_three_bookmakers(self) -> None:
        odds_list = [
            Odds(home_odds=1.55, away_odds=2.50, source="Sportsbet"),
            Odds(home_odds=1.52, away_odds=2.55, source="TAB"),
            Odds(home_odds=1.57, away_odds=2.45, source="Ladbrokes"),
        ]
        home, away = market_consensus(odds_list)
        assert abs((home + away) - 1.0) < 1e-9
        # All three favour home, so home should be > 0.60
        assert home > 0.60


# ===========================================================================
# AC-05: Single bookmaker returns overround-removed probs (no averaging)
# ===========================================================================


class TestAC05SingleBookmaker:
    def test_single_source(self) -> None:
        odds_list = [Odds(home_odds=1.55, away_odds=2.50, source="Sportsbet")]
        home, away = market_consensus(odds_list)

        # Should match remove_overround result for that bookmaker
        expected_home, expected_away = remove_overround(
            odds_to_implied_probability(1.55),
            odds_to_implied_probability(2.50),
        )
        assert abs(home - expected_home) < 1e-9
        assert abs(away - expected_away) < 1e-9
        assert abs((home + away) - 1.0) < 1e-9


# ===========================================================================
# AC-06: home_odds <= 1.0 raises ValueError
# ===========================================================================


class TestAC06InvalidHomeOdds:
    def test_home_odds_one(self) -> None:
        with pytest.raises(ValueError, match="greater than 1.0"):
            odds_to_implied_probability(1.0)

    def test_home_odds_zero(self) -> None:
        with pytest.raises(ValueError, match="greater than 1.0"):
            odds_to_implied_probability(0.0)

    def test_home_odds_negative(self) -> None:
        with pytest.raises(ValueError, match="greater than 1.0"):
            odds_to_implied_probability(-1.5)

    def test_home_odds_below_one(self) -> None:
        with pytest.raises(ValueError, match="greater than 1.0"):
            odds_to_implied_probability(0.95)


# ===========================================================================
# AC-07: away_odds <= 1.0 raises ValueError
# ===========================================================================


class TestAC07InvalidAwayOdds:
    def test_away_odds_through_consensus(self) -> None:
        """Verify that invalid away odds are caught via the market_consensus path."""
        odds_list = [Odds(home_odds=1.55, away_odds=0.80, source="Dodgy")]
        with pytest.raises(ValueError, match="greater than 1.0"):
            market_consensus(odds_list)

    def test_away_odds_one_exactly(self) -> None:
        with pytest.raises(ValueError, match="greater than 1.0"):
            odds_to_implied_probability(1.0)

    def test_away_odds_below_one(self) -> None:
        with pytest.raises(ValueError, match="greater than 1.0"):
            odds_to_implied_probability(0.5)


# ===========================================================================
# AC-08: Fixture missing odds array raises ValueError
# (This is tested via fixtures.py validation — included here for completeness)
# ===========================================================================


class TestAC08MissingOddsField:
    def test_build_market_views_no_odds_defaults_to_fifty_fifty(self) -> None:
        """Games without odds get a default 50/50 market view."""
        game = _game()
        views = build_market_views([game], {})
        assert len(views) == 1
        assert views[0].consensus_home_prob == 0.5
        assert views[0].consensus_away_prob == 0.5

    def test_build_market_views_empty_odds_list(self) -> None:
        """An empty odds list for a game key also defaults to 50/50."""
        game = _game()
        odds_map = {"Sydney Roosters v Brisbane Broncos": []}
        views = build_market_views([game], odds_map)
        assert views[0].consensus_home_prob == 0.5
        assert views[0].consensus_away_prob == 0.5


# ===========================================================================
# AC-09: Odds entry missing source/home_odds/away_odds raises ValueError
# (Validated by fixtures.py — see test_fixtures.py::TestOddsValidation)
# ===========================================================================


class TestAC09OddsEntryValidation:
    def test_market_consensus_empty_list_raises(self) -> None:
        """market_consensus requires at least one bookmaker."""
        with pytest.raises(ValueError, match="at least one bookmaker"):
            market_consensus([])


# ===========================================================================
# AC-10: MarketView correctly computes favourite and favourite_prob
# ===========================================================================


class TestAC10MarketViewProperties:
    def test_favourite_is_home_when_home_prob_higher(self) -> None:
        game = _game()
        mv = MarketView(
            game=game,
            odds_sources=[],
            consensus_home_prob=0.6173,
            consensus_away_prob=0.3827,
        )
        assert mv.favourite == "Sydney Roosters"
        assert mv.favourite_prob == 0.6173

    def test_favourite_is_away_when_away_prob_higher(self) -> None:
        game = _game()
        mv = MarketView(
            game=game,
            odds_sources=[],
            consensus_home_prob=0.35,
            consensus_away_prob=0.65,
        )
        assert mv.favourite == "Brisbane Broncos"
        assert mv.favourite_prob == 0.65

    def test_favourite_tiebreak_home(self) -> None:
        """When probabilities are equal (50/50), favourite defaults to home team."""
        game = _game()
        mv = MarketView(
            game=game,
            odds_sources=[],
            consensus_home_prob=0.50,
            consensus_away_prob=0.50,
        )
        assert mv.favourite == "Sydney Roosters"
        assert mv.favourite_prob == 0.50


# ===========================================================================
# build_market_views integration tests
# ===========================================================================


class TestBuildMarketViews:
    def test_builds_one_view_per_game(self) -> None:
        game1 = _game("Sydney Roosters", "Brisbane Broncos")
        game2 = _game("Melbourne Storm", "Penrith Panthers")
        odds_map = {
            "Sydney Roosters v Brisbane Broncos": [
                Odds(home_odds=1.55, away_odds=2.50, source="Sportsbet"),
            ],
            "Melbourne Storm v Penrith Panthers": [
                Odds(home_odds=1.90, away_odds=1.90, source="Sportsbet"),
            ],
        }
        views = build_market_views([game1, game2], odds_map)
        assert len(views) == 2
        assert all(isinstance(v, MarketView) for v in views)

    def test_market_view_has_correct_game(self) -> None:
        game = _game()
        odds_map = {
            "Sydney Roosters v Brisbane Broncos": [
                Odds(home_odds=1.55, away_odds=2.50, source="Sportsbet"),
            ],
        }
        views = build_market_views([game], odds_map)
        assert views[0].game is game

    def test_market_view_stores_odds_sources(self) -> None:
        game = _game()
        odds_list = [
            Odds(home_odds=1.55, away_odds=2.50, source="Sportsbet"),
            Odds(home_odds=1.52, away_odds=2.55, source="TAB"),
        ]
        odds_map = {"Sydney Roosters v Brisbane Broncos": odds_list}
        views = build_market_views([game], odds_map)
        assert views[0].odds_sources == odds_list

    def test_mixed_games_with_and_without_odds(self) -> None:
        game1 = _game("Sydney Roosters", "Brisbane Broncos")
        game2 = _game("Melbourne Storm", "Penrith Panthers")
        odds_map = {
            "Sydney Roosters v Brisbane Broncos": [
                Odds(home_odds=1.55, away_odds=2.50, source="Sportsbet"),
            ],
            # No odds for Storm v Panthers
        }
        views = build_market_views([game1, game2], odds_map)
        assert len(views) == 2
        # First game has real odds
        assert views[0].consensus_home_prob > 0.6
        # Second game defaults to 50/50
        assert views[1].consensus_home_prob == 0.5
        assert views[1].consensus_away_prob == 0.5


# ===========================================================================
# remove_overround input validation
# ===========================================================================


class TestRemoveOverroundValidation:
    def test_negative_home_implied_raises(self) -> None:
        with pytest.raises(ValueError, match="home_implied"):
            remove_overround(-0.1, 0.5)

    def test_zero_home_implied_raises(self) -> None:
        with pytest.raises(ValueError, match="home_implied"):
            remove_overround(0.0, 0.5)

    def test_negative_away_implied_raises(self) -> None:
        with pytest.raises(ValueError, match="away_implied"):
            remove_overround(0.5, -0.1)

    def test_zero_away_implied_raises(self) -> None:
        with pytest.raises(ValueError, match="away_implied"):
            remove_overround(0.5, 0.0)

    def test_home_implied_above_one_raises(self) -> None:
        with pytest.raises(ValueError, match="home_implied"):
            remove_overround(1.1, 0.5)

    def test_away_implied_above_one_raises(self) -> None:
        with pytest.raises(ValueError, match="away_implied"):
            remove_overround(0.5, 1.1)
