"""Tests for ralph.fixtures — fixture loading and validation.

Each test maps to one or more acceptance criteria from spec 01_check_fixtures.md.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from ralph.fixtures import _parse_kickoff, load_fixtures, validate_fixture_data
from ralph.models import Game, Odds

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_fixture(tmp_path: Path, data: dict, round_number: int = 1) -> Path:
    """Write a fixture dict as JSON to a temp directory and return the dir."""
    filepath = tmp_path / f"round_{round_number:02d}.json"
    filepath.write_text(json.dumps(data), encoding="utf-8")
    return tmp_path


def _valid_fixture_data(
    round_number: int = 1,
    season: int = 2025,
    num_games: int = 2,
) -> dict:
    """Return a minimal valid fixture dict with *num_games* games."""
    teams = [
        ("Sydney Roosters", "Brisbane Broncos", "Allianz Stadium"),
        ("Melbourne Storm", "Canterbury Bulldogs", "AAMI Park"),
        ("Penrith Panthers", "Cronulla Sharks", "BlueBet Stadium"),
        ("Parramatta Eels", "North Queensland Cowboys", "CommBank Stadium"),
        ("Gold Coast Titans", "Wests Tigers", "Cbus Super Stadium"),
        ("Manly Sea Eagles", "South Sydney Rabbitohs", "4 Pines Park"),
        ("Canberra Raiders", "New Zealand Warriors", "GIO Stadium"),
        ("Newcastle Knights", "St George Illawarra Dragons", "McDonald Jones Stadium"),
        ("Dolphins", "Wests Tigers", "Suncorp Stadium"),
    ]
    fixtures = []
    for i in range(num_games):
        home, away, venue = teams[i % len(teams)]
        fixtures.append(
            {
                "home_team": home,
                "away_team": away,
                "venue": venue,
                "kickoff": f"2025-03-{6 + i:02d}T20:00",
                "odds": [
                    {"source": "Sportsbet", "home_odds": 1.55, "away_odds": 2.50},
                    {"source": "TAB", "home_odds": 1.52, "away_odds": 2.55},
                ],
            }
        )
    return {"round_number": round_number, "season": season, "fixtures": fixtures}


# ===========================================================================
# AC-01: Valid fixture file returns list of Game objects
# ===========================================================================


class TestAC01ValidFixtureLoading:
    def test_loads_correct_number_of_games(self, tmp_path: Path) -> None:
        data = _valid_fixture_data(num_games=3)
        data_dir = _write_fixture(tmp_path, data)
        games, odds_map = load_fixtures(1, data_dir=data_dir)
        assert len(games) == 3

    def test_game_fields_match_file(self, tmp_path: Path) -> None:
        data = _valid_fixture_data(num_games=1)
        data_dir = _write_fixture(tmp_path, data)
        games, _ = load_fixtures(1, data_dir=data_dir)
        game = games[0]
        assert isinstance(game, Game)
        assert game.home_team == "Sydney Roosters"
        assert game.away_team == "Brisbane Broncos"
        assert game.venue == "Allianz Stadium"

    def test_odds_returned_for_each_game(self, tmp_path: Path) -> None:
        data = _valid_fixture_data(num_games=2)
        data_dir = _write_fixture(tmp_path, data)
        games, odds_map = load_fixtures(1, data_dir=data_dir)
        assert len(odds_map) == 2
        key = f"{games[0].home_team} v {games[0].away_team}"
        assert key in odds_map
        assert len(odds_map[key]) == 2
        assert all(isinstance(o, Odds) for o in odds_map[key])

    def test_round_01_real_file(self) -> None:
        """Integration: load the actual round_01.json from the project data directory."""
        games, odds_map = load_fixtures(1)
        assert len(games) == 8
        assert all(isinstance(g, Game) for g in games)
        assert len(odds_map) == 8


# ===========================================================================
# AC-02: Missing required field raises ValueError with field name & index
# ===========================================================================


class TestAC02MissingRequiredField:
    @pytest.mark.parametrize("missing_field", ["home_team", "away_team", "venue", "kickoff"])
    def test_missing_fixture_field(self, tmp_path: Path, missing_field: str) -> None:
        data = _valid_fixture_data(num_games=1)
        del data["fixtures"][0][missing_field]
        data_dir = _write_fixture(tmp_path, data)
        with pytest.raises(ValueError, match=f"Game 0.*missing required field '{missing_field}'"):
            load_fixtures(1, data_dir=data_dir)

    def test_empty_string_field_raises(self, tmp_path: Path) -> None:
        data = _valid_fixture_data(num_games=1)
        data["fixtures"][0]["venue"] = ""
        data_dir = _write_fixture(tmp_path, data)
        with pytest.raises(ValueError, match="Game 0.*'venue'.*non-empty string"):
            load_fixtures(1, data_dir=data_dir)

    @pytest.mark.parametrize("missing_field", ["round_number", "season", "fixtures"])
    def test_missing_top_level_field(self, tmp_path: Path, missing_field: str) -> None:
        data = _valid_fixture_data(num_games=1)
        del data[missing_field]
        with pytest.raises(
            ValueError, match=f"Missing required top-level field: '{missing_field}'"
        ):
            validate_fixture_data(data)


# ===========================================================================
# AC-03: Invalid kickoff format raises ValueError with expected format
# ===========================================================================


class TestAC03InvalidKickoffFormat:
    def test_bad_kickoff_string(self, tmp_path: Path) -> None:
        data = _valid_fixture_data(num_games=1)
        data["fixtures"][0]["kickoff"] = "Friday 8pm"
        data_dir = _write_fixture(tmp_path, data)
        with pytest.raises(ValueError, match="invalid kickoff format.*Friday 8pm"):
            load_fixtures(1, data_dir=data_dir)

    def test_bad_kickoff_explains_expected_format(self, tmp_path: Path) -> None:
        data = _valid_fixture_data(num_games=1)
        data["fixtures"][0]["kickoff"] = "not-a-date"
        data_dir = _write_fixture(tmp_path, data)
        with pytest.raises(ValueError, match="ISO 8601"):
            load_fixtures(1, data_dir=data_dir)


# ===========================================================================
# AC-04: round_number outside 1-27 raises ValueError
# ===========================================================================


class TestAC04RoundNumberRange:
    def test_round_number_zero(self, tmp_path: Path) -> None:
        data = _valid_fixture_data(round_number=0)
        with pytest.raises(ValueError, match="round_number must be an integer between 1 and 27"):
            validate_fixture_data(data)

    def test_round_number_28(self, tmp_path: Path) -> None:
        data = _valid_fixture_data(round_number=28)
        with pytest.raises(ValueError, match="round_number must be an integer between 1 and 27"):
            validate_fixture_data(data)

    def test_round_number_negative(self) -> None:
        data = _valid_fixture_data(round_number=-1)
        with pytest.raises(ValueError, match="round_number must be an integer between 1 and 27"):
            validate_fixture_data(data)

    def test_round_number_1_valid(self) -> None:
        data = _valid_fixture_data(round_number=1)
        validate_fixture_data(data)  # Should not raise

    def test_round_number_27_valid(self) -> None:
        data = _valid_fixture_data(round_number=27)
        validate_fixture_data(data)  # Should not raise


# ===========================================================================
# AC-05: CLI round number maps to correct filename
# ===========================================================================


class TestAC05FilePathResolution:
    def test_round_1_maps_to_round_01_json(self, tmp_path: Path) -> None:
        data = _valid_fixture_data(round_number=1)
        _write_fixture(tmp_path, data, round_number=1)
        games, _ = load_fixtures(1, data_dir=tmp_path)
        assert len(games) > 0

    def test_round_12_maps_to_round_12_json(self, tmp_path: Path) -> None:
        data = _valid_fixture_data(round_number=12)
        _write_fixture(tmp_path, data, round_number=12)
        games, _ = load_fixtures(12, data_dir=tmp_path)
        assert len(games) > 0


# ===========================================================================
# AC-06: Missing file gives clear error message
# ===========================================================================


class TestAC06MissingFile:
    def test_missing_file_raises_value_error(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="Fixture file not found"):
            load_fixtures(99, data_dir=tmp_path)

    def test_missing_file_mentions_expected_path(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="round_99.json"):
            load_fixtures(99, data_dir=tmp_path)

    def test_missing_file_mentions_example(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="example"):
            load_fixtures(99, data_dir=tmp_path)


# ===========================================================================
# AC-07: kickoff string parsed into Python datetime
# ===========================================================================


class TestAC07KickoffParsing:
    def test_iso_format_parsed(self) -> None:
        result = _parse_kickoff("2025-03-06T20:00")
        assert isinstance(result, datetime)
        assert result == datetime(2025, 3, 6, 20, 0)

    def test_kickoff_with_minutes(self) -> None:
        result = _parse_kickoff("2025-03-07T19:55")
        assert result == datetime(2025, 3, 7, 19, 55)

    def test_kickoff_in_loaded_game(self, tmp_path: Path) -> None:
        data = _valid_fixture_data(num_games=1)
        data["fixtures"][0]["kickoff"] = "2025-03-06T20:00"
        data_dir = _write_fixture(tmp_path, data)
        games, _ = load_fixtures(1, data_dir=data_dir)
        assert games[0].kickoff == datetime(2025, 3, 6, 20, 0)


# ===========================================================================
# AC-08: round_number from file injected into each Game
# ===========================================================================


class TestAC08RoundNumberInjected:
    def test_round_number_set_on_game(self, tmp_path: Path) -> None:
        data = _valid_fixture_data(round_number=5, num_games=3)
        data_dir = _write_fixture(tmp_path, data, round_number=5)
        games, _ = load_fixtures(5, data_dir=data_dir)
        for game in games:
            assert game.round_number == 5

    def test_round_number_varies(self, tmp_path: Path) -> None:
        data = _valid_fixture_data(round_number=15, num_games=2)
        data_dir = _write_fixture(tmp_path, data, round_number=15)
        games, _ = load_fixtures(15, data_dir=data_dir)
        assert all(g.round_number == 15 for g in games)


# ===========================================================================
# AC-09: Fixture files with 1-9 games are accepted (bye rounds)
# ===========================================================================


class TestAC09GameCountRange:
    def test_single_game_accepted(self, tmp_path: Path) -> None:
        data = _valid_fixture_data(num_games=1)
        data_dir = _write_fixture(tmp_path, data)
        games, _ = load_fixtures(1, data_dir=data_dir)
        assert len(games) == 1

    def test_nine_games_accepted(self, tmp_path: Path) -> None:
        data = _valid_fixture_data(num_games=9)
        data_dir = _write_fixture(tmp_path, data)
        games, _ = load_fixtures(1, data_dir=data_dir)
        assert len(games) == 9

    def test_eight_games_full_round(self, tmp_path: Path) -> None:
        data = _valid_fixture_data(num_games=8)
        data_dir = _write_fixture(tmp_path, data)
        games, _ = load_fixtures(1, data_dir=data_dir)
        assert len(games) == 8

    def test_zero_games_rejected(self, tmp_path: Path) -> None:
        data = _valid_fixture_data(num_games=0)
        data["fixtures"] = []
        with pytest.raises(ValueError, match="non-empty list"):
            validate_fixture_data(data)

    def test_ten_games_rejected(self, tmp_path: Path) -> None:
        data = _valid_fixture_data(num_games=9)
        # Add a 10th game manually
        data["fixtures"].append(data["fixtures"][0].copy())
        with pytest.raises(ValueError, match="at most 9 games"):
            validate_fixture_data(data)


# ===========================================================================
# Additional edge-case tests
# ===========================================================================


class TestInvalidJson:
    def test_corrupt_json_raises_value_error(self, tmp_path: Path) -> None:
        filepath = tmp_path / "round_01.json"
        filepath.write_text("{bad json!!!", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_fixtures(1, data_dir=tmp_path)


class TestOddsValidation:
    def test_odds_at_or_below_one_rejected(self, tmp_path: Path) -> None:
        data = _valid_fixture_data(num_games=1)
        data["fixtures"][0]["odds"][0]["home_odds"] = 1.0
        with pytest.raises(ValueError, match="must be a number > 1.0"):
            validate_fixture_data(data)

    def test_odds_negative_rejected(self, tmp_path: Path) -> None:
        data = _valid_fixture_data(num_games=1)
        data["fixtures"][0]["odds"][0]["away_odds"] = -0.5
        with pytest.raises(ValueError, match="must be a number > 1.0"):
            validate_fixture_data(data)

    def test_odds_without_source_rejected(self, tmp_path: Path) -> None:
        data = _valid_fixture_data(num_games=1)
        del data["fixtures"][0]["odds"][0]["source"]
        with pytest.raises(ValueError, match="missing required field 'source'"):
            validate_fixture_data(data)
