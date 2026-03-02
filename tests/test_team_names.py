"""Tests for ralph.team_names — team name normalisation and game key matching."""

from __future__ import annotations

import pytest

from ralph.team_names import TEAM_ALIASES, build_game_key, normalise_team_name

# ---------------------------------------------------------------------------
# normalise_team_name
# ---------------------------------------------------------------------------


class TestNormaliseTeamName:
    """Tests for normalise_team_name()."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            # Champion Data hyphenated → canonical
            ("Canterbury-Bankstown Bulldogs", "Canterbury Bulldogs"),
            ("Cronulla-Sutherland Sharks", "Cronulla Sutherland Sharks"),
            ("Manly-Warringah Sea Eagles", "Manly Warringah Sea Eagles"),
            # Short nickname → canonical
            ("Warriors", "New Zealand Warriors"),
            ("Bulldogs", "Canterbury Bulldogs"),
            ("Sharks", "Cronulla Sutherland Sharks"),
            ("Sea Eagles", "Manly Warringah Sea Eagles"),
            # Odds API variant
            ("Cronulla Sharks", "Cronulla Sutherland Sharks"),
            # Already-canonical names pass through unchanged
            ("Melbourne Storm", "Melbourne Storm"),
            ("Brisbane Broncos", "Brisbane Broncos"),
            ("Sydney Roosters", "Sydney Roosters"),
            ("Penrith Panthers", "Penrith Panthers"),
            ("Parramatta Eels", "Parramatta Eels"),
            ("Canberra Raiders", "Canberra Raiders"),
            ("Wests Tigers", "Wests Tigers"),
            ("North Queensland Cowboys", "North Queensland Cowboys"),
            ("Gold Coast Titans", "Gold Coast Titans"),
            ("Newcastle Knights", "Newcastle Knights"),
            ("St George Illawarra Dragons", "St George Illawarra Dragons"),
            ("South Sydney Rabbitohs", "South Sydney Rabbitohs"),
            ("Dolphins", "Dolphins"),
            ("New Zealand Warriors", "New Zealand Warriors"),
            ("Canterbury Bulldogs", "Canterbury Bulldogs"),
            ("Cronulla Sutherland Sharks", "Cronulla Sutherland Sharks"),
            ("Manly Warringah Sea Eagles", "Manly Warringah Sea Eagles"),
        ],
    )
    def test_known_aliases(self, raw: str, expected: str) -> None:
        assert normalise_team_name(raw) == expected

    def test_strips_whitespace(self) -> None:
        assert normalise_team_name("  Warriors  ") == "New Zealand Warriors"

    def test_unknown_name_passes_through(self) -> None:
        assert normalise_team_name("Made Up Koalas") == "Made Up Koalas"


# ---------------------------------------------------------------------------
# build_game_key
# ---------------------------------------------------------------------------


class TestBuildGameKey:
    """Tests for build_game_key()."""

    def test_basic_key(self) -> None:
        key = build_game_key("Melbourne Storm", "Brisbane Broncos")
        assert key == "Melbourne Storm v Brisbane Broncos"

    def test_normalises_both_sides(self) -> None:
        # Champion Data style on both sides
        key = build_game_key("Canterbury-Bankstown Bulldogs", "Cronulla-Sutherland Sharks")
        assert key == "Canterbury Bulldogs v Cronulla Sutherland Sharks"

    def test_champion_data_matches_odds_api(self) -> None:
        """A Champion Data key and an Odds API key should produce the same result."""
        cd_key = build_game_key("Manly-Warringah Sea Eagles", "Warriors")
        odds_key = build_game_key("Manly Warringah Sea Eagles", "New Zealand Warriors")
        assert cd_key == odds_key

    def test_cronulla_variant_match(self) -> None:
        """Cronulla Sharks (Odds API) matches Cronulla-Sutherland Sharks (CD)."""
        cd_key = build_game_key("Cronulla-Sutherland Sharks", "Melbourne Storm")
        odds_key = build_game_key("Cronulla Sharks", "Melbourne Storm")
        assert cd_key == odds_key


# ---------------------------------------------------------------------------
# TEAM_ALIASES completeness
# ---------------------------------------------------------------------------


def test_aliases_are_not_self_referential() -> None:
    """Canonical names should not appear as both key and value (no loops)."""
    for key in TEAM_ALIASES:
        # It's fine for a value to also be a key (e.g. a chain), but
        # a key mapping to itself is useless.
        assert TEAM_ALIASES[key] != key, f"Self-referential alias: {key}"


def test_canonical_names_are_stable() -> None:
    """Normalising an already-canonical name should return it unchanged."""
    canonical_names = set(TEAM_ALIASES.values())
    for name in canonical_names:
        assert normalise_team_name(name) == name, (
            f"Canonical name '{name}' changed after normalisation"
        )
