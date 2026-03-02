"""Tests for ralph.tracking — result tracking and accuracy calculation.

Each test maps to one or more acceptance criteria from spec 06_track_accuracy.md.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from ralph.models import Game, RoundTips, Tip
from ralph.tracking import (
    calculate_accuracy,
    get_season_record,
    load_results,
    load_tips_log,
    match_results,
    save_tips_log,
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


def _tip(
    home: str = "Sydney Roosters",
    away: str = "Brisbane Broncos",
    pick: str = "Sydney Roosters",
    confidence: float = 0.6173,
) -> Tip:
    return Tip(
        game=_game(home, away),
        pick=pick,
        confidence=confidence,
        rationale="Test rationale",
        teaching_moment="",
    )


def _round_tips(tips: list[Tip] | None = None, round_number: int = 1) -> RoundTips:
    if tips is None:
        tips = [
            _tip("Sydney Roosters", "Brisbane Broncos", "Sydney Roosters", 0.75),
            _tip("Penrith Panthers", "Cronulla Sharks", "Penrith Panthers", 0.62),
            _tip("Melbourne Storm", "Canterbury Bulldogs", "Melbourne Storm", 0.51),
        ]
    return RoundTips(
        round_number=round_number,
        season=2025,
        tips=tips,
        generated_at=datetime(2025, 3, 5, 14, 30, 0),
        teaching_moment="",
    )


def _write_results_file(
    tmp_path: Path,
    round_number: int = 1,
    results: list[dict] | None = None,
) -> Path:
    """Write a valid results JSON file into the tmp_path results directory."""
    if results is None:
        results = [
            {
                "home_team": "Sydney Roosters",
                "away_team": "Brisbane Broncos",
                "winner": "Sydney Roosters",
            },
            {
                "home_team": "Penrith Panthers",
                "away_team": "Cronulla Sharks",
                "winner": "Penrith Panthers",
            },
            {
                "home_team": "Melbourne Storm",
                "away_team": "Canterbury Bulldogs",
                "winner": "Canterbury Bulldogs",
            },
        ]

    results_dir = tmp_path / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    filepath = results_dir / f"round_{round_number:02d}.json"

    data = {
        "round_number": round_number,
        "season": 2025,
        "results": results,
    }
    filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return filepath


def _write_tips_log_file(
    tmp_path: Path,
    round_number: int = 1,
    tips: list[dict] | None = None,
) -> Path:
    """Write a tips log JSON file directly into the tmp_path tips_log directory."""
    if tips is None:
        tips = [
            {
                "home_team": "Sydney Roosters",
                "away_team": "Brisbane Broncos",
                "pick": "Sydney Roosters",
                "confidence": 0.75,
                "confidence_label": "Lock",
            },
            {
                "home_team": "Penrith Panthers",
                "away_team": "Cronulla Sharks",
                "pick": "Penrith Panthers",
                "confidence": 0.62,
                "confidence_label": "Lean",
            },
            {
                "home_team": "Melbourne Storm",
                "away_team": "Canterbury Bulldogs",
                "pick": "Melbourne Storm",
                "confidence": 0.51,
                "confidence_label": "Coin Flip",
            },
        ]

    tips_dir = tmp_path / "tips_log"
    tips_dir.mkdir(parents=True, exist_ok=True)
    filepath = tips_dir / f"round_{round_number:02d}.json"

    data = {
        "round_number": round_number,
        "season": 2025,
        "generated_at": "2025-03-05T14:30:00",
        "tips": tips,
    }
    filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return filepath


# ===========================================================================
# AC-01: Tips log file is created with the correct schema
# ===========================================================================


class TestSaveTipsLog:
    """AC-01: save_tips_log writes valid JSON with the expected schema."""

    def test_ac01_creates_file(self, tmp_path: Path) -> None:
        """save_tips_log creates a JSON file in the tips_log directory."""
        rt = _round_tips()
        path = save_tips_log(rt, data_dir=tmp_path)
        assert path.exists()
        assert path.name == "round_01.json"

    def test_ac01_valid_json(self, tmp_path: Path) -> None:
        """The written file is valid JSON."""
        rt = _round_tips()
        path = save_tips_log(rt, data_dir=tmp_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_ac01_schema_fields(self, tmp_path: Path) -> None:
        """The JSON contains round_number, season, generated_at, and tips."""
        rt = _round_tips()
        path = save_tips_log(rt, data_dir=tmp_path)
        data = json.loads(path.read_text(encoding="utf-8"))

        assert data["round_number"] == 1
        assert data["season"] == 2025
        assert data["generated_at"] == "2025-03-05T14:30:00"
        assert isinstance(data["tips"], list)
        assert len(data["tips"]) == 3

    def test_ac10_tip_has_confidence_and_label(self, tmp_path: Path) -> None:
        """AC-10: Each tip stores confidence (float) and confidence_label (string)."""
        rt = _round_tips()
        path = save_tips_log(rt, data_dir=tmp_path)
        data = json.loads(path.read_text(encoding="utf-8"))

        for tip in data["tips"]:
            assert "confidence" in tip
            assert isinstance(tip["confidence"], float)
            assert "confidence_label" in tip
            assert isinstance(tip["confidence_label"], str)
            assert tip["confidence_label"] in ("Lock", "Lean", "Coin Flip")

    def test_ac10_confidence_labels_correct(self, tmp_path: Path) -> None:
        """AC-10: Confidence labels match the expected tier thresholds."""
        rt = _round_tips()
        path = save_tips_log(rt, data_dir=tmp_path)
        data = json.loads(path.read_text(encoding="utf-8"))

        labels = [tip["confidence_label"] for tip in data["tips"]]
        assert labels == ["Lock", "Lean", "Coin Flip"]

    def test_ac01_tip_fields(self, tmp_path: Path) -> None:
        """Each tip dict has home_team, away_team, pick, confidence, confidence_label."""
        rt = _round_tips()
        path = save_tips_log(rt, data_dir=tmp_path)
        data = json.loads(path.read_text(encoding="utf-8"))

        required_fields = {"home_team", "away_team", "pick", "confidence", "confidence_label"}
        for tip in data["tips"]:
            assert required_fields.issubset(set(tip.keys()))

    def test_ac01_round_number_padding(self, tmp_path: Path) -> None:
        """Round numbers are zero-padded in the filename."""
        rt = _round_tips(round_number=5)
        path = save_tips_log(rt, data_dir=tmp_path)
        assert path.name == "round_05.json"

    def test_ac01_creates_directory_if_missing(self, tmp_path: Path) -> None:
        """save_tips_log creates the tips_log directory if it doesn't exist."""
        # tmp_path exists but tips_log/ doesn't yet
        rt = _round_tips()
        path = save_tips_log(rt, data_dir=tmp_path)
        assert path.parent.exists()
        assert path.parent.name == "tips_log"

    def test_ac01_returns_path(self, tmp_path: Path) -> None:
        """save_tips_log returns the path to the written file."""
        rt = _round_tips()
        path = save_tips_log(rt, data_dir=tmp_path)
        assert isinstance(path, Path)
        assert path.exists()


# ===========================================================================
# AC-02, AC-03, AC-04: match_results identifies correct/incorrect picks
# ===========================================================================


class TestMatchResults:
    """AC-02/03/04: match_results correctly identifies which picks were right and wrong."""

    def test_ac02_matches_tips_to_results(self) -> None:
        """match_results returns one matched dict per game."""
        tips_log = {
            "round_number": 1,
            "tips": [
                {
                    "home_team": "Sydney Roosters",
                    "away_team": "Brisbane Broncos",
                    "pick": "Sydney Roosters",
                    "confidence": 0.75,
                    "confidence_label": "Lock",
                },
            ],
        }
        results = [
            {
                "home_team": "Sydney Roosters",
                "away_team": "Brisbane Broncos",
                "winner": "Sydney Roosters",
            },
        ]
        matched = match_results(tips_log, results)
        assert len(matched) == 1

    def test_ac03_correct_pick(self) -> None:
        """AC-03: Pick matches winner -> correct is True."""
        tips_log = {
            "tips": [
                {
                    "home_team": "Sydney Roosters",
                    "away_team": "Brisbane Broncos",
                    "pick": "Sydney Roosters",
                    "confidence": 0.75,
                    "confidence_label": "Lock",
                },
            ],
        }
        results = [
            {
                "home_team": "Sydney Roosters",
                "away_team": "Brisbane Broncos",
                "winner": "Sydney Roosters",
            },
        ]
        matched = match_results(tips_log, results)
        assert matched[0]["correct"] is True
        assert matched[0]["pick"] == "Sydney Roosters"
        assert matched[0]["result"] == "Sydney Roosters"

    def test_ac04_incorrect_pick(self) -> None:
        """AC-04: Pick does not match winner -> correct is False."""
        tips_log = {
            "tips": [
                {
                    "home_team": "Sydney Roosters",
                    "away_team": "Brisbane Broncos",
                    "pick": "Sydney Roosters",
                    "confidence": 0.62,
                    "confidence_label": "Lean",
                },
            ],
        }
        results = [
            {
                "home_team": "Sydney Roosters",
                "away_team": "Brisbane Broncos",
                "winner": "Brisbane Broncos",
            },
        ]
        matched = match_results(tips_log, results)
        assert matched[0]["correct"] is False
        assert matched[0]["pick"] == "Sydney Roosters"
        assert matched[0]["result"] == "Brisbane Broncos"

    def test_ac02_multiple_games(self) -> None:
        """match_results handles multiple games in a round."""
        tips_log = {
            "tips": [
                {
                    "home_team": "Sydney Roosters",
                    "away_team": "Brisbane Broncos",
                    "pick": "Sydney Roosters",
                    "confidence": 0.75,
                    "confidence_label": "Lock",
                },
                {
                    "home_team": "Penrith Panthers",
                    "away_team": "Cronulla Sharks",
                    "pick": "Penrith Panthers",
                    "confidence": 0.62,
                    "confidence_label": "Lean",
                },
                {
                    "home_team": "Melbourne Storm",
                    "away_team": "Canterbury Bulldogs",
                    "pick": "Melbourne Storm",
                    "confidence": 0.51,
                    "confidence_label": "Coin Flip",
                },
            ],
        }
        results = [
            {
                "home_team": "Sydney Roosters",
                "away_team": "Brisbane Broncos",
                "winner": "Sydney Roosters",
            },
            {
                "home_team": "Penrith Panthers",
                "away_team": "Cronulla Sharks",
                "winner": "Penrith Panthers",
            },
            {
                "home_team": "Melbourne Storm",
                "away_team": "Canterbury Bulldogs",
                "winner": "Canterbury Bulldogs",
            },
        ]
        matched = match_results(tips_log, results)
        assert len(matched) == 3
        assert matched[0]["correct"] is True  # Roosters correct
        assert matched[1]["correct"] is True  # Panthers correct
        assert matched[2]["correct"] is False  # Storm incorrect

    def test_ac02_matched_dict_fields(self) -> None:
        """Each matched dict has the required keys."""
        tips_log = {
            "tips": [
                {
                    "home_team": "Sydney Roosters",
                    "away_team": "Brisbane Broncos",
                    "pick": "Sydney Roosters",
                    "confidence": 0.75,
                    "confidence_label": "Lock",
                },
            ],
        }
        results = [
            {
                "home_team": "Sydney Roosters",
                "away_team": "Brisbane Broncos",
                "winner": "Sydney Roosters",
            },
        ]
        matched = match_results(tips_log, results)
        m = matched[0]
        assert "game" in m
        assert "pick" in m
        assert "result" in m
        assert "correct" in m
        assert "confidence" in m
        assert "confidence_label" in m

    def test_match_results_skips_unmatched(self) -> None:
        """If a tip has no matching result, it is skipped."""
        tips_log = {
            "tips": [
                {
                    "home_team": "Sydney Roosters",
                    "away_team": "Brisbane Broncos",
                    "pick": "Sydney Roosters",
                    "confidence": 0.75,
                    "confidence_label": "Lock",
                },
            ],
        }
        results = [
            {
                "home_team": "Penrith Panthers",
                "away_team": "Cronulla Sharks",
                "winner": "Penrith Panthers",
            },
        ]
        matched = match_results(tips_log, results)
        assert len(matched) == 0


# ===========================================================================
# AC-05: Cumulative accuracy across multiple rounds
# ===========================================================================


class TestCalculateAccuracy:
    """AC-05/06: calculate_accuracy returns correct overall and per-tier accuracy."""

    def test_ac05_overall_accuracy(self) -> None:
        """Overall accuracy is correct / total."""
        matched = [
            {"correct": True, "confidence_label": "Lock"},
            {"correct": True, "confidence_label": "Lean"},
            {"correct": False, "confidence_label": "Coin Flip"},
        ]
        acc = calculate_accuracy(matched)
        assert acc["total"] == 3
        assert acc["correct"] == 2
        assert acc["overall"] == pytest.approx(2 / 3)

    def test_ac05_perfect_accuracy(self) -> None:
        """100% accuracy when all picks are correct."""
        matched = [
            {"correct": True, "confidence_label": "Lock"},
            {"correct": True, "confidence_label": "Lean"},
        ]
        acc = calculate_accuracy(matched)
        assert acc["overall"] == pytest.approx(1.0)

    def test_ac05_zero_accuracy(self) -> None:
        """0% accuracy when no picks are correct."""
        matched = [
            {"correct": False, "confidence_label": "Lock"},
            {"correct": False, "confidence_label": "Lean"},
        ]
        acc = calculate_accuracy(matched)
        assert acc["overall"] == pytest.approx(0.0)

    def test_ac06_per_tier_accuracy(self) -> None:
        """AC-06: Per-tier accuracy separates Lock, Lean, and Coin Flip."""
        matched = [
            {"correct": True, "confidence_label": "Lock"},
            {"correct": True, "confidence_label": "Lock"},
            {"correct": False, "confidence_label": "Lock"},
            {"correct": True, "confidence_label": "Lean"},
            {"correct": False, "confidence_label": "Lean"},
            {"correct": False, "confidence_label": "Coin Flip"},
            {"correct": True, "confidence_label": "Coin Flip"},
        ]
        acc = calculate_accuracy(matched)
        assert acc["by_tier"]["Lock"] == pytest.approx(2 / 3)
        assert acc["by_tier"]["Lean"] == pytest.approx(1 / 2)
        assert acc["by_tier"]["Coin Flip"] == pytest.approx(1 / 2)

    def test_ac06_empty_tier_returns_zero(self) -> None:
        """A tier with no picks returns 0.0 accuracy."""
        matched = [
            {"correct": True, "confidence_label": "Lock"},
        ]
        acc = calculate_accuracy(matched)
        assert acc["by_tier"]["Lean"] == 0.0
        assert acc["by_tier"]["Coin Flip"] == 0.0

    def test_empty_matched_list(self) -> None:
        """calculate_accuracy with empty list returns zeroed stats."""
        acc = calculate_accuracy([])
        assert acc["overall"] == 0.0
        assert acc["total"] == 0
        assert acc["correct"] == 0

    def test_accuracy_dict_structure(self) -> None:
        """The accuracy dict has the expected keys."""
        matched = [{"correct": True, "confidence_label": "Lock"}]
        acc = calculate_accuracy(matched)
        assert "overall" in acc
        assert "by_tier" in acc
        assert "total" in acc
        assert "correct" in acc
        assert set(acc["by_tier"].keys()) == {"Lock", "Lean", "Coin Flip"}


# ===========================================================================
# AC-05: get_season_record aggregates across rounds
# ===========================================================================


class TestGetSeasonRecord:
    """AC-05/07: get_season_record scans all completed rounds."""

    def test_ac05_aggregates_across_rounds(self, tmp_path: Path) -> None:
        """Season record aggregates accuracy across multiple completed rounds."""
        # Round 1: 2 correct out of 3
        _write_tips_log_file(
            tmp_path,
            round_number=1,
            tips=[
                {
                    "home_team": "Sydney Roosters",
                    "away_team": "Brisbane Broncos",
                    "pick": "Sydney Roosters",
                    "confidence": 0.75,
                    "confidence_label": "Lock",
                },
                {
                    "home_team": "Penrith Panthers",
                    "away_team": "Cronulla Sharks",
                    "pick": "Penrith Panthers",
                    "confidence": 0.62,
                    "confidence_label": "Lean",
                },
                {
                    "home_team": "Melbourne Storm",
                    "away_team": "Canterbury Bulldogs",
                    "pick": "Melbourne Storm",
                    "confidence": 0.51,
                    "confidence_label": "Coin Flip",
                },
            ],
        )
        _write_results_file(
            tmp_path,
            round_number=1,
            results=[
                {
                    "home_team": "Sydney Roosters",
                    "away_team": "Brisbane Broncos",
                    "winner": "Sydney Roosters",
                },
                {
                    "home_team": "Penrith Panthers",
                    "away_team": "Cronulla Sharks",
                    "winner": "Penrith Panthers",
                },
                {
                    "home_team": "Melbourne Storm",
                    "away_team": "Canterbury Bulldogs",
                    "winner": "Canterbury Bulldogs",
                },
            ],
        )

        # Round 2: 1 correct out of 2
        _write_tips_log_file(
            tmp_path,
            round_number=2,
            tips=[
                {
                    "home_team": "Gold Coast Titans",
                    "away_team": "Wests Tigers",
                    "pick": "Gold Coast Titans",
                    "confidence": 0.65,
                    "confidence_label": "Lean",
                },
                {
                    "home_team": "Canberra Raiders",
                    "away_team": "Newcastle Knights",
                    "pick": "Canberra Raiders",
                    "confidence": 0.70,
                    "confidence_label": "Lock",
                },
            ],
        )
        _write_results_file(
            tmp_path,
            round_number=2,
            results=[
                {
                    "home_team": "Gold Coast Titans",
                    "away_team": "Wests Tigers",
                    "winner": "Gold Coast Titans",
                },
                {
                    "home_team": "Canberra Raiders",
                    "away_team": "Newcastle Knights",
                    "winner": "Newcastle Knights",
                },
            ],
        )

        record = get_season_record(data_dir=tmp_path)
        assert record["rounds_completed"] == [1, 2]
        assert record["total"] == 5
        assert record["correct"] == 3
        assert record["overall"] == pytest.approx(3 / 5)

    def test_ac07_no_results_yet(self, tmp_path: Path) -> None:
        """AC-07: No completed rounds returns empty record."""
        record = get_season_record(data_dir=tmp_path)
        assert record["rounds_completed"] == []
        assert record["total"] == 0
        assert record["correct"] == 0
        assert record["overall"] == 0.0

    def test_ac07_tips_only_no_results(self, tmp_path: Path) -> None:
        """Tips exist but no matching results -> no completed rounds."""
        _write_tips_log_file(tmp_path, round_number=1)
        record = get_season_record(data_dir=tmp_path)
        assert record["rounds_completed"] == []

    def test_ac07_results_only_no_tips(self, tmp_path: Path) -> None:
        """Results exist but no matching tips log -> no completed rounds."""
        _write_results_file(tmp_path, round_number=1)
        record = get_season_record(data_dir=tmp_path)
        assert record["rounds_completed"] == []

    def test_partial_season(self, tmp_path: Path) -> None:
        """Only rounds with both tips and results are included."""
        # Round 1: complete (tips + results)
        _write_tips_log_file(tmp_path, round_number=1)
        _write_results_file(tmp_path, round_number=1)

        # Round 2: tips only (no results yet)
        _write_tips_log_file(tmp_path, round_number=2)

        record = get_season_record(data_dir=tmp_path)
        assert record["rounds_completed"] == [1]

    def test_season_record_has_by_tier(self, tmp_path: Path) -> None:
        """Season record includes by_tier breakdown."""
        _write_tips_log_file(tmp_path, round_number=1)
        _write_results_file(tmp_path, round_number=1)

        record = get_season_record(data_dir=tmp_path)
        assert "by_tier" in record
        assert set(record["by_tier"].keys()) == {"Lock", "Lean", "Coin Flip"}


# ===========================================================================
# AC-08: Invalid winner raises ValueError
# ===========================================================================


class TestLoadResults:
    """AC-08/11: load_results validates results files."""

    def test_ac08_invalid_winner_raises(self, tmp_path: Path) -> None:
        """AC-08: winner not matching home or away raises ValueError."""
        _write_results_file(
            tmp_path,
            results=[
                {
                    "home_team": "Sydney Roosters",
                    "away_team": "Brisbane Broncos",
                    "winner": "Melbourne Storm",  # Not home or away!
                },
            ],
        )
        with pytest.raises(ValueError, match="does not match"):
            load_results(1, data_dir=tmp_path)

    def test_ac11_draw_scores_raises(self, tmp_path: Path) -> None:
        """AC-11: Equal scores raise ValueError (no draws in NRL golden point)."""
        _write_results_file(
            tmp_path,
            results=[
                {
                    "home_team": "Sydney Roosters",
                    "away_team": "Brisbane Broncos",
                    "winner": "Sydney Roosters",
                    "home_score": 20,
                    "away_score": 20,
                },
            ],
        )
        with pytest.raises(ValueError, match="cannot draw"):
            load_results(1, data_dir=tmp_path)

    def test_ac11_draw_flag_raises(self, tmp_path: Path) -> None:
        """AC-11: Explicit draw flag raises ValueError."""
        _write_results_file(
            tmp_path,
            results=[
                {
                    "home_team": "Sydney Roosters",
                    "away_team": "Brisbane Broncos",
                    "winner": "Sydney Roosters",
                    "draw": True,
                },
            ],
        )
        with pytest.raises(ValueError, match="draws are not supported"):
            load_results(1, data_dir=tmp_path)

    def test_load_results_valid(self, tmp_path: Path) -> None:
        """A valid results file is loaded without error."""
        _write_results_file(tmp_path)
        results = load_results(1, data_dir=tmp_path)
        assert len(results) == 3
        assert results[0]["winner"] == "Sydney Roosters"

    def test_load_results_missing_file(self, tmp_path: Path) -> None:
        """FileNotFoundError when results file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_results(99, data_dir=tmp_path)

    def test_load_results_missing_fields(self, tmp_path: Path) -> None:
        """ValueError when result dict is missing required fields."""
        _write_results_file(
            tmp_path,
            results=[
                {
                    "home_team": "Sydney Roosters",
                    # Missing away_team and winner!
                },
            ],
        )
        with pytest.raises(ValueError, match="missing required fields"):
            load_results(1, data_dir=tmp_path)

    def test_load_results_invalid_json(self, tmp_path: Path) -> None:
        """ValueError when the file contains invalid JSON."""
        results_dir = tmp_path / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        filepath = results_dir / "round_01.json"
        filepath.write_text("not valid json{{{", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_results(1, data_dir=tmp_path)

    def test_load_results_missing_results_key(self, tmp_path: Path) -> None:
        """ValueError when the JSON doesn't have a 'results' key."""
        results_dir = tmp_path / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        filepath = results_dir / "round_01.json"
        filepath.write_text('{"round_number": 1}', encoding="utf-8")
        with pytest.raises(ValueError, match="Expected a 'results' list"):
            load_results(1, data_dir=tmp_path)

    def test_valid_scores_different(self, tmp_path: Path) -> None:
        """Results with different scores are valid."""
        _write_results_file(
            tmp_path,
            results=[
                {
                    "home_team": "Sydney Roosters",
                    "away_team": "Brisbane Broncos",
                    "winner": "Sydney Roosters",
                    "home_score": 24,
                    "away_score": 18,
                },
            ],
        )
        results = load_results(1, data_dir=tmp_path)
        assert len(results) == 1


# ===========================================================================
# AC-09: Missing tips log raises clear error
# ===========================================================================


class TestLoadTipsLog:
    """AC-09: load_tips_log raises clear error when no tips exist."""

    def test_ac09_missing_tips_log(self, tmp_path: Path) -> None:
        """AC-09: FileNotFoundError with helpful message when tips log is missing."""
        with pytest.raises(FileNotFoundError, match="No tips found for round 5"):
            load_tips_log(5, data_dir=tmp_path)

    def test_ac09_error_message_includes_command(self, tmp_path: Path) -> None:
        """Error message suggests the correct command to generate tips."""
        with pytest.raises(FileNotFoundError, match="ralph tip --round 5"):
            load_tips_log(5, data_dir=tmp_path)

    def test_load_tips_log_valid(self, tmp_path: Path) -> None:
        """A valid tips log file can be loaded."""
        _write_tips_log_file(tmp_path, round_number=1)
        data = load_tips_log(1, data_dir=tmp_path)
        assert data["round_number"] == 1
        assert len(data["tips"]) == 3


# ===========================================================================
# Integration: save_tips_log -> load_tips_log -> match_results -> accuracy
# ===========================================================================


class TestTrackingIntegration:
    """Integration tests for the full tracking pipeline."""

    def test_save_then_load_roundtrip(self, tmp_path: Path) -> None:
        """Tips saved with save_tips_log can be loaded with load_tips_log."""
        rt = _round_tips()
        save_tips_log(rt, data_dir=tmp_path)
        data = load_tips_log(1, data_dir=tmp_path)
        assert data["round_number"] == 1
        assert len(data["tips"]) == 3

    def test_full_pipeline(self, tmp_path: Path) -> None:
        """Full pipeline: save tips -> load tips -> load results -> match -> accuracy."""
        rt = _round_tips()
        save_tips_log(rt, data_dir=tmp_path)

        # Roosters correct, Panthers correct, Storm incorrect
        _write_results_file(tmp_path)

        tips_log = load_tips_log(1, data_dir=tmp_path)
        results = load_results(1, data_dir=tmp_path)
        matched = match_results(tips_log, results)

        assert len(matched) == 3
        assert matched[0]["correct"] is True  # Roosters (Lock)
        assert matched[1]["correct"] is True  # Panthers (Lean)
        assert matched[2]["correct"] is False  # Storm (Coin Flip)

        acc = calculate_accuracy(matched)
        assert acc["total"] == 3
        assert acc["correct"] == 2
        assert acc["overall"] == pytest.approx(2 / 3)
        assert acc["by_tier"]["Lock"] == pytest.approx(1.0)
        assert acc["by_tier"]["Lean"] == pytest.approx(1.0)
        assert acc["by_tier"]["Coin Flip"] == pytest.approx(0.0)

    def test_full_pipeline_season_record(self, tmp_path: Path) -> None:
        """get_season_record integrates with save_tips_log and results files."""
        rt = _round_tips()
        save_tips_log(rt, data_dir=tmp_path)
        _write_results_file(tmp_path)

        record = get_season_record(data_dir=tmp_path)
        assert record["rounds_completed"] == [1]
        assert record["total"] == 3
        assert record["correct"] == 2
