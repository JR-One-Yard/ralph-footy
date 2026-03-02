"""Tests for ralph.models — data model correctness."""

from __future__ import annotations

from datetime import datetime

from ralph.models import Game, MarketView, Odds, RoundTips, Tip

# ---------------------------------------------------------------------------
# Game tests
# ---------------------------------------------------------------------------


class TestGame:
    def test_str_representation(self, sample_game: Game) -> None:
        assert str(sample_game) == "Sydney Roosters vs Brisbane Broncos (Allianz Stadium)"

    def test_fields(self, sample_game: Game) -> None:
        assert sample_game.home_team == "Sydney Roosters"
        assert sample_game.away_team == "Brisbane Broncos"
        assert sample_game.venue == "Allianz Stadium"
        assert sample_game.round_number == 1


# ---------------------------------------------------------------------------
# Odds tests
# ---------------------------------------------------------------------------


class TestOdds:
    def test_home_implied(self, sample_odds_sportsbet: Odds) -> None:
        assert round(sample_odds_sportsbet.home_implied, 4) == 0.6452

    def test_away_implied(self, sample_odds_sportsbet: Odds) -> None:
        assert round(sample_odds_sportsbet.away_implied, 4) == 0.4000

    def test_overround(self, sample_odds_sportsbet: Odds) -> None:
        assert sample_odds_sportsbet.overround > 0


# ---------------------------------------------------------------------------
# Tip confidence label tests (updated thresholds)
# ---------------------------------------------------------------------------


def _make_tip(game: Game, confidence: float) -> Tip:
    """Helper to build a Tip with only the confidence value varying."""
    return Tip(
        game=game,
        pick="Sydney Roosters",
        confidence=confidence,
        rationale="",
        teaching_moment="",
    )


class TestTipConfidenceLabel:
    def test_lock_above_threshold(self, sample_game: Game) -> None:
        assert _make_tip(sample_game, 0.72).confidence_label == "Lock"

    def test_lock_at_boundary(self, sample_game: Game) -> None:
        assert _make_tip(sample_game, 0.70).confidence_label == "Lock"

    def test_lean_mid_range(self, sample_game: Game) -> None:
        assert _make_tip(sample_game, 0.63).confidence_label == "Lean"

    def test_lean_at_boundary(self, sample_game: Game) -> None:
        assert _make_tip(sample_game, 0.55).confidence_label == "Lean"

    def test_coin_flip_just_below_lean(self, sample_game: Game) -> None:
        assert _make_tip(sample_game, 0.54).confidence_label == "Coin Flip"

    def test_coin_flip_at_fifty(self, sample_game: Game) -> None:
        assert _make_tip(sample_game, 0.50).confidence_label == "Coin Flip"

    def test_lock_from_fixture(self, sample_tip_lock: Tip) -> None:
        assert sample_tip_lock.confidence_label == "Lock"

    def test_lean_from_fixture(self, sample_tip_lean: Tip) -> None:
        assert sample_tip_lean.confidence_label == "Lean"

    def test_coin_flip_from_fixture(self, sample_tip_coin_flip: Tip) -> None:
        assert sample_tip_coin_flip.confidence_label == "Coin Flip"


# ---------------------------------------------------------------------------
# MarketView tests
# ---------------------------------------------------------------------------


class TestMarketView:
    def test_favourite_home(self, sample_market_view: MarketView) -> None:
        """When home probability is higher, favourite returns home team."""
        assert sample_market_view.favourite == "Sydney Roosters"

    def test_favourite_away(self, sample_game: Game, sample_odds_list: list[Odds]) -> None:
        """When away probability is higher, favourite returns away team."""
        mv = MarketView(
            game=sample_game,
            odds_sources=sample_odds_list,
            consensus_home_prob=0.40,
            consensus_away_prob=0.60,
        )
        assert mv.favourite == "Brisbane Broncos"

    def test_favourite_tiebreak_home(self, sample_game: Game, sample_odds_list: list[Odds]) -> None:
        """When probabilities are equal, favourite returns home team (tiebreak)."""
        mv = MarketView(
            game=sample_game,
            odds_sources=sample_odds_list,
            consensus_home_prob=0.50,
            consensus_away_prob=0.50,
        )
        assert mv.favourite == "Sydney Roosters"

    def test_favourite_prob_home(self, sample_market_view: MarketView) -> None:
        assert sample_market_view.favourite_prob == 0.6173

    def test_favourite_prob_away(self, sample_game: Game, sample_odds_list: list[Odds]) -> None:
        mv = MarketView(
            game=sample_game,
            odds_sources=sample_odds_list,
            consensus_home_prob=0.35,
            consensus_away_prob=0.65,
        )
        assert mv.favourite_prob == 0.65

    def test_favourite_prob_equal(self, sample_game: Game, sample_odds_list: list[Odds]) -> None:
        mv = MarketView(
            game=sample_game,
            odds_sources=sample_odds_list,
            consensus_home_prob=0.50,
            consensus_away_prob=0.50,
        )
        assert mv.favourite_prob == 0.50

    def test_odds_sources_stored(self, sample_market_view: MarketView) -> None:
        assert len(sample_market_view.odds_sources) == 2
        assert sample_market_view.odds_sources[0].source == "Sportsbet"
        assert sample_market_view.odds_sources[1].source == "TAB"


# ---------------------------------------------------------------------------
# RoundTips tests
# ---------------------------------------------------------------------------


class TestRoundTips:
    def test_total_games(self, sample_round_tips: RoundTips) -> None:
        assert sample_round_tips.total_games == 2

    def test_teaching_moment_default(self) -> None:
        rt = RoundTips(round_number=1, season=2025)
        assert rt.teaching_moment == ""

    def test_teaching_moment_set(self) -> None:
        rt = RoundTips(
            round_number=1,
            season=2025,
            teaching_moment="Implied probability is 1 divided by the decimal odds.",
        )
        assert "Implied probability" in rt.teaching_moment

    def test_generated_at_populated(self) -> None:
        rt = RoundTips(round_number=1, season=2025)
        assert isinstance(rt.generated_at, datetime)

    def test_fields(self, sample_round_tips: RoundTips) -> None:
        assert sample_round_tips.round_number == 1
        assert sample_round_tips.season == 2025
        assert len(sample_round_tips.tips) == 2
