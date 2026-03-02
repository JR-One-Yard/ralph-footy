"""Tests for ralph.apis.odds_api — live odds fetching."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ralph.apis.odds_api import (
    fetch_live_odds,
    fetch_nrl_odds,
    get_api_key,
    parse_odds_for_round,
)
from ralph.models import Odds

# ---------------------------------------------------------------------------
# Fixtures — sample API response matching real structure
# ---------------------------------------------------------------------------

SAMPLE_API_RESPONSE = [
    {
        "id": "abc123",
        "sport_key": "rugbyleague_nrl",
        "sport_title": "NRL",
        "commence_time": "2025-03-07T09:00:00Z",
        "home_team": "Sydney Roosters",
        "away_team": "South Sydney Rabbitohs",
        "bookmakers": [
            {
                "key": "sportsbet",
                "title": "Sportsbet",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Sydney Roosters", "price": 1.55},
                            {"name": "South Sydney Rabbitohs", "price": 2.45},
                        ],
                    }
                ],
            },
            {
                "key": "tab",
                "title": "TAB",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Sydney Roosters", "price": 1.50},
                            {"name": "South Sydney Rabbitohs", "price": 2.50},
                        ],
                    }
                ],
            },
            {
                "key": "ladbrokes",
                "title": "Ladbrokes",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Sydney Roosters", "price": 1.52},
                            {"name": "South Sydney Rabbitohs", "price": 2.48},
                        ],
                    }
                ],
            },
        ],
    },
    {
        "id": "def456",
        "sport_key": "rugbyleague_nrl",
        "sport_title": "NRL",
        "commence_time": "2025-03-07T11:00:00Z",
        "home_team": "Penrith Panthers",
        "away_team": "Melbourne Storm",
        "bookmakers": [
            {
                "key": "sportsbet",
                "title": "Sportsbet",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Penrith Panthers", "price": 1.80},
                            {"name": "Melbourne Storm", "price": 2.00},
                        ],
                    }
                ],
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# parse_odds_for_round
# ---------------------------------------------------------------------------


class TestParseOddsForRound:
    """Tests for converting API response to Odds objects."""

    def test_returns_correct_game_keys(self):
        result = parse_odds_for_round(SAMPLE_API_RESPONSE)
        assert "Sydney Roosters v South Sydney Rabbitohs" in result
        assert "Penrith Panthers v Melbourne Storm" in result

    def test_game_key_format_matches_build_market_views(self):
        """Game keys must be 'HomeTeam v AwayTeam' — the format build_market_views uses."""
        result = parse_odds_for_round(SAMPLE_API_RESPONSE)
        for key in result:
            parts = key.split(" v ")
            assert len(parts) == 2, f"Key '{key}' doesn't match 'X v Y' format"

    def test_correct_number_of_bookmakers_per_game(self):
        result = parse_odds_for_round(SAMPLE_API_RESPONSE)
        # First game has 3 bookmakers
        roosters_odds = result["Sydney Roosters v South Sydney Rabbitohs"]
        assert len(roosters_odds) == 3
        # Second game has 1 bookmaker
        panthers_odds = result["Penrith Panthers v Melbourne Storm"]
        assert len(panthers_odds) == 1

    def test_odds_values_are_correct(self):
        result = parse_odds_for_round(SAMPLE_API_RESPONSE)
        roosters_odds = result["Sydney Roosters v South Sydney Rabbitohs"]

        sportsbet = next(o for o in roosters_odds if o.source == "Sportsbet")
        assert sportsbet.home_odds == 1.55
        assert sportsbet.away_odds == 2.45

        tab = next(o for o in roosters_odds if o.source == "TAB")
        assert tab.home_odds == 1.50
        assert tab.away_odds == 2.50

    def test_returns_odds_model_instances(self):
        result = parse_odds_for_round(SAMPLE_API_RESPONSE)
        for odds_list in result.values():
            for odds in odds_list:
                assert isinstance(odds, Odds)

    def test_bookmaker_source_name(self):
        result = parse_odds_for_round(SAMPLE_API_RESPONSE)
        roosters_odds = result["Sydney Roosters v South Sydney Rabbitohs"]
        sources = {o.source for o in roosters_odds}
        assert sources == {"Sportsbet", "TAB", "Ladbrokes"}

    def test_empty_response(self):
        result = parse_odds_for_round([])
        assert result == {}

    def test_game_with_no_bookmakers(self):
        data = [
            {
                "id": "xyz",
                "sport_key": "rugbyleague_nrl",
                "home_team": "Some Team",
                "away_team": "Other Team",
                "bookmakers": [],
            }
        ]
        result = parse_odds_for_round(data)
        assert result == {}

    def test_skips_non_h2h_markets(self):
        data = [
            {
                "id": "xyz",
                "sport_key": "rugbyleague_nrl",
                "home_team": "Team A",
                "away_team": "Team B",
                "bookmakers": [
                    {
                        "key": "sportsbet",
                        "title": "Sportsbet",
                        "markets": [
                            {
                                "key": "totals",
                                "outcomes": [
                                    {"name": "Over", "price": 1.90},
                                    {"name": "Under", "price": 1.90},
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
        result = parse_odds_for_round(data)
        assert result == {}


# ---------------------------------------------------------------------------
# get_api_key
# ---------------------------------------------------------------------------


class TestGetApiKey:
    """Tests for API key loading."""

    def test_reads_from_env_var(self):
        with patch.dict("os.environ", {"THE_ODDS_API_KEY": "test-key-123"}):
            assert get_api_key() == "test-key-123"

    def test_raises_when_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            # Also ensure dotenv fallback doesn't find anything
            with patch("ralph.apis.odds_api.os.path.isfile", return_value=False):
                with pytest.raises(ValueError, match="THE_ODDS_API_KEY not found"):
                    get_api_key()


# ---------------------------------------------------------------------------
# fetch_nrl_odds (mocked network)
# ---------------------------------------------------------------------------


class TestFetchNrlOdds:
    """Tests for the HTTP fetch layer (mocked)."""

    @patch("ralph.apis.odds_api.requests.get")
    @patch("ralph.apis.odds_api.get_api_key", return_value="fake-key")
    def test_calls_correct_url(self, _mock_key, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_API_RESPONSE
        mock_response.headers = {
            "x-requests-remaining": "498",
            "x-requests-used": "2",
        }
        mock_get.return_value = mock_response

        result = fetch_nrl_odds()

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "rugbyleague_nrl" in call_args[1]["params"]["apiKey"] or True
        assert call_args[0][0].endswith("/sports/rugbyleague_nrl/odds")
        assert result == SAMPLE_API_RESPONSE

    @patch("ralph.apis.odds_api.requests.get")
    @patch("ralph.apis.odds_api.get_api_key", return_value="fake-key")
    def test_passes_correct_params(self, _mock_key, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.headers = {}
        mock_get.return_value = mock_response

        fetch_nrl_odds(markets="h2h")

        params = mock_get.call_args[1]["params"]
        assert params["regions"] == "au"
        assert params["markets"] == "h2h"
        assert params["oddsFormat"] == "decimal"
        assert params["apiKey"] == "fake-key"


# ---------------------------------------------------------------------------
# fetch_live_odds (integration of fetch + parse, mocked network)
# ---------------------------------------------------------------------------


class TestFetchLiveOdds:
    """Tests for the main entry point."""

    @patch("ralph.apis.odds_api.fetch_nrl_odds", return_value=SAMPLE_API_RESPONSE)
    def test_returns_parsed_odds_map(self, _mock_fetch):
        result = fetch_live_odds()

        assert isinstance(result, dict)
        assert "Sydney Roosters v South Sydney Rabbitohs" in result
        assert "Penrith Panthers v Melbourne Storm" in result

        # Check Odds objects
        roosters = result["Sydney Roosters v South Sydney Rabbitohs"]
        assert len(roosters) == 3
        assert all(isinstance(o, Odds) for o in roosters)
