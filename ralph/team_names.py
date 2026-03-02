"""Team name normalisation for cross-source matching.

Champion Data and The Odds API use different team names for the same
NRL clubs.  This module provides a canonical mapping so fixtures and
odds can be reliably joined by a normalised game key.

Strategy:
1. Replace hyphens with spaces.
2. Look up the result in ``TEAM_ALIASES``.
3. If no alias is found, return the hyphen-stripped name as-is.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Canonical alias map
# ---------------------------------------------------------------------------
# Keys are known variations (after hyphen → space conversion).
# Values are the canonical name Ralph uses internally.
#
# We map *towards* the Odds API spelling because that source is less
# controllable (third-party API), whereas Champion Data names are more
# predictable.

TEAM_ALIASES: dict[str, str] = {
    # Champion Data long-form → Odds API form
    "Canterbury Bankstown Bulldogs": "Canterbury Bulldogs",
    # Champion Data short nicknames
    "Warriors": "New Zealand Warriors",
    "Bulldogs": "Canterbury Bulldogs",
    "Sharks": "Cronulla Sutherland Sharks",
    "Sea Eagles": "Manly Warringah Sea Eagles",
    "Storm": "Melbourne Storm",
    "Broncos": "Brisbane Broncos",
    "Roosters": "Sydney Roosters",
    "Panthers": "Penrith Panthers",
    "Eels": "Parramatta Eels",
    "Raiders": "Canberra Raiders",
    "Tigers": "Wests Tigers",
    "Cowboys": "North Queensland Cowboys",
    "Titans": "Gold Coast Titans",
    "Knights": "Newcastle Knights",
    "Dragons": "St George Illawarra Dragons",
    "Rabbitohs": "South Sydney Rabbitohs",
    # Odds API occasional variants
    "Cronulla Sharks": "Cronulla Sutherland Sharks",
}


def normalise_team_name(name: str) -> str:
    """Return the canonical team name for *name*.

    1. Strip leading/trailing whitespace.
    2. Replace hyphens with spaces (handles "Canterbury-Bankstown").
    3. Look up in ``TEAM_ALIASES``; return the canonical form if found.
    4. Otherwise return the hyphen-stripped name unchanged.
    """
    cleaned = name.strip().replace("-", " ")
    return TEAM_ALIASES.get(cleaned, cleaned)


def build_game_key(home: str, away: str) -> str:
    """Build a normalised game key: ``"NormalisedHome v NormalisedAway"``."""
    return f"{normalise_team_name(home)} v {normalise_team_name(away)}"
