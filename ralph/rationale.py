"""Rationale generation — Claude API-powered explanations in Ralph's voice.

Each tip gets a short, cheeky rationale explaining WHY Ralph picked that team.
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
        "Ralph is backing the {pick} hard here. The market has them at"
        " {pick_prob_pct} {home_or_away} at {venue} — {market_confidence}."
        " {quant_signal}. The {other} would need something special to pull this off."
    ),
    (
        "This is as close to a sure thing as footy gets. The {pick} are"
        " {pick_prob_pct} favourites (EV: {ev_fav}) and the bookies are"
        " {market_confidence} on this one. Back the {pick}."
    ),
    (
        "At {pick_best_odds}, the {pick} are short but the numbers stack up"
        " (Kelly says {kelly_fav} of your bankroll). {market_confidence}"
        " across the bookmakers. Lock it in."
    ),
    (
        "Ralph doesn't like to use the word 'certainty' in footy, but the"
        " {pick} at {pick_prob_pct} {home_or_away} is about as confident as"
        " he gets. Spread is {spread_pct} — {market_confidence}."
        " The {other} at {other_best_odds} are a genuine roughie."
    ),
]

LEAN_TEMPLATES: list[str] = [
    (
        "Ralph leans {pick} here — the market has them at {pick_prob_pct}"
        " {home_or_away} at {venue}. {quant_signal}."
        " The {other} are capable of making this ugly, but you'd want better"
        " odds to back them."
    ),
    (
        "The {pick} are favoured at {pick_prob_pct} and Ralph reckons that's"
        " fair. EV is {ev_fav} on the {pick}, {ev_dog} on the {other}."
        " Not a certainty — but Ralph's going with the market."
    ),
    (
        "Market says {pick} at {pick_prob_pct}, Ralph says yeah, fair enough."
        " Bookmaker spread is {spread_pct} ({market_confidence})."
        " The {pick} should get the job done {home_or_away}."
    ),
    (
        "This one leans {pick} — they're {pick_prob_pct} favourites."
        " Kelly fraction: {kelly_fav}. The {other} have a path at"
        " {other_best_odds}, but it's the harder road."
    ),
]

COIN_FLIP_TEMPLATES: list[str] = [
    (
        "Honestly? This one could go either way. The market has {pick} at a"
        " slight edge ({pick_prob_pct}) but the spread is just {spread_pct}"
        " — {market_confidence}. Going {pick} because someone has to pick."
    ),
    (
        "Ralph is going {pick} here, but it's basically a coin flip at"
        " {pick_prob_pct}. {quant_signal}."
        " {pick_best_odds} vs {other_best_odds}. This is the kind of game"
        " that makes tipping comps fun (and frustrating)."
    ),
    (
        "The thinnest of margins separates these two. {pick} at"
        " {pick_prob_pct} gets the Ralph nod — EV is {ev_fav} vs {ev_dog}."
        " {venue} could be the decider."
    ),
    (
        "If someone at the pub told you they KNEW who'd win this one, walk"
        " away — they're dreaming. Ralph has {pick} at {pick_prob_pct}"
        " but the {other} at {other_best_odds} are just as likely."
        " {market_confidence}. Pencil in {pick} and hope."
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
You are Ralph, a cheeky Australian footy forecaster with a quant edge. \
You explain NRL tipping picks in 2-3 punchy sentences that weave in \
quantitative concepts naturally. You're the smartest bloke at the pub — \
never condescending, always entertaining. Use Australian English.

Rules:
- 2-3 sentences ONLY, under 400 characters total.
- Weave in at least ONE quant concept (EV, Kelly, spread, overround, implied prob).
- Mention the picked team by mascot name (e.g. "Roosters" not "Sydney Roosters").
- Never hedge excessively — be opinionated.
- No bullet points, no headers, no markdown.
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
Write Ralph's rationale for this NRL pick.

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

Write 2-3 sentences as Ralph. Mention {pick_short} and {other_short} by mascot name."""


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
    A 2-3 sentence rationale string in Ralph's voice.
    """
    # Try API-powered rationale first
    if not offline and game_analysis is not None:
        api_rationale = generate_rationale_api(tip, market_view, game_analysis)
        if api_rationale:
            return api_rationale

    # Fallback to enriched templates
    return generate_rationale_template(tip, market_view, game_index, game_analysis)
