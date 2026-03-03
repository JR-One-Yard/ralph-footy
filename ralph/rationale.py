"""Rationale generation — Claude API-powered explanations for NRL_FOOTIEFORECASTER.

Each tip gets a short, precise rationale explaining WHY that team was picked.
When online, rationales are generated via the Claude API using quant metrics.
When offline (or on API failure), enriched templates are used as fallback.
"""

from __future__ import annotations

import logging
import os

from ralph.models import GameAnalysis, MarketView, RoundAnalysis, Tip

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fallback templates by confidence tier — enriched with quant metrics
# ---------------------------------------------------------------------------

LOCK_TEMPLATES: list[str] = [
    (
        "The {pick} at {pick_prob_pct} {home_or_away} is as close to a certainty"
        " as the NRL gets. {market_confidence} across bookmakers, EV of {ev_fav}."
        " {quant_signal}. Back them."
    ),
    (
        "Market consensus has the {pick} at {pick_prob_pct} favourites with an"
        " EV of {ev_fav} — the numbers stack up cleanly. The {other} would need"
        " something extraordinary to turn this over. Lock it in."
    ),
    (
        "At {pick_best_odds}, the {pick} are short but Kelly says {kelly_fav} of"
        " bankroll — that's a real edge, not just a hunch. {market_confidence}"
        " across the bookmakers. This is a confident back."
    ),
    (
        "The spread is {spread_pct} — {market_confidence} — and the {pick} at"
        " {pick_prob_pct} {home_or_away} have the strongest market signal this"
        " round. The {other} at {other_best_odds} are a genuine roughie."
    ),
]

LEAN_TEMPLATES: list[str] = [
    (
        "The {pick} are {pick_prob_pct} {home_or_away} at {venue}."
        " {quant_signal}. The {other} are capable of making this uncomfortable,"
        " but you'd want better odds to back them."
    ),
    (
        "Market has the {pick} at {pick_prob_pct} and the data supports it."
        " EV is {ev_fav} on the {pick}, {ev_dog} on the {other}."
        " Not a certainty — but the expected value says follow the market."
    ),
    (
        "The {pick} at {pick_prob_pct} — bookmaker spread is {spread_pct}"
        " ({market_confidence}). The implied probability gives them the"
        " edge {home_or_away}."
    ),
    (
        "This one leans {pick} — they're {pick_prob_pct} favourites."
        " Kelly fraction: {kelly_fav}. The {other} have a path at"
        " {other_best_odds}, but it's the harder road."
    ),
]

COIN_FLIP_TEMPLATES: list[str] = [
    (
        "A {spread_pct} spread means the market genuinely cannot separate"
        " these two. {pick} at {pick_prob_pct} gets the nod, but at this"
        " margin you're betting on noise. {venue} and home advantage are"
        " the tiebreaker."
    ),
    (
        "The {pick} at {pick_prob_pct} — but this is basically a coin flip."
        " {quant_signal}. {pick_best_odds} vs {other_best_odds}. This is"
        " the kind of game that makes tipping comps interesting."
    ),
    (
        "The thinnest of margins separates these two. {pick} at"
        " {pick_prob_pct} — EV is {ev_fav} vs {ev_dog}."
        " {venue} could be the decider."
    ),
    (
        "Anyone claiming certainty on this game is selling you something."
        " The {pick} at {pick_prob_pct} edge is within the noise."
        " The {other} at {other_best_odds} are just as likely."
        " {market_confidence}. Pencil in {pick} and move on."
    ),
]


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def team_short_name(full_name: str) -> str:
    """Extract the mascot (last word) from a full NRL team name.

    Examples
    --------
    >>> team_short_name("South Sydney Rabbitohs")
    'Rabbitohs'
    >>> team_short_name("St George Illawarra Dragons")
    'Dragons'
    >>> team_short_name("Penrith Panthers")
    'Panthers'
    """
    return full_name.split()[-1]


def _templates_for_tier(confidence_label: str) -> list[str]:
    """Return the template list for a given confidence tier."""
    if confidence_label == "Lock":
        return LOCK_TEMPLATES
    elif confidence_label == "Lean":
        return LEAN_TEMPLATES
    else:
        return COIN_FLIP_TEMPLATES


def _best_odds_for_team(market_view: MarketView, team: str) -> float:
    """Find the best (lowest) odds for *team* across all bookmaker sources."""
    if not market_view.odds_sources:
        return 0.0
    is_home = team == market_view.game.home_team
    if is_home:
        return min(o.home_odds for o in market_view.odds_sources)
    return min(o.away_odds for o in market_view.odds_sources)


def _best_odds_for_other(market_view: MarketView, team: str) -> float:
    """Find the best (highest) odds for the *other* team — the underdog price."""
    if not market_view.odds_sources:
        return 0.0
    is_home = team == market_view.game.home_team
    if is_home:
        return max(o.away_odds for o in market_view.odds_sources)
    return max(o.home_odds for o in market_view.odds_sources)


def _build_template_context(
    tip: Tip,
    market_view: MarketView,
    game_analysis: GameAnalysis | None,
) -> dict[str, str]:
    """Build the template substitution context for a game."""
    pick_short = team_short_name(tip.pick)
    game = tip.game

    if tip.pick == game.home_team:
        other_full = game.away_team
        pick_prob = market_view.consensus_home_prob
        other_prob = market_view.consensus_away_prob
        home_or_away = "at home"
    else:
        other_full = game.home_team
        pick_prob = market_view.consensus_away_prob
        other_prob = market_view.consensus_home_prob
        home_or_away = "on the road"

    other_short = team_short_name(other_full)
    pick_best_odds = _best_odds_for_team(market_view, tip.pick)
    other_best_odds = _best_odds_for_other(market_view, tip.pick)

    # Quant-enriched fields (fallback to basic values if no analysis)
    if game_analysis:
        ev_fav = f"{game_analysis.ev_favourite:+.1%}"
        ev_dog = f"{game_analysis.ev_underdog:+.1%}"
        kelly_fav = f"{game_analysis.kelly_favourite:.1%}"
        spread_pct = f"{game_analysis.market_spread:.1%}"
        market_confidence = game_analysis.market_confidence_label.lower()
        quant_signal = game_analysis.quant_signal
    else:
        ev_fav = "N/A"
        ev_dog = "N/A"
        kelly_fav = "N/A"
        spread_pct = "N/A"
        market_confidence = "market aligned"
        quant_signal = "Market aligned — follow the consensus"

    return {
        "pick": pick_short,
        "other": other_short,
        "pick_prob_pct": f"{round(pick_prob * 100)}%",
        "other_prob_pct": f"{round(other_prob * 100)}%",
        "pick_best_odds": f"${pick_best_odds:.2f}",
        "other_best_odds": f"${other_best_odds:.2f}",
        "venue": game.venue,
        "confidence_label": tip.confidence_label,
        "home_or_away": home_or_away,
        "ev_fav": ev_fav,
        "ev_dog": ev_dog,
        "kelly_fav": kelly_fav,
        "spread_pct": spread_pct,
        "market_confidence": market_confidence,
        "quant_signal": quant_signal,
    }


# ---------------------------------------------------------------------------
# Template-based rationale (offline fallback)
# ---------------------------------------------------------------------------


def generate_rationale_template(
    tip: Tip,
    market_view: MarketView,
    game_index: int,
    game_analysis: GameAnalysis | None = None,
) -> str:
    """Build a rationale string using enriched templates.

    This is the deterministic fallback used when the Claude API is
    unavailable or ``--offline`` mode is active.
    """
    templates = _templates_for_tier(tip.confidence_label)
    template = templates[game_index % len(templates)]
    ctx = _build_template_context(tip, market_view, game_analysis)
    return template.format(**ctx)


# ---------------------------------------------------------------------------
# Claude API-powered rationale
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are NRL_FOOTIEFORECASTER, a quantitative NRL tipping system that explains \
its picks with precision and clarity. You combine market consensus data with \
statistical reasoning and communicate complex ideas in plain, confident language. \
You respect your audience's intelligence — you never talk down to them, but you \
also don't assume they have a stats degree.

Rules:
- 2-3 sentences ONLY, under 600 characters total.
- Weave in at least ONE quantitative concept (EV, Kelly criterion, market spread, \
overround, implied probability, convergence, calibration).
- Mention the picked team by mascot name (e.g. "Roosters" not "Sydney Roosters").
- Be direct and opinionated. No hedging, no false humility.
- Use precise language. If "expected value" is the right term, use it. \
If a simpler word conveys the same meaning without losing precision, prefer it.
- No bullet points, no headers, no markdown.
- Use Australian English.
"""


def _build_api_prompt(
    tip: Tip,
    market_view: MarketView,
    game_analysis: GameAnalysis,
) -> str:
    """Build the user prompt for the Claude API call."""
    pick_short = team_short_name(tip.pick)
    game = tip.game
    other = (
        game.away_team if tip.pick == game.home_team else game.home_team
    )
    other_short = team_short_name(other)
    home_or_away = "at home" if tip.pick == game.home_team else "on the road"

    odds_lines = []
    for o in market_view.odds_sources:
        odds_lines.append(
            f"  {o.source}: {game.home_team} ${o.home_odds:.2f} | "
            f"{game.away_team} ${o.away_odds:.2f} (overround: {o.overround:.1f}%)"
        )
    odds_block = "\n".join(odds_lines)

    return f"""\
Write the rationale for this NRL pick.

Game: {game.home_team} vs {game.away_team}
Venue: {game.venue}
Pick: {pick_short} ({home_or_away})
Confidence: {tip.confidence_label} ({tip.confidence:.0%})

Market data:
{odds_block}

Consensus: {game.home_team} {market_view.consensus_home_prob:.1%} | \
{game.away_team} {market_view.consensus_away_prob:.1%}

Quant metrics:
- Market spread: {game_analysis.market_spread:.1%} ({game_analysis.market_confidence_label})
- EV favourite: {game_analysis.ev_favourite:+.1%}
- EV underdog: {game_analysis.ev_underdog:+.1%}
- Kelly (favourite): {game_analysis.kelly_favourite:.1%}
- Kelly (underdog): {game_analysis.kelly_underdog:.1%}
- Max bookie discrepancy: {game_analysis.max_value_discrepancy:.1%} ({game_analysis.discrepancy_source})
- Quant signal: {game_analysis.quant_signal}

Your job is to SUPPORT this pick — explain why it's the right call. Do not argue for the other team.

Write 2-3 sentences. Mention {pick_short} and {other_short} by mascot name."""


def generate_rationale_api(
    tip: Tip,
    market_view: MarketView,
    game_analysis: GameAnalysis,
) -> str | None:
    """Generate a rationale via the Claude API.

    Returns the rationale string, or None if the API call fails.
    """
    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic package not installed — falling back to templates")
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set — falling back to templates")
        return None

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=400,
            system=_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": _build_api_prompt(tip, market_view, game_analysis),
                }
            ],
        )
        text = response.content[0].text.strip()
        # Truncate if somehow over 800 chars
        if len(text) > 800:
            text = text[:797] + "..."
        return text
    except Exception:
        logger.exception("Claude API call failed — falling back to templates")
        return None


# ---------------------------------------------------------------------------
# Public API — used by tips.py
# ---------------------------------------------------------------------------


def generate_rationale(
    tip: Tip,
    market_view: MarketView,
    game_index: int,
    game_analysis: GameAnalysis | None = None,
    offline: bool = False,
) -> str:
    """Build a rationale string for a single tip.

    When ``offline`` is False and a ``game_analysis`` is provided,
    attempts to generate via the Claude API. Falls back to enriched
    templates on failure or when offline.

    Parameters
    ----------
    tip:
        The generated tip (with pick and confidence already set).
    market_view:
        Market data for the game (odds sources, probabilities).
    game_index:
        0-based position of this game in the round fixture list.
        Used for deterministic template rotation in fallback mode.
    game_analysis:
        Optional quant analysis for the game.
    offline:
        If True, skip API calls entirely and use templates.

    Returns
    -------
    A 2-3 sentence rationale string.
    """
    # Try API-powered rationale first
    if not offline and game_analysis is not None:
        api_rationale = generate_rationale_api(tip, market_view, game_analysis)
        if api_rationale:
            return api_rationale

    # Fallback to enriched templates
    return generate_rationale_template(tip, market_view, game_index, game_analysis)
