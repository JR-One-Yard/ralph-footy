"""Fixture loading and validation for Ralph — NRL Footy Forecaster."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ralph.apis.champion_data import get_round_fixtures as _get_round_fixtures
from ralph.models import Game, Odds
from ralph.team_names import build_game_key

# Base directory for round fixture files, relative to project root.
_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "rounds"


def load_fixtures(
    round_number: int,
    data_dir: Path | None = None,
) -> tuple[list[Game], dict[str, list[Odds]]]:
    """Load and validate a round fixture file.

    Parameters
    ----------
    round_number:
        The round to load (1-27).
    data_dir:
        Override the default data directory (useful for testing).

    Returns
    -------
    A tuple of:
        - A list of ``Game`` objects for the round.
        - A dict mapping game keys (``"HomeTeam v AwayTeam"``) to their
          list of ``Odds`` objects.

    Raises
    ------
    ValueError
        If the file is missing, contains invalid JSON, or fails
        validation.
    """
    base = data_dir or _DATA_DIR
    filepath = base / f"round_{round_number:02d}.json"

    if not filepath.exists():
        raise ValueError(
            f"Fixture file not found: {filepath}\n"
            f"Please create {filepath} with the round's fixtures in JSON format.\n"
            f"See data/rounds/round_01.json for an example."
        )

    try:
        raw = filepath.read_text(encoding="utf-8")
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {filepath}: {exc}") from exc

    validate_fixture_data(data)

    games: list[Game] = []
    odds_map: dict[str, list[Odds]] = {}

    for idx, fixture in enumerate(data["fixtures"]):
        kickoff = _parse_kickoff(fixture["kickoff"], game_index=idx)
        game = Game(
            home_team=fixture["home_team"],
            away_team=fixture["away_team"],
            venue=fixture["venue"],
            kickoff=kickoff,
            round_number=data["round_number"],
        )
        games.append(game)

        # Parse odds if present (odds are optional at the fixture-loading
        # layer — the market engine will complain if they're absent).
        game_key = build_game_key(game.home_team, game.away_team)
        odds_list: list[Odds] = []
        for odds_entry in fixture.get("odds", []):
            odds_list.append(
                Odds(
                    home_odds=odds_entry["home_odds"],
                    away_odds=odds_entry["away_odds"],
                    source=odds_entry["source"],
                )
            )
        odds_map[game_key] = odds_list

    return games, odds_map


def validate_fixture_data(data: dict) -> None:
    """Validate the structure of parsed fixture JSON.

    Raises ``ValueError`` with a clear message on any problem.
    """
    # --- Top-level required fields ---
    for field in ("round_number", "season", "fixtures"):
        if field not in data:
            raise ValueError(f"Missing required top-level field: '{field}'")

    # --- round_number range ---
    rn = data["round_number"]
    if not isinstance(rn, int) or rn < 1 or rn > 27:
        raise ValueError(f"round_number must be an integer between 1 and 27, got {rn!r}")

    # --- season ---
    season = data["season"]
    if not isinstance(season, int) or season < 2025:
        raise ValueError(f"season must be an integer >= 2025, got {season!r}")

    # --- fixtures list ---
    fixtures = data["fixtures"]
    if not isinstance(fixtures, list) or len(fixtures) < 1:
        raise ValueError("fixtures must be a non-empty list (1-9 games per round)")
    if len(fixtures) > 9:
        raise ValueError(f"fixtures can contain at most 9 games, got {len(fixtures)}")

    # --- Per-fixture validation ---
    required_fields = ("home_team", "away_team", "venue", "kickoff")
    for idx, fixture in enumerate(fixtures):
        if not isinstance(fixture, dict):
            raise ValueError(f"Game {idx}: expected a JSON object, got {type(fixture).__name__}")
        for field in required_fields:
            if field not in fixture:
                raise ValueError(f"Game {idx}: missing required field '{field}'")
            val = fixture[field]
            if not isinstance(val, str) or not val.strip():
                raise ValueError(f"Game {idx}: '{field}' must be a non-empty string, got {val!r}")

        # Validate odds entries if present
        for oi, odds_entry in enumerate(fixture.get("odds", [])):
            if not isinstance(odds_entry, dict):
                raise ValueError(f"Game {idx}, odds {oi}: expected a JSON object")
            for ofield in ("source", "home_odds", "away_odds"):
                if ofield not in odds_entry:
                    raise ValueError(f"Game {idx}, odds {oi}: missing required field '{ofield}'")
            for ofield in ("home_odds", "away_odds"):
                val = odds_entry[ofield]
                if not isinstance(val, (int, float)) or val <= 1.0:
                    raise ValueError(
                        f"Game {idx}, odds {oi}: '{ofield}' must be a number > 1.0, got {val!r}"
                    )


def fetch_live_fixtures(round_number: int) -> list[Game]:
    """Fetch live fixtures from the Champion Data API for a round.

    This is a thin wrapper around the Champion Data client that provides
    the same return type (``list[Game]``) as the local ``load_fixtures()``
    but without odds data (odds come from a separate source).

    Parameters
    ----------
    round_number:
        The NRL round to fetch (1-27).

    Returns
    -------
    A list of ``Game`` objects for the round.

    Raises
    ------
    ValueError
        If the API returns no fixtures for the round.
    requests.RequestException
        On network errors.
    """
    games = _get_round_fixtures(round_number)
    if not games:
        raise ValueError(
            f"No fixtures returned from Champion Data for round {round_number}. "
            "The round may not exist or the API may be unavailable."
        )
    return games


def _parse_kickoff(kickoff_str: str, game_index: int = 0) -> datetime:
    """Parse an ISO 8601 kickoff string into a naive ``datetime``.

    Expected format: ``YYYY-MM-DDTHH:MM`` (no timezone).

    Raises ``ValueError`` if the string doesn't match.
    """
    try:
        return datetime.fromisoformat(kickoff_str)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Game {game_index}: invalid kickoff format '{kickoff_str}'. "
            f"Expected ISO 8601 format like '2025-03-06T20:00'. Error: {exc}"
        ) from exc
