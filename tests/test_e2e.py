"""End-to-end integration test for the full pipeline.

Exercises the complete tip-generation pipeline with realistic fixture
data, validating that every module works together correctly from
fixture loading through to file output.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from ralph.fixtures import load_fixtures
from ralph.market import build_market_views
from ralph.output import save_tip_sheet
from ralph.teaching import generate_teaching_snippet
from ralph.tips import generate_round_tips
from ralph.tracking import save_tips_log

# Inline fixture data — no dependency on external files.
_FIXTURE_DATA = {
    "round_number": 1,
    "season": 2026,
    "fixtures": [
        {
            "home_team": "Sydney Roosters",
            "away_team": "Brisbane Broncos",
            "venue": "Allianz Stadium",
            "kickoff": "2026-03-05T20:00",
            "odds": [
                {"source": "Sportsbet", "home_odds": 1.55, "away_odds": 2.50},
                {"source": "TAB", "home_odds": 1.52, "away_odds": 2.55},
            ],
        },
        {
            "home_team": "Penrith Panthers",
            "away_team": "Cronulla Sharks",
            "venue": "BlueBet Stadium",
            "kickoff": "2026-03-06T18:00",
            "odds": [
                {"source": "Sportsbet", "home_odds": 1.40, "away_odds": 3.00},
                {"source": "TAB", "home_odds": 1.38, "away_odds": 3.10},
            ],
        },
        {
            "home_team": "Melbourne Storm",
            "away_team": "Canterbury Bulldogs",
            "venue": "AAMI Park",
            "kickoff": "2026-03-06T19:55",
            "odds": [
                {"source": "Sportsbet", "home_odds": 1.30, "away_odds": 3.50},
                {"source": "TAB", "home_odds": 1.32, "away_odds": 3.40},
            ],
        },
        {
            "home_team": "Parramatta Eels",
            "away_team": "North Queensland Cowboys",
            "venue": "CommBank Stadium",
            "kickoff": "2026-03-07T15:00",
            "odds": [
                {"source": "Sportsbet", "home_odds": 1.80, "away_odds": 2.05},
                {"source": "TAB", "home_odds": 1.78, "away_odds": 2.08},
            ],
        },
        {
            "home_team": "Gold Coast Titans",
            "away_team": "Wests Tigers",
            "venue": "Cbus Super Stadium",
            "kickoff": "2026-03-07T17:30",
            "odds": [
                {"source": "Sportsbet", "home_odds": 1.65, "away_odds": 2.30},
                {"source": "TAB", "home_odds": 1.62, "away_odds": 2.35},
            ],
        },
        {
            "home_team": "Manly Sea Eagles",
            "away_team": "South Sydney Rabbitohs",
            "venue": "4 Pines Park",
            "kickoff": "2026-03-07T19:35",
            "odds": [
                {"source": "Sportsbet", "home_odds": 1.72, "away_odds": 2.15},
                {"source": "TAB", "home_odds": 1.70, "away_odds": 2.20},
            ],
        },
        {
            "home_team": "Canberra Raiders",
            "away_team": "New Zealand Warriors",
            "venue": "GIO Stadium",
            "kickoff": "2026-03-08T14:00",
            "odds": [
                {"source": "Sportsbet", "home_odds": 1.85, "away_odds": 2.00},
                {"source": "TAB", "home_odds": 1.83, "away_odds": 2.02},
            ],
        },
        {
            "home_team": "Newcastle Knights",
            "away_team": "St George Illawarra Dragons",
            "venue": "McDonald Jones Stadium",
            "kickoff": "2026-03-08T16:05",
            "odds": [
                {"source": "Sportsbet", "home_odds": 1.90, "away_odds": 1.95},
                {"source": "TAB", "home_odds": 1.88, "away_odds": 1.97},
            ],
        },
    ],
}


@pytest.fixture()
def e2e_data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory seeded with inline fixture data.

    Returns the tmp_path root (acts as the data_dir override for all
    pipeline functions that accept one).
    """
    rounds_dir = tmp_path / "rounds"
    rounds_dir.mkdir()
    fixture_file = rounds_dir / "round_01.json"
    fixture_file.write_text(json.dumps(_FIXTURE_DATA), encoding="utf-8")
    return tmp_path


class TestEndToEndPipeline:
    """Full pipeline integration test using inline fixture data."""

    # ------------------------------------------------------------------
    # Run the pipeline once and cache results for all assertions
    # ------------------------------------------------------------------

    @pytest.fixture(autouse=True)
    def _run_pipeline(self, e2e_data_dir: Path) -> None:
        """Execute the complete pipeline, storing results on self."""
        # 1. Load fixtures
        rounds_dir = e2e_data_dir / "rounds"
        self.games, self.odds_map = load_fixtures(1, data_dir=rounds_dir)

        # 2. Build market views
        self.market_views = build_market_views(self.games, self.odds_map)

        # 3. Generate tips (includes rationale)
        season = self.games[0].kickoff.year if self.games else 2026
        self.round_tips = generate_round_tips(self.market_views, 1, season)

        # 4. Generate teaching snippet and attach
        self.teaching = generate_teaching_snippet(1, self.market_views)
        self.round_tips.teaching_moment = self.teaching

        # 5. Save tips log
        self.tips_log_path = save_tips_log(self.round_tips, data_dir=e2e_data_dir)

        # 6. Save Markdown tip sheet
        tips_dir = e2e_data_dir / "tips"
        self.tip_sheet_path = save_tip_sheet(
            self.round_tips, self.market_views, {}, data_dir=tips_dir
        )

        # Keep a reference to the data dir for file-level checks.
        self._data_dir = e2e_data_dir

    # ------------------------------------------------------------------
    # Tip count
    # ------------------------------------------------------------------

    def test_eight_tips_generated(self):
        """Pipeline produces exactly 8 tips (one per game)."""
        assert len(self.round_tips.tips) == 8

    # ------------------------------------------------------------------
    # Rationale
    # ------------------------------------------------------------------

    def test_all_tips_have_nonempty_rationale(self):
        """Every tip has a non-empty rationale string."""
        for tip in self.round_tips.tips:
            assert tip.rationale, f"Empty rationale for {tip.game}"

    # ------------------------------------------------------------------
    # Confidence labels
    # ------------------------------------------------------------------

    def test_all_tips_have_valid_confidence_label(self):
        """Every tip's confidence_label is Lock, Lean, or Coin Flip."""
        valid_labels = {"Lock", "Lean", "Coin Flip"}
        for tip in self.round_tips.tips:
            assert tip.confidence_label in valid_labels, (
                f"Invalid label '{tip.confidence_label}' for {tip.game}"
            )

    # ------------------------------------------------------------------
    # Confidence range
    # ------------------------------------------------------------------

    def test_all_tips_confidence_between_zero_and_one(self):
        """Every tip's confidence is in [0.0, 1.0]."""
        for tip in self.round_tips.tips:
            assert 0.0 <= tip.confidence <= 1.0, (
                f"Confidence {tip.confidence} out of range for {tip.game}"
            )

    # ------------------------------------------------------------------
    # Teaching snippet
    # ------------------------------------------------------------------

    def test_teaching_snippet_present_and_nonempty(self):
        """The teaching_moment on round_tips is present and non-empty."""
        assert self.round_tips.teaching_moment
        assert len(self.round_tips.teaching_moment) > 10

    # ------------------------------------------------------------------
    # Markdown file creation
    # ------------------------------------------------------------------

    def test_markdown_file_created(self):
        """A Markdown tip sheet file is created on disk."""
        assert self.tip_sheet_path.exists()
        assert self.tip_sheet_path.suffix == ".md"

    def test_markdown_contains_all_eight_game_sections(self):
        """The Markdown file contains section headers for all 8 games."""
        content = self.tip_sheet_path.read_text(encoding="utf-8")
        for i in range(1, 9):
            assert f"## GAME {i}:" in content, f"Missing GAME {i} section in Markdown"

    # ------------------------------------------------------------------
    # Tips log file creation
    # ------------------------------------------------------------------

    def test_tips_log_created(self):
        """A tips log JSON file is created on disk."""
        assert self.tips_log_path.exists()
        assert self.tips_log_path.suffix == ".json"

    def test_tips_log_contains_eight_entries(self):
        """The tips log JSON contains exactly 8 tip entries."""
        data = json.loads(self.tips_log_path.read_text(encoding="utf-8"))
        assert len(data["tips"]) == 8

    # ------------------------------------------------------------------
    # Pick validity
    # ------------------------------------------------------------------

    def test_each_pick_is_one_of_the_two_teams(self):
        """Every tip's pick is either the home or away team for that game."""
        for tip in self.round_tips.tips:
            valid_teams = {tip.game.home_team, tip.game.away_team}
            assert tip.pick in valid_teams, f"Pick '{tip.pick}' not in {valid_teams} for {tip.game}"

    # ------------------------------------------------------------------
    # No unresolved placeholders
    # ------------------------------------------------------------------

    def test_no_unresolved_placeholders_in_rationale(self):
        """No {variable} placeholders remain in any rationale text."""
        placeholder_re = re.compile(r"\{[a-z_]+\}")
        for tip in self.round_tips.tips:
            assert not placeholder_re.search(tip.rationale), (
                f"Unresolved placeholder in rationale: {tip.rationale}"
            )

    def test_no_unresolved_placeholders_in_teaching(self):
        """No {variable} placeholders remain in the teaching snippet."""
        placeholder_re = re.compile(r"\{[a-z_]+\}")
        assert not placeholder_re.search(self.round_tips.teaching_moment), (
            f"Unresolved placeholder in teaching: {self.round_tips.teaching_moment}"
        )

    # ------------------------------------------------------------------
    # Market probabilities sum to ~1.0
    # ------------------------------------------------------------------

    def test_market_view_probabilities_sum_to_one(self):
        """Each MarketView's home + away probabilities sum to ~1.0."""
        for mv in self.market_views:
            total = mv.consensus_home_prob + mv.consensus_away_prob
            assert abs(total - 1.0) < 1e-9, (
                f"Probabilities sum to {total} (not ~1.0) for "
                f"{mv.game.home_team} v {mv.game.away_team}"
            )

    # ------------------------------------------------------------------
    # Tips log content matches round_tips
    # ------------------------------------------------------------------

    def test_tips_log_picks_match_round_tips(self):
        """The tips log file's pick values match what the pipeline produced."""
        data = json.loads(self.tips_log_path.read_text(encoding="utf-8"))
        for log_entry, tip in zip(data["tips"], self.round_tips.tips):
            assert log_entry["pick"] == tip.pick
            assert log_entry["confidence_label"] == tip.confidence_label
