"""Tests for ralph.teaching — teaching content (Spec 05).

Covers all 9 acceptance criteria from specs/05_learn_something.md.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import pytest

from ralph.models import Game, MarketView, Odds
from ralph.teaching import (
    build_teaching_context,
    generate_teaching_snippet,
    load_teaching_topics,
    select_topic,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TOPICS_PATH = Path(__file__).resolve().parent.parent / "data" / "teaching_topics.json"


def _make_market_view(
    home: str,
    away: str,
    home_prob: float,
    away_prob: float,
    home_odds: float = 1.80,
    away_odds: float = 2.00,
) -> MarketView:
    """Convenience helper to build a MarketView with minimal boilerplate."""
    game = Game(
        home_team=home,
        away_team=away,
        venue="Test Stadium",
        kickoff=datetime(2025, 3, 6, 20, 0),
        round_number=1,
    )
    odds = [Odds(home_odds=home_odds, away_odds=away_odds, source="TestBookie")]
    return MarketView(
        game=game,
        odds_sources=odds,
        consensus_home_prob=home_prob,
        consensus_away_prob=away_prob,
    )


@pytest.fixture()
def sample_market_views_teaching() -> list[MarketView]:
    """A realistic set of market views for teaching tests."""
    return [
        _make_market_view(
            "Sydney Roosters",
            "Brisbane Broncos",
            0.72,
            0.28,
            home_odds=1.40,
            away_odds=3.00,
        ),
        _make_market_view(
            "Melbourne Storm",
            "Penrith Panthers",
            0.51,
            0.49,
            home_odds=1.90,
            away_odds=1.90,
        ),
        _make_market_view(
            "Parramatta Eels",
            "Canterbury Bulldogs",
            0.60,
            0.40,
            home_odds=1.65,
            away_odds=2.30,
        ),
    ]


# ---------------------------------------------------------------------------
# AC-01: Round 1 returns the "Implied Probability" topic (id 1, index 0)
# ---------------------------------------------------------------------------


def test_ac01_round_1_returns_implied_probability():
    """Given round 1, select_topic returns index 0 (Implied Probability)."""
    topics = load_teaching_topics()
    idx = select_topic(1, len(topics))
    assert idx == 0
    assert topics[idx]["title"] == "Implied Probability"


# ---------------------------------------------------------------------------
# AC-02: Round 11 with 10 topics cycles back to index 0
# ---------------------------------------------------------------------------


def test_ac02_round_11_cycles_to_index_0():
    """Given round 11 with 10 topics, the cycle restarts: (11-1) % 10 = 0."""
    assert select_topic(11, 10) == 0


def test_ac02_select_topic_basic_cycle():
    """select_topic(1, 10) returns 0; select_topic(10, 10) returns 9."""
    assert select_topic(1, 10) == 0
    assert select_topic(10, 10) == 9
    assert select_topic(11, 10) == 0
    assert select_topic(20, 10) == 9


# ---------------------------------------------------------------------------
# AC-03: Template variables are replaced with actual round data
# ---------------------------------------------------------------------------


def test_ac03_template_variables_resolved(
    sample_market_views_teaching: list[MarketView],
):
    """Template variables like {biggest_fav} are replaced with data."""
    snippet = generate_teaching_snippet(1, sample_market_views_teaching)
    # Round 1 uses the Implied Probability topic which references {biggest_fav}
    # The biggest favourite is Sydney Roosters (0.72) -> short name "Roosters"
    assert "Roosters" in snippet
    # Should contain a dollar sign from odds formatting
    assert "$" in snippet


def test_ac03_build_teaching_context_values(
    sample_market_views_teaching: list[MarketView],
):
    """build_teaching_context extracts correct stats from market views."""
    ctx = build_teaching_context(sample_market_views_teaching)
    # Biggest favourite: Roosters at 72%
    assert ctx["biggest_fav"] == "Roosters"
    assert ctx["biggest_fav_prob"] == "72%"
    # Tightest game: Storm vs Panthers (51%)
    assert ctx["closest_game_home"] == "Storm"
    assert ctx["closest_game_away"] == "Panthers"
    assert ctx["closest_game_prob"] == "51%"
    # Counts
    assert ctx["num_games"] == "3"
    # 1 lock (Roosters at 72%), 1 coin-flip (Storm/Panthers at 51%)
    assert ctx["num_locks"] == "1"
    assert ctx["num_coin_flips"] == "1"


# ---------------------------------------------------------------------------
# AC-04: Fallback text used when variables cannot be resolved
# ---------------------------------------------------------------------------


def test_ac04_fallback_when_no_market_data():
    """If market_views is empty, the fallback text (no variables) is used."""
    snippet = generate_teaching_snippet(1, [])
    # Fallback for topic 1 should not contain any {variable} placeholders
    assert "{" not in snippet
    # Fallback should still be meaningful text
    assert len(snippet) > 50


def test_ac04_fallback_with_empty_odds_sources():
    """Market views with no odds sources trigger context gaps -> fallback."""
    game = Game(
        home_team="Team A",
        away_team="Team B",
        venue="Test Stadium",
        kickoff=datetime(2025, 3, 6, 20, 0),
        round_number=1,
    )
    # MarketView with no odds sources — build_teaching_context will return
    # "N/A" for odds-dependent fields, which doesn't match template expectations
    # but also doesn't leave unresolved {placeholders}.
    mv = MarketView(
        game=game,
        odds_sources=[],
        consensus_home_prob=0.60,
        consensus_away_prob=0.40,
    )
    snippet = generate_teaching_snippet(1, [mv])
    # Must not have unresolved placeholders
    assert not re.search(r"\{[a-z_]+\}", snippet)


# ---------------------------------------------------------------------------
# AC-05: teaching_topics.json exists and has at least 10 topics
# ---------------------------------------------------------------------------


def test_ac05_topics_file_exists():
    """data/teaching_topics.json exists on disk."""
    assert _TOPICS_PATH.exists(), f"Expected file at {_TOPICS_PATH}"


def test_ac05_at_least_10_topics():
    """The teaching topics file contains at least 10 topics."""
    topics = load_teaching_topics()
    assert len(topics) >= 10


# ---------------------------------------------------------------------------
# AC-06: Snippet length is between 100 and 600 characters
# ---------------------------------------------------------------------------


def test_ac06_snippet_length_within_bounds(
    sample_market_views_teaching: list[MarketView],
):
    """Each teaching snippet (resolved) is between 100 and 600 characters."""
    topics = load_teaching_topics()
    for round_num in range(1, len(topics) + 1):
        snippet = generate_teaching_snippet(round_num, sample_market_views_teaching)
        assert 100 <= len(snippet) <= 600, (
            f"Round {round_num} snippet length {len(snippet)} out of bounds: {snippet!r}"
        )


def test_ac06_fallback_length_within_bounds():
    """Fallback text (no market data) is also between 100 and 600 chars."""
    topics = load_teaching_topics()
    for round_num in range(1, len(topics) + 1):
        snippet = generate_teaching_snippet(round_num, [])
        assert 100 <= len(snippet) <= 600, (
            f"Round {round_num} fallback length {len(snippet)} out of bounds: {snippet!r}"
        )


# ---------------------------------------------------------------------------
# AC-07: Teaching snippet is accessible on RoundTips
# ---------------------------------------------------------------------------


def test_ac07_round_tips_has_teaching_moment(sample_round_tips):
    """RoundTips has a teaching_moment field that accepts a string."""
    # The conftest fixture creates a RoundTips with teaching_moment=""
    assert hasattr(sample_round_tips, "teaching_moment")
    sample_round_tips.teaching_moment = "Test snippet"
    assert sample_round_tips.teaching_moment == "Test snippet"


# ---------------------------------------------------------------------------
# AC-08: No unresolved {variable} placeholders in output
# ---------------------------------------------------------------------------


def test_ac08_no_unresolved_placeholders_with_data(
    sample_market_views_teaching: list[MarketView],
):
    """Resolved snippets have no leftover {variable} patterns."""
    topics = load_teaching_topics()
    for round_num in range(1, len(topics) + 1):
        snippet = generate_teaching_snippet(round_num, sample_market_views_teaching)
        unresolved = re.findall(r"\{[a-z_]+\}", snippet)
        assert unresolved == [], f"Round {round_num} has unresolved placeholders: {unresolved}"


def test_ac08_no_unresolved_placeholders_fallback():
    """Fallback snippets (empty market data) have no {variable} patterns."""
    topics = load_teaching_topics()
    for round_num in range(1, len(topics) + 1):
        snippet = generate_teaching_snippet(round_num, [])
        unresolved = re.findall(r"\{[a-z_]+\}", snippet)
        assert unresolved == [], (
            f"Round {round_num} fallback has unresolved placeholders: {unresolved}"
        )


# ---------------------------------------------------------------------------
# AC-09: Every topic has id, title, category, template, and fallback fields
# ---------------------------------------------------------------------------


def test_ac09_all_topics_have_required_fields():
    """Every topic in teaching_topics.json has all required fields."""
    topics = load_teaching_topics()
    required = {"id", "title", "category", "template", "fallback"}
    for i, topic in enumerate(topics):
        missing = required - set(topic.keys())
        assert missing == set(), (
            f"Topic at index {i} ('{topic.get('title', '???')}') is missing: {sorted(missing)}"
        )


def test_ac09_topic_ids_are_unique():
    """All topic IDs are unique."""
    topics = load_teaching_topics()
    ids = [t["id"] for t in topics]
    assert len(ids) == len(set(ids)), f"Duplicate IDs found: {ids}"


# ---------------------------------------------------------------------------
# Additional edge-case / robustness tests
# ---------------------------------------------------------------------------


def test_load_teaching_topics_invalid_path():
    """Loading from a non-existent path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_teaching_topics(Path("/tmp/nonexistent_topics.json"))


def test_load_teaching_topics_missing_fields(tmp_path):
    """A topic missing required fields raises ValueError."""
    bad_file = tmp_path / "bad_topics.json"
    bad_file.write_text(json.dumps({"topics": [{"id": 1, "title": "Oops"}]}))
    with pytest.raises(ValueError, match="missing required fields"):
        load_teaching_topics(bad_file)


def test_generate_snippet_deterministic(
    sample_market_views_teaching: list[MarketView],
):
    """Same inputs always produce the same output (deterministic)."""
    a = generate_teaching_snippet(1, sample_market_views_teaching)
    b = generate_teaching_snippet(1, sample_market_views_teaching)
    assert a == b


def test_all_topics_cycle_correctly():
    """Rounds 1..20 cycle through 10 topics correctly."""
    topics = load_teaching_topics()
    n = len(topics)
    for r in range(1, 2 * n + 1):
        expected_idx = (r - 1) % n
        assert select_topic(r, n) == expected_idx
