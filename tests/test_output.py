"""Tests for ralph.output — console and Markdown tip sheet formatting.

Covers key acceptance criteria from spec 07_share_tip_sheet.md.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from ralph.models import Game, MarketView, Odds, RoundTips, Tip
from ralph.output import (
    _format_kickoff,
    format_round_console,
    format_round_markdown,
    format_tip_console,
    save_tip_sheet,
)

# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------


@pytest.fixture()
def friday_game() -> Game:
    """A game kicking off on Friday at 7:55pm AEDT (UTC+11).

    UTC: Friday 2025-03-07 08:55 -> AEDT: Friday 2025-03-07 19:55.
    """
    return Game(
        home_team="Sydney Roosters",
        away_team="Brisbane Broncos",
        venue="Allianz Stadium",
        kickoff=datetime(2025, 3, 7, 8, 55, tzinfo=timezone.utc),
        round_number=1,
    )


@pytest.fixture()
def saturday_game() -> Game:
    """A game kicking off on Saturday at 3:00pm AEDT (UTC+11).

    UTC: Saturday 2025-03-08 04:00 -> AEDT: Saturday 2025-03-08 15:00.
    """
    return Game(
        home_team="Melbourne Storm",
        away_team="Penrith Panthers",
        venue="AAMI Park",
        kickoff=datetime(2025, 3, 8, 4, 0, tzinfo=timezone.utc),
        round_number=1,
    )


@pytest.fixture()
def friday_odds() -> list[Odds]:
    return [
        Odds(home_odds=1.55, away_odds=2.50, source="Sportsbet"),
        Odds(home_odds=1.52, away_odds=2.55, source="TAB"),
    ]


@pytest.fixture()
def saturday_odds() -> list[Odds]:
    return [
        Odds(home_odds=1.90, away_odds=1.90, source="Sportsbet"),
    ]


@pytest.fixture()
def friday_mv(friday_game: Game, friday_odds: list[Odds]) -> MarketView:
    return MarketView(
        game=friday_game,
        odds_sources=friday_odds,
        consensus_home_prob=0.6173,
        consensus_away_prob=0.3827,
    )


@pytest.fixture()
def saturday_mv(saturday_game: Game, saturday_odds: list[Odds]) -> MarketView:
    return MarketView(
        game=saturday_game,
        odds_sources=saturday_odds,
        consensus_home_prob=0.51,
        consensus_away_prob=0.49,
    )


@pytest.fixture()
def lock_mv(friday_game: Game, friday_odds: list[Odds]) -> MarketView:
    """A MarketView with Lock-level confidence (>=70%)."""
    return MarketView(
        game=friday_game,
        odds_sources=friday_odds,
        consensus_home_prob=0.75,
        consensus_away_prob=0.25,
    )


@pytest.fixture()
def lock_tip(friday_game: Game) -> Tip:
    return Tip(
        game=friday_game,
        pick="Sydney Roosters",
        confidence=0.75,
        rationale="Ralph is very confident here.",
        teaching_moment="",
    )


@pytest.fixture()
def lean_tip(friday_game: Game) -> Tip:
    return Tip(
        game=friday_game,
        pick="Sydney Roosters",
        confidence=0.6173,
        rationale="Ralph leans Roosters here.",
        teaching_moment="",
    )


@pytest.fixture()
def coin_flip_tip(saturday_game: Game) -> Tip:
    return Tip(
        game=saturday_game,
        pick="Melbourne Storm",
        confidence=0.51,
        rationale="Could go either way.",
        teaching_moment="",
    )


@pytest.fixture()
def sample_round(lean_tip: Tip, coin_flip_tip: Tip) -> RoundTips:
    return RoundTips(
        round_number=1,
        season=2025,
        tips=[lean_tip, coin_flip_tip],
        generated_at=datetime(2025, 3, 5, 12, 0, 0),
        teaching_moment="Here is a teaching moment about probability.",
    )


# ---------------------------------------------------------------------------
# AC-13: Kickoff time display — "Friday 7:55pm" format
# ---------------------------------------------------------------------------


class TestKickoffFormatting:
    """AC-13: Kickoff times in 'Day H:MMam/pm' format."""

    def test_friday_evening(self, friday_game: Game):
        result = _format_kickoff(friday_game.kickoff)
        assert result == "Friday 7:55pm"

    def test_saturday_afternoon(self, saturday_game: Game):
        result = _format_kickoff(saturday_game.kickoff)
        assert result == "Saturday 3:00pm"

    def test_sunday_morning(self):
        # Sunday 10:30am AEDT = Saturday 11:30pm UTC
        kickoff = datetime(2025, 3, 8, 23, 30, tzinfo=timezone.utc)
        result = _format_kickoff(kickoff)
        assert result == "Sunday 10:30am"

    def test_thursday_night(self):
        # Thursday 8:00pm AEDT = Thursday 9:00am UTC
        kickoff = datetime(2025, 3, 6, 9, 0, tzinfo=timezone.utc)
        result = _format_kickoff(kickoff)
        assert result == "Thursday 8:00pm"

    def test_no_leading_zero(self):
        """The hour should NOT have a leading zero (7:55pm not 07:55pm)."""
        # Friday 7:30am AEDT = Thursday 8:30pm UTC
        kickoff = datetime(2025, 3, 6, 20, 30, tzinfo=timezone.utc)
        result = _format_kickoff(kickoff)
        assert result == "Friday 7:30am"
        assert "07:" not in result


# ---------------------------------------------------------------------------
# Console output tests
# ---------------------------------------------------------------------------


class TestFormatTipConsole:
    """Tests for single-tip console formatting."""

    def test_contains_team_names(self, lean_tip: Tip, friday_mv: MarketView):
        result = format_tip_console(lean_tip, friday_mv, game_number=1)
        assert "Sydney Roosters" in result
        assert "Brisbane Broncos" in result

    def test_contains_venue(self, lean_tip: Tip, friday_mv: MarketView):
        result = format_tip_console(lean_tip, friday_mv, game_number=1)
        assert "Allianz Stadium" in result

    def test_contains_kickoff(self, lean_tip: Tip, friday_mv: MarketView):
        """AC-13: kickoff in the console output."""
        result = format_tip_console(lean_tip, friday_mv, game_number=1)
        assert "Friday 7:55pm" in result

    def test_contains_confidence_label_lean(self, lean_tip: Tip, friday_mv: MarketView):
        """AC-05: confidence label shown."""
        result = format_tip_console(lean_tip, friday_mv, game_number=1)
        assert "Lean" in result

    def test_contains_confidence_percentage(self, lean_tip: Tip, friday_mv: MarketView):
        """AC-05: confidence percentage shown."""
        result = format_tip_console(lean_tip, friday_mv, game_number=1)
        assert "62%" in result

    def test_contains_game_number(self, lean_tip: Tip, friday_mv: MarketView):
        """AC-14: game number in output."""
        result = format_tip_console(lean_tip, friday_mv, game_number=3)
        assert "GAME 3" in result

    def test_contains_rationale(self, lean_tip: Tip, friday_mv: MarketView):
        """AC-07: rationale shown."""
        result = format_tip_console(lean_tip, friday_mv, game_number=1)
        assert "Ralph leans Roosters here." in result

    def test_ac15_odds_with_dollar_sign(self, lean_tip: Tip, friday_mv: MarketView):
        """AC-15: odds displayed with dollar sign prefix."""
        result = format_tip_console(lean_tip, friday_mv, game_number=1)
        assert "$1.52" in result  # best home odds
        assert "$2.50" in result  # best away odds

    def test_ac06_implied_probabilities(self, lean_tip: Tip, friday_mv: MarketView):
        """AC-06: market odds and implied probabilities shown."""
        result = format_tip_console(lean_tip, friday_mv, game_number=1)
        assert "62%" in result  # home prob
        assert "38%" in result  # away prob
        assert "after overround removal" in result

    def test_lock_colour_markup(self, lock_tip: Tip, lock_mv: MarketView):
        """AC-12: Lock tips use green colour."""
        result = format_tip_console(lock_tip, lock_mv, game_number=1)
        assert "bold green" in result

    def test_lean_colour_markup(self, lean_tip: Tip, friday_mv: MarketView):
        """AC-12: Lean tips use yellow colour."""
        result = format_tip_console(lean_tip, friday_mv, game_number=1)
        assert "bold yellow" in result

    def test_coin_flip_colour_markup(self, coin_flip_tip: Tip, saturday_mv: MarketView):
        """AC-12: Coin Flip tips use red colour."""
        result = format_tip_console(coin_flip_tip, saturday_mv, game_number=1)
        assert "bold red" in result


# ---------------------------------------------------------------------------
# Round console output tests
# ---------------------------------------------------------------------------


class TestFormatRoundConsole:
    """Tests for full round console formatting."""

    def test_ac03_header_contains_season_and_round(
        self, sample_round: RoundTips, friday_mv: MarketView, saturday_mv: MarketView
    ):
        """AC-03: header with season year and round number."""
        result = format_round_console(sample_round, [friday_mv, saturday_mv])
        assert "2025" in result
        assert "Round 1" in result

    def test_ac04_all_games_present(
        self, sample_round: RoundTips, friday_mv: MarketView, saturday_mv: MarketView
    ):
        """AC-04: each game shows up."""
        result = format_round_console(sample_round, [friday_mv, saturday_mv])
        assert "Sydney Roosters" in result
        assert "Melbourne Storm" in result
        assert "Penrith Panthers" in result

    def test_ac08_teaching_moment_appears_once(
        self, sample_round: RoundTips, friday_mv: MarketView, saturday_mv: MarketView
    ):
        """AC-08: teaching moment appears once."""
        result = format_round_console(sample_round, [friday_mv, saturday_mv])
        assert "DID YOU KNOW?" in result
        assert "teaching moment about probability" in result
        assert result.count("DID YOU KNOW?") == 1

    def test_ac10_no_results_footer(
        self, sample_round: RoundTips, friday_mv: MarketView, saturday_mv: MarketView
    ):
        """AC-10: footer shows 'No results yet' when no season record."""
        result = format_round_console(sample_round, [friday_mv, saturday_mv], season_record=None)
        assert "No results yet" in result

    def test_ac09_season_record_footer(
        self, sample_round: RoundTips, friday_mv: MarketView, saturday_mv: MarketView
    ):
        """AC-09: footer shows season record when results exist."""
        record = {
            "rounds_completed": [1],
            "overall": 0.75,
            "correct": 6,
            "total": 8,
            "by_tier": {"Lock": 1.0, "Lean": 0.667, "Coin Flip": 0.5},
        }
        result = format_round_console(sample_round, [friday_mv, saturday_mv], season_record=record)
        assert "6/8" in result
        assert "75%" in result

    def test_ac14_games_numbered_sequentially(
        self, sample_round: RoundTips, friday_mv: MarketView, saturday_mv: MarketView
    ):
        """AC-14: games numbered 1, 2, etc."""
        result = format_round_console(sample_round, [friday_mv, saturday_mv])
        assert "GAME 1" in result
        assert "GAME 2" in result

    def test_footer_quote(
        self, sample_round: RoundTips, friday_mv: MarketView, saturday_mv: MarketView
    ):
        """Footer includes Ralph's signature quote."""
        result = format_round_console(sample_round, [friday_mv, saturday_mv])
        assert "I don't know everything about footy" in result
        assert "Ralph v" in result


# ---------------------------------------------------------------------------
# Markdown output tests
# ---------------------------------------------------------------------------


class TestFormatRoundMarkdown:
    """Tests for Markdown tip sheet generation."""

    def test_ac11_valid_markdown_header(
        self, sample_round: RoundTips, friday_mv: MarketView, saturday_mv: MarketView
    ):
        """AC-11: valid Markdown with proper header."""
        md = format_round_markdown(sample_round, [friday_mv, saturday_mv])
        assert md.startswith("# RALPH")
        assert "Round 1" in md

    def test_contains_all_game_sections(
        self, sample_round: RoundTips, friday_mv: MarketView, saturday_mv: MarketView
    ):
        md = format_round_markdown(sample_round, [friday_mv, saturday_mv])
        assert "## GAME 1:" in md
        assert "## GAME 2:" in md

    def test_contains_team_names(
        self, sample_round: RoundTips, friday_mv: MarketView, saturday_mv: MarketView
    ):
        md = format_round_markdown(sample_round, [friday_mv, saturday_mv])
        assert "Sydney Roosters" in md
        assert "Brisbane Broncos" in md
        assert "Melbourne Storm" in md
        assert "Penrith Panthers" in md

    def test_contains_pick_and_confidence(
        self, sample_round: RoundTips, friday_mv: MarketView, saturday_mv: MarketView
    ):
        """AC-05: pick with confidence percentage and tier label."""
        md = format_round_markdown(sample_round, [friday_mv, saturday_mv])
        assert "**RALPH'S TIP:**" in md
        assert "Lean" in md
        assert "Coin Flip" in md

    def test_contains_venue_and_kickoff(
        self, sample_round: RoundTips, friday_mv: MarketView, saturday_mv: MarketView
    ):
        """AC-04: venue and kickoff in output."""
        md = format_round_markdown(sample_round, [friday_mv, saturday_mv])
        assert "Allianz Stadium" in md
        assert "Friday 7:55pm" in md
        assert "AAMI Park" in md
        assert "Saturday 3:00pm" in md

    def test_ac06_market_odds_and_probabilities(
        self, sample_round: RoundTips, friday_mv: MarketView, saturday_mv: MarketView
    ):
        """AC-06: market odds and implied probabilities."""
        md = format_round_markdown(sample_round, [friday_mv, saturday_mv])
        assert "**MARKET SAYS:**" in md
        assert "$1.52" in md  # best home odds for Roosters
        assert "after overround removal" in md

    def test_ac15_odds_with_dollar_sign(
        self, sample_round: RoundTips, friday_mv: MarketView, saturday_mv: MarketView
    ):
        """AC-15: odds displayed with dollar sign."""
        md = format_round_markdown(sample_round, [friday_mv, saturday_mv])
        assert "$1.52" in md
        assert "$2.50" in md

    def test_ac07_rationale_present(
        self, sample_round: RoundTips, friday_mv: MarketView, saturday_mv: MarketView
    ):
        """AC-07: rationale text in output."""
        md = format_round_markdown(sample_round, [friday_mv, saturday_mv])
        assert "**RATIONALE:**" in md
        assert "Ralph leans Roosters here." in md

    def test_ac08_teaching_moment(
        self, sample_round: RoundTips, friday_mv: MarketView, saturday_mv: MarketView
    ):
        """AC-08: teaching moment appears once, after all games."""
        md = format_round_markdown(sample_round, [friday_mv, saturday_mv])
        assert "## DID YOU KNOW?" in md
        assert "teaching moment about probability" in md
        # Teaching section should come after last game section
        last_game_pos = md.rfind("## GAME 2:")
        teaching_pos = md.find("## DID YOU KNOW?")
        assert teaching_pos > last_game_pos

    def test_ac10_no_results_footer(
        self, sample_round: RoundTips, friday_mv: MarketView, saturday_mv: MarketView
    ):
        """AC-10: 'No results yet' footer when no season record."""
        md = format_round_markdown(sample_round, [friday_mv, saturday_mv])
        assert "No results yet" in md

    def test_ac09_season_record_footer(
        self, sample_round: RoundTips, friday_mv: MarketView, saturday_mv: MarketView
    ):
        """AC-09: footer shows season record when results exist."""
        record = {
            "rounds_completed": [1],
            "overall": 0.75,
            "correct": 6,
            "total": 8,
            "by_tier": {"Lock": 1.0, "Lean": 0.667, "Coin Flip": 0.5},
        }
        md = format_round_markdown(sample_round, [friday_mv, saturday_mv], season_record=record)
        assert "6/8" in md
        assert "75%" in md

    def test_contains_separator_lines(
        self, sample_round: RoundTips, friday_mv: MarketView, saturday_mv: MarketView
    ):
        """Markdown has horizontal rule separators."""
        md = format_round_markdown(sample_round, [friday_mv, saturday_mv])
        assert "---" in md

    def test_footer_quote_and_version(
        self, sample_round: RoundTips, friday_mv: MarketView, saturday_mv: MarketView
    ):
        """Footer includes Ralph's quote and version."""
        md = format_round_markdown(sample_round, [friday_mv, saturday_mv])
        assert "I don't know everything about footy" in md
        assert "Ralph v" in md

    def test_generated_date(
        self, sample_round: RoundTips, friday_mv: MarketView, saturday_mv: MarketView
    ):
        """Header includes generated date."""
        md = format_round_markdown(sample_round, [friday_mv, saturday_mv])
        assert "Generated 2025-03-05" in md


# ---------------------------------------------------------------------------
# File output tests
# ---------------------------------------------------------------------------


class TestSaveTipSheet:
    """Tests for saving the Markdown tip sheet to disk."""

    def test_ac02_creates_file(
        self,
        tmp_path: Path,
        sample_round: RoundTips,
        friday_mv: MarketView,
        saturday_mv: MarketView,
    ):
        """AC-02: a Markdown file is created."""
        result_path = save_tip_sheet(sample_round, [friday_mv, saturday_mv], data_dir=tmp_path)
        assert result_path.exists()
        assert result_path.suffix == ".md"

    def test_filename_format(
        self,
        tmp_path: Path,
        sample_round: RoundTips,
        friday_mv: MarketView,
        saturday_mv: MarketView,
    ):
        """File is named round_01.md (zero-padded)."""
        result_path = save_tip_sheet(sample_round, [friday_mv, saturday_mv], data_dir=tmp_path)
        assert result_path.name == "round_01.md"

    def test_file_contains_markdown(
        self,
        tmp_path: Path,
        sample_round: RoundTips,
        friday_mv: MarketView,
        saturday_mv: MarketView,
    ):
        """AC-11: file contains valid Markdown."""
        result_path = save_tip_sheet(sample_round, [friday_mv, saturday_mv], data_dir=tmp_path)
        content = result_path.read_text(encoding="utf-8")
        assert content.startswith("# RALPH")
        assert "Sydney Roosters" in content
        assert "DID YOU KNOW?" in content

    def test_creates_directory_if_needed(
        self,
        tmp_path: Path,
        sample_round: RoundTips,
        friday_mv: MarketView,
        saturday_mv: MarketView,
    ):
        """Directory is created if it does not exist."""
        nested = tmp_path / "nested" / "tips"
        result_path = save_tip_sheet(sample_round, [friday_mv, saturday_mv], data_dir=nested)
        assert result_path.exists()

    def test_returns_path(
        self,
        tmp_path: Path,
        sample_round: RoundTips,
        friday_mv: MarketView,
        saturday_mv: MarketView,
    ):
        """Returns the Path of the written file."""
        result_path = save_tip_sheet(sample_round, [friday_mv, saturday_mv], data_dir=tmp_path)
        assert isinstance(result_path, Path)
        assert result_path.parent == tmp_path

    def test_round_number_padding(
        self,
        tmp_path: Path,
        friday_mv: MarketView,
        saturday_mv: MarketView,
        lean_tip: Tip,
        coin_flip_tip: Tip,
    ):
        """Round numbers are zero-padded: round_09.md, round_10.md."""
        round_tips = RoundTips(
            round_number=9,
            season=2025,
            tips=[lean_tip, coin_flip_tip],
            generated_at=datetime(2025, 3, 5, 12, 0, 0),
            teaching_moment="Test teaching.",
        )
        result_path = save_tip_sheet(round_tips, [friday_mv, saturday_mv], data_dir=tmp_path)
        assert result_path.name == "round_09.md"

        round_tips_10 = RoundTips(
            round_number=10,
            season=2025,
            tips=[lean_tip, coin_flip_tip],
            generated_at=datetime(2025, 3, 5, 12, 0, 0),
            teaching_moment="Test teaching.",
        )
        result_path_10 = save_tip_sheet(round_tips_10, [friday_mv, saturday_mv], data_dir=tmp_path)
        assert result_path_10.name == "round_10.md"
