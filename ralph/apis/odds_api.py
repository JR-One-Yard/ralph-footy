"""Live odds fetching from The Odds API.

Fetches multi-bookmaker NRL head-to-head odds and converts them
into Ralph's ``Odds`` model, ready for ``build_market_views()``.

API docs: https://the-odds-api.com/liveapi/guides/v4/
Free tier: 500 requests/month.
"""

from __future__ import annotations

import logging
import os

import requests

from ralph.models import Odds
from ralph.team_names import build_game_key

logger = logging.getLogger(__name__)

SPORT_KEY = "rugbyleague_nrl"
BASE_URL = "https://api.the-odds-api.com/v4"

# NOTE — Team name mapping
# The Odds API uses team names that may differ slightly from other data
# sources (e.g. Champion Data).  Known differences spotted so far:
#   - Odds API: "Cronulla Sharks" vs Champion Data: "Cronulla-Sutherland Sharks"
#   - Odds API: "St George Illawarra Dragons" — may match or may not
# A proper team-name normalisation layer should be built later.  For now
# the names are passed through as-is from the API response.


def get_api_key() -> str:
    """Read The Odds API key from environment or ``.env`` file.

    Checks ``os.environ["THE_ODDS_API_KEY"]`` first, then falls back to
    reading the ``.env`` file in the project root.

    Raises
    ------
    ValueError
        If the key is not found in either location.
    """
    key = os.environ.get("THE_ODDS_API_KEY")
    if key:
        return key

    # Fallback: try reading .env file from project root
    try:
        from dotenv import load_dotenv

        load_dotenv()
        key = os.environ.get("THE_ODDS_API_KEY")
        if key:
            return key
    except ImportError:
        # python-dotenv not installed — try manual parse
        env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
        env_path = os.path.normpath(env_path)
        if os.path.isfile(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("THE_ODDS_API_KEY="):
                        key = line.split("=", 1)[1].strip()
                        if key:
                            return key

    raise ValueError(
        "THE_ODDS_API_KEY not found. Set it as an environment variable "
        "or add it to the .env file in the project root."
    )


def fetch_nrl_odds(markets: str = "h2h") -> list[dict]:
    """Fetch live NRL odds from The Odds API.

    Parameters
    ----------
    markets:
        Markets to fetch (default ``"h2h"`` for head-to-head).

    Returns
    -------
    Raw JSON list of game objects from the API.

    Raises
    ------
    ValueError
        If the API key is missing.
    requests.RequestException
        If the network request fails.
    """
    api_key = get_api_key()

    url = f"{BASE_URL}/sports/{SPORT_KEY}/odds"
    params = {
        "apiKey": api_key,
        "regions": "au",
        "markets": markets,
        "oddsFormat": "decimal",
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()

    # Log API quota info from response headers
    remaining = response.headers.get("x-requests-remaining")
    used = response.headers.get("x-requests-used")
    if remaining is not None or used is not None:
        logger.info("Odds API quota — used: %s, remaining: %s", used, remaining)
        print(f"[Odds API] Requests used: {used}, remaining: {remaining}")

    return response.json()


def parse_odds_for_round(raw_odds: list[dict]) -> dict[str, list[Odds]]:
    """Convert raw API response into a dict of ``Odds`` lists keyed by game.

    The game key format is ``"HomeTeam v AwayTeam"`` to match what
    :func:`ralph.market.build_market_views` expects.

    Parameters
    ----------
    raw_odds:
        List of game dicts as returned by :func:`fetch_nrl_odds`.

    Returns
    -------
    Dict mapping game keys to lists of :class:`~ralph.models.Odds`.
    """
    odds_map: dict[str, list[Odds]] = {}

    for game in raw_odds:
        home_team = game.get("home_team", "")
        away_team = game.get("away_team", "")
        game_key = build_game_key(home_team, away_team)

        game_odds: list[Odds] = []

        for bookmaker in game.get("bookmakers", []):
            source = bookmaker.get("title", bookmaker.get("key", "unknown"))

            for market in bookmaker.get("markets", []):
                if market.get("key") != "h2h":
                    continue

                outcomes = {o["name"]: o["price"] for o in market.get("outcomes", [])}

                home_price = outcomes.get(home_team)
                away_price = outcomes.get(away_team)

                if home_price is not None and away_price is not None:
                    game_odds.append(
                        Odds(
                            home_odds=home_price,
                            away_odds=away_price,
                            source=source,
                        )
                    )

        if game_odds:
            odds_map[game_key] = game_odds

    return odds_map


def fetch_live_odds() -> dict[str, list[Odds]]:
    """Fetch and parse live NRL odds — main entry point.

    Calls :func:`fetch_nrl_odds` then :func:`parse_odds_for_round`.

    Returns
    -------
    Dict mapping game keys (``"HomeTeam v AwayTeam"``) to lists of
    :class:`~ralph.models.Odds`, compatible with
    :func:`ralph.market.build_market_views`.

    Raises
    ------
    ValueError
        If the API key is not configured.
    requests.RequestException
        If the network request fails.
    """
    raw = fetch_nrl_odds()
    return parse_odds_for_round(raw)
