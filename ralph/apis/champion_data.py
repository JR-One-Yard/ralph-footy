"""Champion Data API client for live NRL fixture and result data."""

from __future__ import annotations

from datetime import datetime, timezone

import requests

from ralph.models import Game

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://mc.championdata.com/data"
COMP_ID_NRL_2026 = 12999

# Request timeout in seconds.
_TIMEOUT = 15


# ---------------------------------------------------------------------------
# Low-level fetchers
# ---------------------------------------------------------------------------


def fetch_competitions() -> list[dict]:
    """Fetch the full list of competitions from Champion Data.

    Returns a list of competition dicts, each containing keys like
    ``id``, ``name``, ``season``, and ``rounds``.

    Raises
    ------
    requests.RequestException
        On any network / HTTP error (wrapped with a friendly message).
    """
    url = f"{BASE_URL}/competitions.json"
    try:
        resp = requests.get(url, timeout=_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise requests.RequestException(
            f"Failed to fetch competitions from Champion Data ({url}): {exc}"
        ) from exc

    data = resp.json()
    return data["competitionDetails"]["competition"]


def find_nrl_competition(season: int = 2026) -> int:
    """Find the Champion Data competition ID for a given NRL season.

    Parameters
    ----------
    season:
        The year to search for (default 2026).

    Returns
    -------
    The integer competition ID.

    Raises
    ------
    ValueError
        If no matching NRL premiership competition is found for the season.
    """
    competitions = fetch_competitions()
    for comp in competitions:
        name = comp.get("name", "").lower()
        comp_season = comp.get("season")
        if "nrl premiership" in name and str(comp_season) == str(season):
            return int(comp["id"])

    raise ValueError(
        f"Could not find an NRL Premiership competition for season {season}. "
        f"Available competitions: {[c.get('name') for c in competitions]}"
    )


def fetch_fixture(comp_id: int = COMP_ID_NRL_2026) -> list[dict]:
    """Fetch the full fixture list for a competition.

    Parameters
    ----------
    comp_id:
        The Champion Data competition ID (default: 2026 NRL).

    Returns
    -------
    A list of match dicts straight from the API.
    """
    url = f"{BASE_URL}/{comp_id}/fixture.json"
    try:
        resp = requests.get(url, timeout=_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise requests.RequestException(
            f"Failed to fetch fixture from Champion Data ({url}): {exc}"
        ) from exc

    data = resp.json()
    return data["fixture"]["match"]


# ---------------------------------------------------------------------------
# Higher-level helpers
# ---------------------------------------------------------------------------


def _parse_utc_kickoff(utc_str: str) -> datetime:
    """Parse a Champion Data ``utcStartTime`` into a timezone-aware datetime.

    The API returns ISO 8601 strings like ``"2026-03-05T09:00:00Z"`` or
    ``"2026-03-05T09:00:00"``.  We normalise to a UTC-aware datetime.
    """
    # Strip trailing 'Z' if present and parse.
    cleaned = utc_str.replace("Z", "+00:00") if utc_str.endswith("Z") else utc_str
    dt = datetime.fromisoformat(cleaned)
    # If the API omitted timezone info, assume UTC.
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _match_to_game(match: dict, round_number: int) -> Game:
    """Convert a single Champion Data match dict into a ``Game`` object."""
    # Prefer full squad name (e.g. "Newcastle Knights"), fall back to nickname.
    home = match.get("homeSquadName") or match.get("homeSquadNickname", "Unknown")
    away = match.get("awaySquadName") or match.get("awaySquadNickname", "Unknown")
    venue = match.get("venueName", "TBC")

    kickoff = _parse_utc_kickoff(match["utcStartTime"])

    return Game(
        home_team=home,
        away_team=away,
        venue=venue,
        kickoff=kickoff,
        round_number=round_number,
    )


def get_round_fixtures(
    round_number: int,
    comp_id: int = COMP_ID_NRL_2026,
) -> list[Game]:
    """Fetch fixtures for a specific round and return as ``Game`` objects.

    Parameters
    ----------
    round_number:
        The NRL round number (1-27).
    comp_id:
        Champion Data competition ID.

    Returns
    -------
    A list of ``Game`` objects for the requested round.
    """
    matches = fetch_fixture(comp_id)
    round_matches = [m for m in matches if m.get("roundNumber") == round_number]
    return [_match_to_game(m, round_number) for m in round_matches]


def get_round_results(
    round_number: int,
    comp_id: int = COMP_ID_NRL_2026,
) -> list[dict]:
    """Fetch completed results for a specific round.

    Parameters
    ----------
    round_number:
        The NRL round number (1-27).
    comp_id:
        Champion Data competition ID.

    Returns
    -------
    A list of result dicts, each with keys:
    ``home_team``, ``away_team``, ``home_score``, ``away_score``, ``winner``.
    Only matches with ``matchStatus == "complete"`` are included.
    """
    matches = fetch_fixture(comp_id)
    results: list[dict] = []

    for m in matches:
        if m.get("roundNumber") != round_number:
            continue
        if m.get("matchStatus", "").lower() != "complete":
            continue

        home = m.get("homeSquadName") or m.get("homeSquadNickname", "Unknown")
        away = m.get("awaySquadName") or m.get("awaySquadNickname", "Unknown")
        home_score = int(m.get("homeSquadScore", 0))
        away_score = int(m.get("awaySquadScore", 0))

        if home_score > away_score:
            winner = home
        elif away_score > home_score:
            winner = away
        else:
            winner = "Draw"

        results.append(
            {
                "home_team": home,
                "away_team": away,
                "home_score": home_score,
                "away_score": away_score,
                "winner": winner,
            }
        )

    return results
