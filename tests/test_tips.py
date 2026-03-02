"""Tests for ralph.tips — tip generation.

Each test class maps to one or more acceptance criteria from spec 03_get_ralphs_pick.md.
"""

from __future__ import annotations

from datetime import datetime

from ralph.models import Game, MarketView, Odds
from ralph.tips import generate_round_tips, generate_tip

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
    home: str = "Sydney Roosters",
    away: str = "Brisbane Broncos",
) -> MarketView:
    game = _game(home, away)
    return MarketView(
        game=game,
        odds_sources=[Odds(home_odds=1.80, away_odds=2.00, source="Test")],
        consensus_home_prob=home_prob,
        consensus_away_prob=away_prob,
    )


# ===========================================================================
# AC-01: Ralph picks the team with the higher consensus probability
# ===========================================================================


class TestAC01PickHigherProbability:
    def test_picks_home_when_home_prob_higher(self) -> None:
        """Home team at 72% should be picked."""
        mv = _market_view(0.72, 0.28)
        tip = generate_tip(mv)
        assert tip.pick == "Sydney Roosters"

    def test_picks_away_when_away_prob_higher(self) -> None:
        """Away team at 55% should be picked."""
        mv = _market_view(0.45, 0.55)
        tip = generate_tip(mv)
        assert tip.pick == "Brisbane Broncos"

    def test_picks_heavy_favourite(self) -> None:
        """A dominant favourite (85%) is picked."""
        mv = _market_view(0.85, 0.15)
        tip = generate_tip(mv)
        assert tip.pick == "Sydney Roosters"

    def test_picks_slight_away_favourite(self) -> None:
        """Slight away favourite at 52% is still picked."""
        mv = _market_view(0.48, 0.52)
        tip = generate_tip(mv)
        assert tip.pick == "Brisbane Broncos"


# ===========================================================================
# AC-02: Confidence equals the favourite's consensus probability
# ===========================================================================


class TestAC02ConfidenceEqualsFavouriteProb:
    def test_confidence_matches_home_favourite(self) -> None:
        mv = _market_view(0.72, 0.28)
        tip = generate_tip(mv)
        assert tip.confidence == 0.72

    def test_confidence_matches_away_favourite(self) -> None:
        mv = _market_view(0.45, 0.55)
        tip = generate_tip(mv)
        assert tip.confidence == 0.55

    def test_confidence_matches_coin_flip(self) -> None:
        mv = _market_view(0.51, 0.49)
        tip = generate_tip(mv)
        assert tip.confidence == 0.51


# ===========================================================================
# AC-03: Home team wins tiebreak when probabilities are exactly equal (50/50)
# ===========================================================================


class TestAC03HomeTiebreak:
    def test_exact_fifty_fifty_picks_home(self) -> None:
        mv = _market_view(0.50, 0.50)
        tip = generate_tip(mv)
        assert tip.pick == "Sydney Roosters"

    def test_exact_fifty_fifty_confidence_is_half(self) -> None:
        mv = _market_view(0.50, 0.50)
        tip = generate_tip(mv)
        assert tip.confidence == 0.50


# ===========================================================================
# AC-04: confidence = 0.72 -> confidence_label == "Lock"
# ===========================================================================


class TestAC04LockTier:
    def test_confidence_0_72_is_lock(self) -> None:
        mv = _market_view(0.72, 0.28)
        tip = generate_tip(mv)
        assert tip.confidence_label == "Lock"

    def test_high_lock_0_85(self) -> None:
        mv = _market_view(0.85, 0.15)
        tip = generate_tip(mv)
        assert tip.confidence_label == "Lock"


# ===========================================================================
# AC-05: confidence = 0.70 -> confidence_label == "Lock" (boundary inclusive)
# ===========================================================================


class TestAC05LockBoundaryInclusive:
    def test_confidence_exactly_0_70_is_lock(self) -> None:
        mv = _market_view(0.70, 0.30)
        tip = generate_tip(mv)
        assert tip.confidence_label == "Lock"


# ===========================================================================
# AC-06: confidence = 0.63 -> confidence_label == "Lean"
# ===========================================================================


class TestAC06LeanTier:
    def test_confidence_0_63_is_lean(self) -> None:
        mv = _market_view(0.63, 0.37)
        tip = generate_tip(mv)
        assert tip.confidence_label == "Lean"

    def test_confidence_0_65_is_lean(self) -> None:
        mv = _market_view(0.65, 0.35)
        tip = generate_tip(mv)
        assert tip.confidence_label == "Lean"


# ===========================================================================
# AC-07: confidence = 0.55 -> confidence_label == "Lean" (boundary inclusive)
# ===========================================================================


class TestAC07LeanBoundaryInclusive:
    def test_confidence_exactly_0_55_is_lean(self) -> None:
        mv = _market_view(0.55, 0.45)
        tip = generate_tip(mv)
        assert tip.confidence_label == "Lean"


# ===========================================================================
# AC-08: confidence = 0.54 -> confidence_label == "Coin Flip"
# ===========================================================================


class TestAC08CoinFlipJustBelow:
    def test_confidence_0_54_is_coin_flip(self) -> None:
        mv = _market_view(0.54, 0.46)
        tip = generate_tip(mv)
        assert tip.confidence_label == "Coin Flip"


# ===========================================================================
# AC-09: confidence = 0.50 -> confidence_label == "Coin Flip"
# ===========================================================================


class TestAC09CoinFlipLowest:
    def test_confidence_0_50_is_coin_flip(self) -> None:
        mv = _market_view(0.50, 0.50)
        tip = generate_tip(mv)
        assert tip.confidence_label == "Coin Flip"

    def test_confidence_0_51_is_coin_flip(self) -> None:
        mv = _market_view(0.51, 0.49)
        tip = generate_tip(mv)
        assert tip.confidence_label == "Coin Flip"


# ===========================================================================
# AC-10: 8 MarketViews -> RoundTips with exactly 8 Tip objects
# ===========================================================================


class TestAC10RoundTipsCount:
    def test_eight_market_views_produce_eight_tips(self) -> None:
        teams = [
            ("Sydney Roosters", "Brisbane Broncos"),
            ("Melbourne Storm", "Penrith Panthers"),
            ("South Sydney Rabbitohs", "Canterbury Bulldogs"),
            ("Manly Sea Eagles", "Cronulla Sharks"),
            ("Parramatta Eels", "North Queensland Cowboys"),
            ("Newcastle Knights", "Gold Coast Titans"),
            ("St George Illawarra Dragons", "Wests Tigers"),
            ("Canberra Raiders", "New Zealand Warriors"),
        ]
        market_views = [_market_view(0.60, 0.40, home=h, away=a) for h, a in teams]
        round_tips = generate_round_tips(market_views, round_number=1, season=2025)
        assert len(round_tips.tips) == 8
        assert round_tips.total_games == 8

    def test_two_market_views_produce_two_tips(self) -> None:
        mvs = [
            _market_view(0.60, 0.40),
            _market_view(0.45, 0.55, "Melbourne Storm", "Penrith Panthers"),
        ]
        round_tips = generate_round_tips(mvs, round_number=1, season=2025)
        assert len(round_tips.tips) == 2

    def test_round_number_and_season_are_set(self) -> None:
        mvs = [_market_view(0.60, 0.40)]
        round_tips = generate_round_tips(mvs, round_number=5, season=2026)
        assert round_tips.round_number == 5
        assert round_tips.season == 2026

    def test_empty_market_views_produces_zero_tips(self) -> None:
        round_tips = generate_round_tips([], round_number=1, season=2025)
        assert len(round_tips.tips) == 0


# ===========================================================================
# AC-11: Rationale is populated; teaching_moment on each Tip is empty string
# ===========================================================================


class TestAC11RationaleAndTeaching:
    def test_single_tip_has_populated_rationale(self) -> None:
        mv = _market_view(0.65, 0.35)
        tip = generate_tip(mv)
        assert tip.rationale != ""
        assert isinstance(tip.rationale, str)

    def test_single_tip_has_empty_teaching_moment(self) -> None:
        mv = _market_view(0.65, 0.35)
        tip = generate_tip(mv)
        assert tip.teaching_moment == ""

    def test_round_tips_have_populated_rationale(self) -> None:
        mvs = [_market_view(0.60, 0.40), _market_view(0.51, 0.49)]
        round_tips = generate_round_tips(mvs, round_number=1, season=2025)
        for tip in round_tips.tips:
            assert tip.rationale != ""
            assert tip.teaching_moment == ""

    def test_round_tips_teaching_moment_empty(self) -> None:
        mvs = [_market_view(0.60, 0.40)]
        round_tips = generate_round_tips(mvs, round_number=1, season=2025)
        assert round_tips.teaching_moment == ""


# ===========================================================================
# AC-12: RoundTips.generated_at is populated with the current datetime
# ===========================================================================


class TestAC12GeneratedAtPopulated:
    def test_generated_at_is_populated(self) -> None:
        before = datetime.now()
        mvs = [_market_view(0.60, 0.40)]
        round_tips = generate_round_tips(mvs, round_number=1, season=2025)
        after = datetime.now()

        assert round_tips.generated_at is not None
        assert isinstance(round_tips.generated_at, datetime)
        assert before <= round_tips.generated_at <= after


# ===========================================================================
# Determinism — same input always produces same output
# ===========================================================================


class TestDeterminism:
    def test_same_input_same_tip(self) -> None:
        """Two calls with identical input must produce identical picks."""
        mv = _market_view(0.63, 0.37)
        tip1 = generate_tip(mv)
        tip2 = generate_tip(mv)
        assert tip1.pick == tip2.pick
        assert tip1.confidence == tip2.confidence

    def test_tip_game_reference(self) -> None:
        """The Tip should reference the same Game as the MarketView."""
        mv = _market_view(0.60, 0.40)
        tip = generate_tip(mv)
        assert tip.game is mv.game
