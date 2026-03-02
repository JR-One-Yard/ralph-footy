"""Shared pytest fixtures for Ralph tests."""

from __future__ import annotations

from datetime import datetime

import pytest

from ralph.models import Game, MarketView, Odds, RoundTips, Tip

# ---------------------------------------------------------------------------
# Game fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_game() -> Game:
    """A single NRL fixture: Roosters vs Broncos at Allianz Stadium."""
    return Game(
        home_team="Sydney Roosters",
        away_team="Brisbane Broncos",
        venue="Allianz Stadium",
        kickoff=datetime(2025, 3, 6, 20, 0),
        round_number=1,
    )


@pytest.fixture()
def sample_game_close() -> Game:
    """A tight contest: Storm vs Panthers at AAMI Park."""
    return Game(
        home_team="Melbourne Storm",
        away_team="Penrith Panthers",
        venue="AAMI Park",
        kickoff=datetime(2025, 3, 7, 19, 55),
        round_number=1,
    )


@pytest.fixture()
def sample_games(sample_game: Game, sample_game_close: Game) -> list[Game]:
    """A list of two NRL fixtures for round 1."""
    return [sample_game, sample_game_close]


# ---------------------------------------------------------------------------
# Odds fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_odds_sportsbet() -> Odds:
    """Sportsbet odds: Roosters $1.55, Broncos $2.50."""
    return Odds(home_odds=1.55, away_odds=2.50, source="Sportsbet")


@pytest.fixture()
def sample_odds_tab() -> Odds:
    """TAB odds: Roosters $1.52, Broncos $2.55."""
    return Odds(home_odds=1.52, away_odds=2.55, source="TAB")


@pytest.fixture()
def sample_odds_list(sample_odds_sportsbet: Odds, sample_odds_tab: Odds) -> list[Odds]:
    """Multi-bookmaker odds for the Roosters vs Broncos game."""
    return [sample_odds_sportsbet, sample_odds_tab]


@pytest.fixture()
def sample_odds_close() -> list[Odds]:
    """Tight-contest odds for Storm vs Panthers."""
    return [
        Odds(home_odds=1.90, away_odds=1.90, source="Sportsbet"),
        Odds(home_odds=1.87, away_odds=1.93, source="TAB"),
    ]


# ---------------------------------------------------------------------------
# MarketView fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_market_view(sample_game: Game, sample_odds_list: list[Odds]) -> MarketView:
    """MarketView for Roosters vs Broncos — Roosters are clear favourite."""
    return MarketView(
        game=sample_game,
        odds_sources=sample_odds_list,
        consensus_home_prob=0.6173,
        consensus_away_prob=0.3827,
    )


@pytest.fixture()
def sample_market_view_close(sample_game_close: Game, sample_odds_close: list[Odds]) -> MarketView:
    """MarketView for Storm vs Panthers — near coin-flip."""
    return MarketView(
        game=sample_game_close,
        odds_sources=sample_odds_close,
        consensus_home_prob=0.51,
        consensus_away_prob=0.49,
    )


@pytest.fixture()
def sample_market_view_lock(sample_game: Game, sample_odds_list: list[Odds]) -> MarketView:
    """MarketView where the favourite has Lock-level confidence (>=70%)."""
    return MarketView(
        game=sample_game,
        odds_sources=sample_odds_list,
        consensus_home_prob=0.75,
        consensus_away_prob=0.25,
    )


@pytest.fixture()
def sample_market_views(
    sample_market_view: MarketView, sample_market_view_close: MarketView
) -> list[MarketView]:
    """A list of MarketView objects for a partial round."""
    return [sample_market_view, sample_market_view_close]


# ---------------------------------------------------------------------------
# Tip fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_tip_lock(sample_game: Game) -> Tip:
    """A Lock-tier tip (confidence >= 0.70)."""
    return Tip(
        game=sample_game,
        pick="Sydney Roosters",
        confidence=0.75,
        rationale="",
        teaching_moment="",
    )


@pytest.fixture()
def sample_tip_lean(sample_game: Game) -> Tip:
    """A Lean-tier tip (0.55 <= confidence < 0.70)."""
    return Tip(
        game=sample_game,
        pick="Sydney Roosters",
        confidence=0.6173,
        rationale="",
        teaching_moment="",
    )


@pytest.fixture()
def sample_tip_coin_flip(sample_game_close: Game) -> Tip:
    """A Coin Flip-tier tip (confidence < 0.55)."""
    return Tip(
        game=sample_game_close,
        pick="Melbourne Storm",
        confidence=0.51,
        rationale="",
        teaching_moment="",
    )


# ---------------------------------------------------------------------------
# RoundTips fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_round_tips(sample_tip_lean: Tip, sample_tip_coin_flip: Tip) -> RoundTips:
    """A RoundTips object with two tips for round 1."""
    return RoundTips(
        round_number=1,
        season=2025,
        tips=[sample_tip_lean, sample_tip_coin_flip],
        generated_at=datetime(2025, 3, 5, 12, 0, 0),
        teaching_moment="",
    )
