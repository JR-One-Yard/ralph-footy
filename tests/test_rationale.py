"""Tests for ralph.rationale — rationale generation.

Tests the enriched template fallback mode (offline). API-driven rationale
is tested separately via integration tests.
"""

from __future__ import annotations

from datetime import datetime

from ralph.models import Game, MarketView, Odds, Tip
from ralph.quant import analyse_game
from ralph.rationale import (
    COIN_FLIP_TEMPLATES,
    LEAN_TEMPLATES,
    LOCK_TEMPLATES,
    generate_rationale,
    generate_rationale_template,
    team_short_name,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _game(
    home: str = "Sydney Roosters",
    away: str = "Brisbane Broncos",
    venue: str = "Allianz Stadium",
) -> Game:
    return Game(
        home_team=home,
        away_team=away,
        venue=venue,
        kickoff=datetime(2025, 3, 6, 20, 0),
        round_number=1,
    )


def _odds(
    home_odds: float = 1.55,
    away_odds: float = 2.50,
    source: str = "Sportsbet",
) -> Odds:
    return Odds(home_odds=home_odds, away_odds=away_odds, source=source)


def _market_view(
    home_prob: float,
    away_prob: float,
    home: str = "Sydney Roosters",
    away: str = "Brisbane Broncos",
    venue: str = "Allianz Stadium",
    odds_sources: list[Odds] | None = None,
) -> MarketView:
    game = _game(home, away, venue)
    if odds_sources is None:
        odds_sources = [
            _odds(1.55, 2.50, "Sportsbet"),
            _odds(1.52, 2.55, "TAB"),
        ]
    return MarketView(
        game=game,
        odds_sources=odds_sources,
        consensus_home_prob=home_prob,
        consensus_away_prob=away_prob,
    )


def _tip(
    pick: str,
    confidence: float,
    home: str = "Sydney Roosters",
    away: str = "Brisbane Broncos",
    venue: str = "Allianz Stadium",
) -> Tip:
    game = _game(home, away, venue)
    return Tip(
        game=game,
        pick=pick,
        confidence=confidence,
        rationale="",
        teaching_moment="",
    )


# ===========================================================================
# AC-01: Lock-tier tip uses a Lock template and contains the picked team
#         name and the probability percentage.
# ===========================================================================


class TestAC01LockTemplate:
    """Lock-tier tip (confidence >= 0.70) uses a Lock template."""

    def test_lock_rationale_contains_pick_name(self) -> None:
        tip = _tip("Sydney Roosters", 0.75)
        mv = _market_view(0.75, 0.25)
        rationale = generate_rationale(tip, mv, game_index=0, offline=True)
        assert "Roosters" in rationale

    def test_lock_rationale_contains_probability(self) -> None:
        tip = _tip("Sydney Roosters", 0.75)
        mv = _market_view(0.75, 0.25)
        rationale = generate_rationale(tip, mv, game_index=0, offline=True)
        assert "75%" in rationale

    def test_lock_rationale_uses_lock_template(self) -> None:
        """The generated rationale should use a Lock-tier template."""
        tip = _tip("Sydney Roosters", 0.75)
        mv = _market_view(0.75, 0.25)
        rationale = generate_rationale(tip, mv, game_index=0, offline=True)
        # Lock template 0 starts with "The {pick} at {pick_prob_pct}"
        assert "as close to a certainty" in rationale

    def test_lock_boundary_at_0_70(self) -> None:
        """Exactly 0.70 confidence is Lock tier."""
        tip = _tip("Sydney Roosters", 0.70)
        mv = _market_view(0.70, 0.30)
        rationale = generate_rationale(tip, mv, game_index=0, offline=True)
        assert "70%" in rationale
        assert "as close to a certainty" in rationale

    def test_four_lock_templates_exist(self) -> None:
        assert len(LOCK_TEMPLATES) == 4


# ===========================================================================
# AC-02: Lean-tier tip uses a Lean template.
# ===========================================================================


class TestAC02LeanTemplate:
    """Lean-tier tip (0.55 <= confidence < 0.70) uses a Lean template."""

    def test_lean_rationale_uses_lean_template(self) -> None:
        tip = _tip("Sydney Roosters", 0.62)
        mv = _market_view(0.62, 0.38)
        rationale = generate_rationale(tip, mv, game_index=0, offline=True)
        # Lean template 0 contains "capable of making this uncomfortable"
        assert "Roosters" in rationale
        assert "62%" in rationale

    def test_lean_rationale_contains_pick_name(self) -> None:
        tip = _tip("Sydney Roosters", 0.62)
        mv = _market_view(0.62, 0.38)
        rationale = generate_rationale(tip, mv, game_index=0, offline=True)
        assert "Roosters" in rationale

    def test_lean_rationale_contains_probability(self) -> None:
        tip = _tip("Sydney Roosters", 0.62)
        mv = _market_view(0.62, 0.38)
        rationale = generate_rationale(tip, mv, game_index=0, offline=True)
        assert "62%" in rationale

    def test_lean_boundary_at_0_55(self) -> None:
        """Exactly 0.55 confidence is Lean tier."""
        tip = _tip("Sydney Roosters", 0.55)
        mv = _market_view(0.55, 0.45)
        rationale = generate_rationale(tip, mv, game_index=0, offline=True)
        assert "55%" in rationale
        assert "Roosters" in rationale

    def test_four_lean_templates_exist(self) -> None:
        assert len(LEAN_TEMPLATES) == 4


# ===========================================================================
# AC-03: Coin Flip-tier tip uses a Coin Flip template.
# ===========================================================================


class TestAC03CoinFlipTemplate:
    """Coin Flip-tier tip (confidence < 0.55) uses a Coin Flip template."""

    def test_coin_flip_rationale_uses_coin_flip_template(self) -> None:
        tip = _tip("Sydney Roosters", 0.52)
        mv = _market_view(0.52, 0.48)
        rationale = generate_rationale(tip, mv, game_index=0, offline=True)
        # Coin flip template 0 contains "spread means the market genuinely cannot separate"
        assert "market genuinely cannot separate" in rationale

    def test_coin_flip_rationale_contains_pick_name(self) -> None:
        tip = _tip("Sydney Roosters", 0.52)
        mv = _market_view(0.52, 0.48)
        rationale = generate_rationale(tip, mv, game_index=0, offline=True)
        assert "Roosters" in rationale

    def test_coin_flip_rationale_contains_probability(self) -> None:
        tip = _tip("Sydney Roosters", 0.52)
        mv = _market_view(0.52, 0.48)
        rationale = generate_rationale(tip, mv, game_index=0, offline=True)
        assert "52%" in rationale

    def test_coin_flip_at_0_50(self) -> None:
        """Exactly 0.50 confidence is Coin Flip tier."""
        tip = _tip("Sydney Roosters", 0.50)
        mv = _market_view(0.50, 0.50)
        rationale = generate_rationale(tip, mv, game_index=0, offline=True)
        assert "50%" in rationale

    def test_four_coin_flip_templates_exist(self) -> None:
        assert len(COIN_FLIP_TEMPLATES) == 4


# ===========================================================================
# AC-04: No two games in the same round get identical rationale
#         (template rotation ensures variety).
# ===========================================================================


class TestAC04TemplateRotationVariety:
    """No rationale template produces identical output for two different games."""

    def test_same_tier_different_games_different_rationale(self) -> None:
        """Two Lean-tier games at different indices get different text."""
        tip0 = _tip("Sydney Roosters", 0.62)
        mv0 = _market_view(0.62, 0.38)
        tip1 = _tip("Melbourne Storm", 0.65, home="Melbourne Storm", away="Penrith Panthers")
        mv1 = _market_view(
            0.65,
            0.35,
            home="Melbourne Storm",
            away="Penrith Panthers",
            venue="AAMI Park",
        )
        r0 = generate_rationale(tip0, mv0, game_index=0, offline=True)
        r1 = generate_rationale(tip1, mv1, game_index=1, offline=True)
        assert r0 != r1

    def test_same_teams_different_indices_different_rationale(self) -> None:
        """Even identical teams at different indices get different templates."""
        tip = _tip("Sydney Roosters", 0.62)
        mv = _market_view(0.62, 0.38)
        r0 = generate_rationale(tip, mv, game_index=0, offline=True)
        r1 = generate_rationale(tip, mv, game_index=1, offline=True)
        assert r0 != r1

    def test_eight_game_round_all_unique(self) -> None:
        """A full 8-game round produces 8 unique rationales."""
        teams = [
            ("Sydney Roosters", "Brisbane Broncos", 0.62, 0.38),
            ("Melbourne Storm", "Penrith Panthers", 0.58, 0.42),
            ("South Sydney Rabbitohs", "Canterbury Bulldogs", 0.72, 0.28),
            ("Manly Sea Eagles", "Cronulla Sharks", 0.66, 0.34),
            ("Parramatta Eels", "North Queensland Cowboys", 0.51, 0.49),
            ("Newcastle Knights", "Gold Coast Titans", 0.60, 0.40),
            ("St George Illawarra Dragons", "Wests Tigers", 0.80, 0.20),
            ("Canberra Raiders", "New Zealand Warriors", 0.54, 0.46),
        ]
        rationales = []
        for i, (home, away, hp, ap) in enumerate(teams):
            tip = _tip(home, hp, home=home, away=away)
            mv = _market_view(hp, ap, home=home, away=away)
            rationales.append(generate_rationale(tip, mv, game_index=i, offline=True))
        assert len(set(rationales)) == 8

    def test_rotation_wraps_around(self) -> None:
        """Template selection wraps: index 4 uses same template as index 0."""
        tip = _tip("Sydney Roosters", 0.62)
        mv = _market_view(0.62, 0.38)
        r0 = generate_rationale(tip, mv, game_index=0, offline=True)
        r4 = generate_rationale(tip, mv, game_index=4, offline=True)
        # Same template, same data => same output
        assert r0 == r4


# ===========================================================================
# AC-05: Every rationale contains the actual probability percentage
#         (not a placeholder like {pick_prob_pct}).
# ===========================================================================


class TestAC05ActualProbabilityInOutput:
    """Every rationale contains the actual probability, no unresolved placeholders."""

    def test_no_unresolved_placeholders(self) -> None:
        """Rationale should not contain any {variable} placeholders."""
        tip = _tip("Sydney Roosters", 0.65)
        mv = _market_view(0.65, 0.35)
        rationale = generate_rationale(tip, mv, game_index=0, offline=True)
        assert "{" not in rationale
        assert "}" not in rationale

    def test_all_tiers_have_no_placeholders(self) -> None:
        """Check all three tiers for unresolved placeholders."""
        configs = [
            ("Sydney Roosters", 0.75, 0.75, 0.25),  # Lock
            ("Sydney Roosters", 0.62, 0.62, 0.38),  # Lean
            ("Sydney Roosters", 0.52, 0.52, 0.48),  # Coin Flip
        ]
        for pick, conf, hp, ap in configs:
            tip = _tip(pick, conf)
            mv = _market_view(hp, ap)
            for idx in range(4):
                rationale = generate_rationale(tip, mv, game_index=idx, offline=True)
                assert "{" not in rationale, (
                    f"Unresolved placeholder at tier={tip.confidence_label}, idx={idx}"
                )
                assert "}" not in rationale

    def test_probability_appears_as_percentage(self) -> None:
        """The probability should appear as 'NN%' in the output."""
        tip = _tip("Sydney Roosters", 0.62)
        mv = _market_view(0.62, 0.38)
        rationale = generate_rationale(tip, mv, game_index=0, offline=True)
        assert "62%" in rationale


# ===========================================================================
# AC-06: Every rationale contains the picked team's short name (mascot).
# ===========================================================================


class TestAC06PickedTeamShortName:
    """Every rationale contains the picked team's short name."""

    def test_home_pick_short_name_in_rationale(self) -> None:
        tip = _tip("Sydney Roosters", 0.62)
        mv = _market_view(0.62, 0.38)
        rationale = generate_rationale(tip, mv, game_index=0, offline=True)
        assert "Roosters" in rationale

    def test_away_pick_short_name_in_rationale(self) -> None:
        tip = _tip("Brisbane Broncos", 0.62)
        mv = _market_view(0.38, 0.62)
        rationale = generate_rationale(tip, mv, game_index=0, offline=True)
        assert "Broncos" in rationale

    def test_multi_word_team_name_uses_mascot(self) -> None:
        """South Sydney Rabbitohs -> 'Rabbitohs' in rationale."""
        game = _game(home="South Sydney Rabbitohs", away="Canterbury Bulldogs")
        tip = Tip(
            game=game,
            pick="South Sydney Rabbitohs",
            confidence=0.65,
            rationale="",
            teaching_moment="",
        )
        mv = MarketView(
            game=game,
            odds_sources=[_odds(1.55, 2.50)],
            consensus_home_prob=0.65,
            consensus_away_prob=0.35,
        )
        rationale = generate_rationale(tip, mv, game_index=0, offline=True)
        assert "Rabbitohs" in rationale

    def test_opponent_short_name_in_rationale(self) -> None:
        """The opposing team's short name should also appear where templates use {other}."""
        tip = _tip("Sydney Roosters", 0.62)
        mv = _market_view(0.62, 0.38)
        rationale = generate_rationale(tip, mv, game_index=0, offline=True)
        assert "Broncos" in rationale


# ===========================================================================
# AC-07: team_short_name() correctly extracts mascots.
# ===========================================================================


class TestAC07TeamShortName:
    """team_short_name extracts the mascot from full team names."""

    def test_rabbitohs(self) -> None:
        assert team_short_name("South Sydney Rabbitohs") == "Rabbitohs"

    def test_dragons(self) -> None:
        assert team_short_name("St George Illawarra Dragons") == "Dragons"

    def test_panthers(self) -> None:
        assert team_short_name("Penrith Panthers") == "Panthers"

    def test_roosters(self) -> None:
        assert team_short_name("Sydney Roosters") == "Roosters"

    def test_cowboys(self) -> None:
        assert team_short_name("North Queensland Cowboys") == "Cowboys"

    def test_warriors(self) -> None:
        assert team_short_name("New Zealand Warriors") == "Warriors"

    def test_titans(self) -> None:
        assert team_short_name("Gold Coast Titans") == "Titans"

    def test_storm(self) -> None:
        assert team_short_name("Melbourne Storm") == "Storm"

    def test_broncos(self) -> None:
        assert team_short_name("Brisbane Broncos") == "Broncos"

    def test_bulldogs(self) -> None:
        assert team_short_name("Canterbury Bulldogs") == "Bulldogs"

    def test_sea_eagles(self) -> None:
        """'Manly Sea Eagles' -> last word is 'Eagles'."""
        assert team_short_name("Manly Sea Eagles") == "Eagles"

    def test_sharks(self) -> None:
        assert team_short_name("Cronulla Sharks") == "Sharks"

    def test_eels(self) -> None:
        assert team_short_name("Parramatta Eels") == "Eels"

    def test_knights(self) -> None:
        assert team_short_name("Newcastle Knights") == "Knights"

    def test_raiders(self) -> None:
        assert team_short_name("Canberra Raiders") == "Raiders"

    def test_tigers(self) -> None:
        assert team_short_name("Wests Tigers") == "Tigers"

    def test_dolphins(self) -> None:
        assert team_short_name("The Dolphins") == "Dolphins"


# ===========================================================================
# AC-09: Given the same round file input twice, the same rationale text
#         is produced both times (deterministic) — offline mode.
# ===========================================================================


class TestAC09Deterministic:
    """Same input always produces the same rationale text (offline mode)."""

    def test_same_input_same_output(self) -> None:
        tip = _tip("Sydney Roosters", 0.62)
        mv = _market_view(0.62, 0.38)
        r1 = generate_rationale(tip, mv, game_index=0, offline=True)
        r2 = generate_rationale(tip, mv, game_index=0, offline=True)
        assert r1 == r2

    def test_deterministic_across_all_indices(self) -> None:
        """All four template slots produce identical output on repeated calls."""
        tip = _tip("Sydney Roosters", 0.62)
        mv = _market_view(0.62, 0.38)
        for idx in range(4):
            r1 = generate_rationale(tip, mv, game_index=idx, offline=True)
            r2 = generate_rationale(tip, mv, game_index=idx, offline=True)
            assert r1 == r2, f"Non-deterministic at game_index={idx}"


# ===========================================================================
# Quant-enriched template tests
# ===========================================================================


class TestQuantEnrichedTemplates:
    """Templates include quant metrics when GameAnalysis is provided."""

    def test_template_with_game_analysis_includes_ev(self) -> None:
        mv = _market_view(0.62, 0.38)
        ga = analyse_game(mv)
        tip = _tip("Sydney Roosters", 0.62)
        rationale = generate_rationale_template(tip, mv, game_index=1, game_analysis=ga)
        # Lean template 1 includes {ev_fav} and {ev_dog}
        assert "%" in rationale  # EV formatted as percentage

    def test_template_without_game_analysis_uses_na(self) -> None:
        mv = _market_view(0.62, 0.38)
        tip = _tip("Sydney Roosters", 0.62)
        rationale = generate_rationale_template(tip, mv, game_index=1, game_analysis=None)
        assert "N/A" in rationale

    def test_all_templates_resolve_with_game_analysis(self) -> None:
        """No unresolved placeholders when game analysis is provided."""
        configs = [
            ("Sydney Roosters", 0.75, 0.75, 0.25),  # Lock
            ("Sydney Roosters", 0.62, 0.62, 0.38),  # Lean
            ("Sydney Roosters", 0.52, 0.52, 0.48),  # Coin Flip
        ]
        for pick, conf, hp, ap in configs:
            tip = _tip(pick, conf)
            mv = _market_view(hp, ap)
            ga = analyse_game(mv)
            for idx in range(4):
                rationale = generate_rationale_template(tip, mv, idx, game_analysis=ga)
                assert "{" not in rationale, (
                    f"Unresolved placeholder at tier={tip.confidence_label}, idx={idx}"
                )


# ===========================================================================
# Additional edge-case and integration tests
# ===========================================================================


class TestTemplateContentIntegrity:
    """Verify templates contain expected placeholders and produce valid output."""

    def test_all_templates_total_twelve(self) -> None:
        """There should be exactly 12 templates total (4 per tier)."""
        total = len(LOCK_TEMPLATES) + len(LEAN_TEMPLATES) + len(COIN_FLIP_TEMPLATES)
        assert total == 12

    def test_away_team_pick_home_or_away_value(self) -> None:
        """When the away team is picked, rationale should say 'on the road'."""
        tip = _tip("Brisbane Broncos", 0.62)
        mv = _market_view(0.38, 0.62)
        rationale = generate_rationale(tip, mv, game_index=0, offline=True)
        assert "on the road" in rationale

    def test_home_team_pick_home_or_away_value(self) -> None:
        """When the home team is picked, rationale should say 'at home'."""
        tip = _tip("Sydney Roosters", 0.75)
        mv = _market_view(0.75, 0.25)
        rationale = generate_rationale(tip, mv, game_index=0, offline=True)
        assert "at home" in rationale

    def test_venue_appears_in_rationale(self) -> None:
        """Venue appears in templates that reference it."""
        tip = _tip("Sydney Roosters", 0.52)
        mv = _market_view(0.52, 0.48)
        # Coin flip template 0 references {venue}
        rationale = generate_rationale(tip, mv, game_index=0, offline=True)
        assert "Allianz Stadium" in rationale
