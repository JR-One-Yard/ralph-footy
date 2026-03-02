"""Tests for the Champion Data API client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from ralph.apis.champion_data import (
    fetch_competitions,
    fetch_fixture,
    find_nrl_competition,
    get_round_fixtures,
    get_round_results,
)
from ralph.fixtures import fetch_live_fixtures
from ralph.models import Game

# ---------------------------------------------------------------------------
# Sample API responses
# ---------------------------------------------------------------------------

SAMPLE_COMPETITIONS = {
    "competitionDetails": {
        "competition": [
            {"id": 12999, "name": "2026 Telstra NRL Premiership", "season": 2026},
            {"id": 12800, "name": "2025 Telstra NRL Premiership", "season": 2025},
            {"id": 13001, "name": "2026 NSW Cup", "season": 2026},
        ]
    }
}

SAMPLE_FIXTURE = {
    "fixture": {
        "match": [
            {
                "roundNumber": 1,
                "homeSquadName": "Penrith Panthers",
                "awaySquadName": "Sydney Roosters",
                "homeSquadNickname": "Panthers",
                "awaySquadNickname": "Roosters",
                "venueName": "BlueBet Stadium",
                "utcStartTime": "2026-03-05T09:00:00Z",
                "localStartTime": "2026-03-05T20:00:00",
                "matchStatus": "upcoming",
                "homeSquadScore": 0,
                "awaySquadScore": 0,
            },
            {
                "roundNumber": 1,
                "homeSquadName": "Melbourne Storm",
                "awaySquadName": "South Sydney Rabbitohs",
                "homeSquadNickname": "Storm",
                "awaySquadNickname": "Rabbitohs",
                "venueName": "AAMI Park",
                "utcStartTime": "2026-03-06T08:00:00Z",
                "localStartTime": "2026-03-06T19:00:00",
                "matchStatus": "complete",
                "homeSquadScore": 28,
                "awaySquadScore": 16,
            },
            {
                "roundNumber": 2,
                "homeSquadName": "Brisbane Broncos",
                "awaySquadName": "North Queensland Cowboys",
                "homeSquadNickname": "Broncos",
                "awaySquadNickname": "Cowboys",
                "venueName": "Suncorp Stadium",
                "utcStartTime": "2026-03-12T09:00:00Z",
                "localStartTime": "2026-03-12T19:00:00",
                "matchStatus": "upcoming",
                "homeSquadScore": 0,
                "awaySquadScore": 0,
            },
            {
                "roundNumber": 1,
                "homeSquadName": "Canterbury-Bankstown Bulldogs",
                "awaySquadName": "Manly-Warringah Sea Eagles",
                "homeSquadNickname": "Bulldogs",
                "awaySquadNickname": "Sea Eagles",
                "venueName": "Accor Stadium",
                "utcStartTime": "2026-03-06T07:00:00",
                "localStartTime": "2026-03-06T18:00:00",
                "matchStatus": "complete",
                "homeSquadScore": 18,
                "awaySquadScore": 18,
            },
        ]
    }
}


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    """Create a mock requests.Response."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.raise_for_status.return_value = None
    return mock


# ---------------------------------------------------------------------------
# fetch_competitions
# ---------------------------------------------------------------------------


class TestFetchCompetitions:
    @patch("ralph.apis.champion_data.requests.get")
    def test_returns_competition_list(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_response(SAMPLE_COMPETITIONS)
        comps = fetch_competitions()
        assert len(comps) == 3
        assert comps[0]["id"] == 12999

    @patch("ralph.apis.champion_data.requests.get")
    def test_network_error_raises(self, mock_get: MagicMock) -> None:
        mock_get.side_effect = requests.ConnectionError("Connection refused")
        with pytest.raises(requests.RequestException, match="Failed to fetch competitions"):
            fetch_competitions()


# ---------------------------------------------------------------------------
# find_nrl_competition
# ---------------------------------------------------------------------------


class TestFindNrlCompetition:
    @patch("ralph.apis.champion_data.fetch_competitions")
    def test_finds_2026_comp(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = SAMPLE_COMPETITIONS["competitionDetails"]["competition"]
        comp_id = find_nrl_competition(season=2026)
        assert comp_id == 12999

    @patch("ralph.apis.champion_data.fetch_competitions")
    def test_finds_2025_comp(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = SAMPLE_COMPETITIONS["competitionDetails"]["competition"]
        comp_id = find_nrl_competition(season=2025)
        assert comp_id == 12800

    @patch("ralph.apis.champion_data.fetch_competitions")
    def test_missing_season_raises(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = SAMPLE_COMPETITIONS["competitionDetails"]["competition"]
        with pytest.raises(ValueError, match="Could not find an NRL Premiership"):
            find_nrl_competition(season=2024)


# ---------------------------------------------------------------------------
# fetch_fixture
# ---------------------------------------------------------------------------


class TestFetchFixture:
    @patch("ralph.apis.champion_data.requests.get")
    def test_returns_match_list(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_response(SAMPLE_FIXTURE)
        matches = fetch_fixture()
        assert len(matches) == 4

    @patch("ralph.apis.champion_data.requests.get")
    def test_network_error_raises(self, mock_get: MagicMock) -> None:
        mock_get.side_effect = requests.ConnectionError("timeout")
        with pytest.raises(requests.RequestException, match="Failed to fetch fixture"):
            fetch_fixture()


# ---------------------------------------------------------------------------
# get_round_fixtures
# ---------------------------------------------------------------------------


class TestGetRoundFixtures:
    @patch("ralph.apis.champion_data.fetch_fixture")
    def test_filters_by_round(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = SAMPLE_FIXTURE["fixture"]["match"]
        games = get_round_fixtures(round_number=1)
        assert len(games) == 3  # 3 matches in round 1

    @patch("ralph.apis.champion_data.fetch_fixture")
    def test_returns_game_objects(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = SAMPLE_FIXTURE["fixture"]["match"]
        games = get_round_fixtures(round_number=1)
        assert all(isinstance(g, Game) for g in games)

    @patch("ralph.apis.champion_data.fetch_fixture")
    def test_game_fields_populated(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = SAMPLE_FIXTURE["fixture"]["match"]
        games = get_round_fixtures(round_number=1)

        first = games[0]
        assert first.home_team == "Penrith Panthers"
        assert first.away_team == "Sydney Roosters"
        assert first.venue == "BlueBet Stadium"
        assert first.round_number == 1
        assert first.kickoff.year == 2026
        assert first.kickoff.month == 3

    @patch("ralph.apis.champion_data.fetch_fixture")
    def test_round_2_returns_one_game(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = SAMPLE_FIXTURE["fixture"]["match"]
        games = get_round_fixtures(round_number=2)
        assert len(games) == 1
        assert games[0].home_team == "Brisbane Broncos"

    @patch("ralph.apis.champion_data.fetch_fixture")
    def test_nonexistent_round_returns_empty(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = SAMPLE_FIXTURE["fixture"]["match"]
        games = get_round_fixtures(round_number=99)
        assert games == []

    @patch("ralph.apis.champion_data.fetch_fixture")
    def test_kickoff_parsed_with_z_suffix(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = SAMPLE_FIXTURE["fixture"]["match"]
        games = get_round_fixtures(round_number=1)
        # First match has "Z" suffix — should be parsed as UTC.
        assert games[0].kickoff.tzinfo is not None

    @patch("ralph.apis.champion_data.fetch_fixture")
    def test_kickoff_parsed_without_z_suffix(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = SAMPLE_FIXTURE["fixture"]["match"]
        games = get_round_fixtures(round_number=1)
        # Fourth match (index 2 in round 1) has no "Z" — should still get UTC.
        assert games[2].kickoff.tzinfo is not None


# ---------------------------------------------------------------------------
# get_round_results
# ---------------------------------------------------------------------------


class TestGetRoundResults:
    @patch("ralph.apis.champion_data.fetch_fixture")
    def test_returns_only_complete_matches(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = SAMPLE_FIXTURE["fixture"]["match"]
        results = get_round_results(round_number=1)
        # Round 1 has 3 matches but only 2 are "complete".
        assert len(results) == 2

    @patch("ralph.apis.champion_data.fetch_fixture")
    def test_result_fields(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = SAMPLE_FIXTURE["fixture"]["match"]
        results = get_round_results(round_number=1)
        storm_result = results[0]
        assert storm_result["home_team"] == "Melbourne Storm"
        assert storm_result["away_team"] == "South Sydney Rabbitohs"
        assert storm_result["home_score"] == 28
        assert storm_result["away_score"] == 16
        assert storm_result["winner"] == "Melbourne Storm"

    @patch("ralph.apis.champion_data.fetch_fixture")
    def test_draw_result(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = SAMPLE_FIXTURE["fixture"]["match"]
        results = get_round_results(round_number=1)
        draw_result = results[1]
        assert draw_result["home_score"] == 18
        assert draw_result["away_score"] == 18
        assert draw_result["winner"] == "Draw"

    @patch("ralph.apis.champion_data.fetch_fixture")
    def test_no_complete_matches(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = SAMPLE_FIXTURE["fixture"]["match"]
        results = get_round_results(round_number=2)
        assert results == []


# ---------------------------------------------------------------------------
# fetch_live_fixtures (wrapper in fixtures.py)
# ---------------------------------------------------------------------------


class TestFetchLiveFixtures:
    @patch("ralph.fixtures._get_round_fixtures")
    def test_returns_games(self, mock_get: MagicMock) -> None:
        mock_get.return_value = [
            Game(
                home_team="Penrith Panthers",
                away_team="Sydney Roosters",
                venue="BlueBet Stadium",
                kickoff=__import__("datetime").datetime(2026, 3, 5, 9, 0),
                round_number=1,
            )
        ]
        games = fetch_live_fixtures(1)
        assert len(games) == 1
        assert games[0].home_team == "Penrith Panthers"

    @patch("ralph.fixtures._get_round_fixtures")
    def test_empty_round_raises(self, mock_get: MagicMock) -> None:
        mock_get.return_value = []
        with pytest.raises(ValueError, match="No fixtures returned"):
            fetch_live_fixtures(99)
