"""Formatted output — rich console and Markdown tip sheet generation.

Produces the styled per-game output with Ralph's tip, market
breakdown, rationale, and a rotating "Did You Know?" teaching
moment about probability, markets, ML, or LLMs.
"""

from __future__ import annotations

import platform
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from ralph import __version__
from ralph.models import MarketView, RoundTips, Tip

# Default directory for Markdown tip sheets.
_DEFAULT_TIPS_DIR = Path(__file__).resolve().parent.parent / "data" / "tips"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


_AEST = ZoneInfo("Australia/Sydney")


def _format_kickoff(kickoff: datetime) -> str:
    """Format a kickoff datetime as 'Friday 7:55pm' in Australian Eastern time.

    Converts the (typically UTC) kickoff datetime to ``Australia/Sydney``
    which automatically handles AEST/AEDT daylight-saving transitions.

    Uses ``%-I`` on Unix (macOS/Linux) and ``%#I`` on Windows to strip
    the leading zero from the hour.
    """
    # Convert to Australian Eastern time.  If the datetime is naive,
    # assume it is already in local time (for backwards compatibility).
    if kickoff.tzinfo is not None:
        kickoff = kickoff.astimezone(_AEST)

    day_name = kickoff.strftime("%A")
    if platform.system() == "Windows":
        time_str = kickoff.strftime("%#I:%M%p").lower()
    else:
        time_str = kickoff.strftime("%-I:%M%p").lower()
    return f"{day_name} {time_str}"


def _best_home_odds(market_view: MarketView) -> float:
    """Return the best (lowest) home odds across all bookmaker sources."""
    if not market_view.odds_sources:
        return 0.0
    return min(o.home_odds for o in market_view.odds_sources)


def _best_away_odds(market_view: MarketView) -> float:
    """Return the best (lowest) away odds across all bookmaker sources."""
    if not market_view.odds_sources:
        return 0.0
    return min(o.away_odds for o in market_view.odds_sources)


def _confidence_colour(label: str) -> str:
    """Return the rich colour name for a confidence tier."""
    if label == "Lock":
        return "green"
    elif label == "Lean":
        return "yellow"
    else:
        return "red"


def _format_season_record_text(season_record: dict | None) -> str:
    """Build the season record string for the footer.

    Returns the 'No results yet' variant when there is no record.
    """
    if not season_record or not season_record.get("rounds_completed"):
        return "Ralph's Season Record: No results yet — check back after the round!"

    total = season_record["total"]
    correct = season_record["correct"]
    overall = season_record["overall"]
    by_tier = season_record.get("by_tier", {})

    # Per-tier stats: we need counts, not just percentages.
    # Re-derive from the overall numbers where possible.
    # The season_record dict only has totals, so we display them simply.
    record_line = f"Ralph's Season Record: {correct}/{total} ({overall:.0%})"

    # Build tier breakdown from by_tier percentages.
    # Note: we don't have per-tier counts in the record dict so we just
    # show the accuracy percentages.
    lock_pct = by_tier.get("Lock", 0.0)
    lean_pct = by_tier.get("Lean", 0.0)
    cf_pct = by_tier.get("Coin Flip", 0.0)
    tier_line = f"Lock: {lock_pct:.0%} | Lean: {lean_pct:.0%} | Coin Flip: {cf_pct:.0%}"

    return f"{record_line}\n{tier_line}"


# ---------------------------------------------------------------------------
# Console formatting (rich)
# ---------------------------------------------------------------------------


def format_tip_console(tip: Tip, market_view: MarketView, game_number: int) -> str:
    """Format a single game tip as a rich-markup string.

    Parameters
    ----------
    tip:
        The generated tip for this game.
    market_view:
        Market data for this game (odds sources, probabilities).
    game_number:
        1-based game number for display.

    Returns
    -------
    A string containing rich markup for the tip block.
    """
    game = tip.game
    label = tip.confidence_label
    colour = _confidence_colour(label)
    kickoff_str = _format_kickoff(game.kickoff)
    conf_pct = f"{round(tip.confidence * 100)}%"

    home_odds = _best_home_odds(market_view)
    away_odds = _best_away_odds(market_view)
    home_prob_pct = f"{round(market_view.consensus_home_prob * 100)}%"
    away_prob_pct = f"{round(market_view.consensus_away_prob * 100)}%"

    lines = [
        f"[bold cyan]=== GAME {game_number}: {game.home_team} vs {game.away_team} ===[/bold cyan]",
        f"{game.venue} | {kickoff_str}",
        "",
        f"[bold {colour}]RALPH'S TIP: {tip.pick} ({conf_pct} confidence — {label})[/bold {colour}]",
        "",
    ]

    if home_odds > 0 and away_odds > 0:
        lines.append(
            f"[dim]MARKET SAYS: {game.home_team} ${home_odds:.2f} | "
            f"{game.away_team} ${away_odds:.2f}[/dim]"
        )
        lines.append(
            f"[dim]  Implied: {game.home_team} {home_prob_pct} | "
            f"{game.away_team} {away_prob_pct} (after overround removal)[/dim]"
        )
    else:
        lines.append("[dim]MARKET SAYS: No odds available[/dim]")

    if tip.rationale:
        lines.append("")
        lines.append(f"RATIONALE:\n{tip.rationale}")

    return "\n".join(lines)


def format_round_console(
    round_tips: RoundTips,
    market_views: list[MarketView],
    season_record: dict | None = None,
) -> str:
    """Format the full round as a rich-markup string.

    Parameters
    ----------
    round_tips:
        The complete round tips including teaching_moment.
    market_views:
        Market data for each game (same order as tips).
    season_record:
        Optional season record dict.  Pass ``None`` or an empty-list
        record to show the 'No results yet' footer.

    Returns
    -------
    A string containing rich markup for the entire tip sheet.
    """
    parts: list[str] = []

    # Header
    generated = round_tips.generated_at.strftime("%Y-%m-%d %H:%M")
    header = (
        f"[bold green]RALPH — Footy Forecaster[/bold green]\n"
        f"NRL {round_tips.season} — Round {round_tips.round_number} Tips\n"
        f"Generated: {generated}"
    )
    parts.append(header)
    parts.append("")

    # Per-game tips
    for i, (tip, mv) in enumerate(zip(round_tips.tips, market_views)):
        parts.append(format_tip_console(tip, mv, game_number=i + 1))
        parts.append("")  # blank line separator

    # Teaching moment
    if round_tips.teaching_moment:
        parts.append("[yellow]DID YOU KNOW?[/yellow]")
        parts.append(round_tips.teaching_moment)
        parts.append("")

    # Footer
    record_text = _format_season_record_text(season_record)
    parts.append(f"[dim]{record_text}[/dim]")
    parts.append("")
    parts.append(
        '[dim]"I don\'t know everything about footy, but I know what the bookies think."[/dim]'
    )
    parts.append(f"[dim]— Ralph v{__version__}[/dim]")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Markdown formatting
# ---------------------------------------------------------------------------


def format_round_markdown(
    round_tips: RoundTips,
    market_views: list[MarketView],
    season_record: dict | None = None,
) -> str:
    """Generate the full tip sheet as a Markdown string.

    Parameters
    ----------
    round_tips:
        The complete round tips including teaching_moment.
    market_views:
        Market data for each game (same order as tips).
    season_record:
        Optional season record dict.

    Returns
    -------
    A Markdown-formatted string suitable for saving to a file or
    pasting into Slack.
    """
    lines: list[str] = []

    generated = round_tips.generated_at.strftime("%Y-%m-%d %H:%M")

    # Header
    lines.append(f"# RALPH — NRL {round_tips.season} Round {round_tips.round_number} Tips")
    lines.append("")
    lines.append(f"*Generated {generated}*")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Per-game blocks
    for i, (tip, mv) in enumerate(zip(round_tips.tips, market_views)):
        game = tip.game
        game_num = i + 1
        kickoff_str = _format_kickoff(game.kickoff)
        label = tip.confidence_label
        conf_pct = f"{round(tip.confidence * 100)}%"

        home_odds = _best_home_odds(mv)
        away_odds = _best_away_odds(mv)
        home_prob_pct = f"{round(mv.consensus_home_prob * 100)}%"
        away_prob_pct = f"{round(mv.consensus_away_prob * 100)}%"

        lines.append(f"## GAME {game_num}: {game.home_team} vs {game.away_team}")
        lines.append(f"**{game.venue}** | {kickoff_str}")
        lines.append("")
        lines.append(f"**RALPH'S TIP:** {tip.pick} ({conf_pct} confidence — {label})")
        lines.append("")

        if home_odds > 0 and away_odds > 0:
            lines.append(
                f"**MARKET SAYS:** {game.home_team} ${home_odds:.2f} | "
                f"{game.away_team} ${away_odds:.2f}"
            )
            lines.append(
                f"Implied: {game.home_team} {home_prob_pct} | "
                f"{game.away_team} {away_prob_pct} (after overround removal)"
            )
        else:
            lines.append("**MARKET SAYS:** No odds available")

        lines.append("")

        if tip.rationale:
            lines.append("**RATIONALE:**")
            lines.append(tip.rationale)
            lines.append("")

        lines.append("---")
        lines.append("")

    # Teaching moment
    if round_tips.teaching_moment:
        lines.append("## DID YOU KNOW?")
        lines.append("")
        lines.append(round_tips.teaching_moment)
        lines.append("")
        lines.append("---")
        lines.append("")

    # Footer — season record
    if season_record and season_record.get("rounds_completed"):
        total = season_record["total"]
        correct = season_record["correct"]
        overall = season_record["overall"]
        by_tier = season_record.get("by_tier", {})
        lock_pct = by_tier.get("Lock", 0.0)
        lean_pct = by_tier.get("Lean", 0.0)
        cf_pct = by_tier.get("Coin Flip", 0.0)
        lines.append(f"*Ralph's Season Record: {correct}/{total} ({overall:.0%})*")
        lines.append(f"*Lock: {lock_pct:.0%} | Lean: {lean_pct:.0%} | Coin Flip: {cf_pct:.0%}*")
    else:
        lines.append("*Ralph's Season Record: No results yet — check back after the round!*")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append('*"I don\'t know everything about footy, but I know what the bookies think."*')
    lines.append(f"*— Ralph v{__version__}*")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# File output
# ---------------------------------------------------------------------------


def save_tip_sheet(
    round_tips: RoundTips,
    market_views: list[MarketView],
    season_record: dict | None = None,
    data_dir: Path | None = None,
) -> Path:
    """Write the Markdown tip sheet to disk.

    Parameters
    ----------
    round_tips:
        The complete round tips.
    market_views:
        Market data for each game.
    season_record:
        Optional season record dict.
    data_dir:
        Override the tip sheet directory (useful for testing).
        When provided, the file is written directly into *data_dir*.
        When ``None``, the default ``data/tips/`` directory is used.

    Returns
    -------
    The :class:`Path` of the written Markdown file.
    """
    if data_dir is not None:
        out_dir = data_dir
    else:
        out_dir = _DEFAULT_TIPS_DIR

    out_dir.mkdir(parents=True, exist_ok=True)

    filename = f"round_{round_tips.round_number:02d}.md"
    filepath = out_dir / filename

    markdown = format_round_markdown(round_tips, market_views, season_record)
    filepath.write_text(markdown, encoding="utf-8")

    return filepath
