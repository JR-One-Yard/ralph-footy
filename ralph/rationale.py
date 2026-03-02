"""Rationale generation — template-driven explanations in Ralph's voice.

Each tip gets a short, cheeky rationale explaining WHY Ralph picked that team.
Templates are parameterised with actual game data (team names, probabilities,
odds) and rotated by game position within the round for variety.
"""

from __future__ import annotations

from ralph.models import MarketView, Tip

# ---------------------------------------------------------------------------
# Templates by confidence tier — 4 each, Ralph's voice
# ---------------------------------------------------------------------------

LOCK_TEMPLATES: list[str] = [
    (
        "Ralph is backing the {pick} hard here. The market has them at"
        " {pick_prob_pct} {home_or_away} at {venue}, and that feels about"
        " right. The {other} would need something special to pull this one off."
    ),
    (
        "This is as close to a sure thing as footy gets (which is to say,"
        " it's still footy). The {pick} are {pick_prob_pct} favourites and"
        " Ralph reckons the bookies have read this one well. Back the {pick}."
    ),
    (
        "At {pick_best_odds}, the {pick} are short odds for a reason."
        " The market says {pick_prob_pct} and Ralph is not about to argue"
        " with that {home_or_away}. Lock it in."
    ),
    (
        "Ralph doesn't like to use the word 'certainty' in footy, but the"
        " {pick} at {pick_prob_pct} {home_or_away} is about as confident as"
        " he gets. The {other} at {other_best_odds} are a genuine roughie here."
    ),
]

LEAN_TEMPLATES: list[str] = [
    (
        "Ralph leans {pick} here \u2014 the market has them at {pick_prob_pct}"
        " which feels about right {home_or_away} at {venue}. The {other} are"
        " capable of making this ugly, but you'd want better odds to back them."
    ),
    (
        "The {pick} are favoured at {pick_prob_pct} and Ralph reckons that's"
        " fair. Not a certainty by any stretch \u2014 the {other} at"
        " {other_best_odds} aren't bad value if you fancy an upset \u2014 but"
        " Ralph's going with the market on this one."
    ),
    (
        "Market says {pick} at {pick_prob_pct}, Ralph says yeah, fair enough."
        " The {pick} should get the job done {home_or_away} but the {other}"
        " won't make it easy. A solid lean, not a lock."
    ),
    (
        "This one leans {pick} \u2014 they're {pick_prob_pct} favourites and"
        " Ralph agrees with the market read. The {other} have a path to"
        " victory here at {other_best_odds}, but it's the harder road."
    ),
]

COIN_FLIP_TEMPLATES: list[str] = [
    (
        "Honestly? This one could go either way. The market has {pick} at a"
        " slight edge ({pick_prob_pct}) but Ralph wouldn't bet his house on"
        " it. Going {pick} because someone has to pick, but don't be shocked"
        " if the {other} salute."
    ),
    (
        "Ralph is going {pick} here, but it's basically a coin flip at"
        " {pick_prob_pct}. The bookies can't split them either \u2014"
        " {pick_best_odds} vs {other_best_odds}. This is the kind of game"
        " that makes tipping comps fun (and frustrating)."
    ),
    (
        "The thinnest of margins separates these two. {pick} at"
        " {pick_prob_pct} gets the Ralph nod but he'd understand if you went"
        " the other way. {venue} could be the decider."
    ),
    (
        "If someone at the pub told you they KNEW who'd win this one, walk"
        " away \u2014 they're dreaming. Ralph has {pick} at {pick_prob_pct}"
        " but honestly, the {other} at {other_best_odds} are just as likely."
        " Pencil in {pick} and hope for the best."
    ),
]


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
    """Find the best (lowest) odds for *team* across all bookmaker sources.

    For the favourite, "best" means the lowest price (shortest odds).
    For the underdog, "best" means the highest price (longest odds).

    In this implementation we always return the minimum odds for the picked
    team (shortest price = best for a favourite backer) and maximum for the
    other team (longest price = best value for an upset backer).
    """
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
        # "other" is the away team — best value = highest away odds
        return max(o.away_odds for o in market_view.odds_sources)
    # "other" is the home team — best value = highest home odds
    return max(o.home_odds for o in market_view.odds_sources)


def generate_rationale(tip: Tip, market_view: MarketView, game_index: int) -> str:
    """Build a rationale string for a single tip.

    Selects a template from the appropriate tier using deterministic
    rotation (``game_index % len(templates)``) and populates it with
    actual game data.

    Parameters
    ----------
    tip:
        The generated tip (with pick and confidence already set).
    market_view:
        Market data for the game (odds sources, probabilities).
    game_index:
        0-based position of this game in the round fixture list.
        Used for deterministic template rotation.

    Returns
    -------
    A 2-3 sentence rationale string in Ralph's voice, with all
    placeholders resolved.
    """
    templates = _templates_for_tier(tip.confidence_label)
    template = templates[game_index % len(templates)]

    pick_short = team_short_name(tip.pick)

    # Determine the "other" team
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

    return template.format(
        pick=pick_short,
        other=other_short,
        pick_prob_pct=f"{round(pick_prob * 100)}%",
        other_prob_pct=f"{round(other_prob * 100)}%",
        pick_best_odds=f"${pick_best_odds:.2f}",
        other_best_odds=f"${other_best_odds:.2f}",
        venue=game.venue,
        confidence_label=tip.confidence_label,
        home_or_away=home_or_away,
    )
