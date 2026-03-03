"""Formatted output — rich console and Markdown tip sheet generation.

Produces the styled per-game output with the tip, market snapshot,
quant signal, rationale, and a rotating "Did You Know?" teaching moment
about probability, markets, ML, or LLMs.
"""

from __future__ import annotations

import platform
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from ralph import __version__
from ralph.models import GameAnalysis, MarketView, RoundAnalysis, RoundTips, Tip

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
        return "Season Record: No results yet — check back after the round!"

    total = season_record["total"]
    correct = season_record["correct"]
    overall = season_record["overall"]
    by_tier = season_record.get("by_tier", {})

    record_line = f"Season Record: {correct}/{total} ({overall:.0%})"

    lock_pct = by_tier.get("Lock", 0.0)
    lean_pct = by_tier.get("Lean", 0.0)
    cf_pct = by_tier.get("Coin Flip", 0.0)
    tier_line = f"Lock: {lock_pct:.0%} | Lean: {lean_pct:.0%} | Coin Flip: {cf_pct:.0%}"

    return f"{record_line}\n{tier_line}"


def _lookup_game_analysis(
    game_analyses: list[GameAnalysis] | None, market_view: MarketView
) -> GameAnalysis | None:
    """Find the GameAnalysis matching a MarketView (by game identity)."""
    if not game_analyses:
        return None
    for ga in game_analyses:
        if ga.market_view is market_view:
            return ga
    return None


# ---------------------------------------------------------------------------
# Console formatting (rich)
# ---------------------------------------------------------------------------


def format_tip_console(
    tip: Tip,
    market_view: MarketView,
    game_number: int,
    game_analysis: GameAnalysis | None = None,
) -> str:
    """Format a single game tip as a rich-markup string."""
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
        f"[bold {colour}]THE TIP: {tip.pick} ({conf_pct} confidence — {label})[/bold {colour}]",
        "",
    ]

    # Market Snapshot (enriched when quant data available)
    if home_odds > 0 and away_odds > 0:
        lines.append(
            f"[dim]MARKET SNAPSHOT:[/dim]"
        )
        lines.append(
            f"[dim]  Consensus: {game.home_team} {home_prob_pct} | "
            f"{game.away_team} {away_prob_pct}[/dim]"
        )
        lines.append(
            f"[dim]  Best odds: {game.home_team} ${home_odds:.2f} | "
            f"{game.away_team} ${away_odds:.2f}[/dim]"
        )
        if game_analysis:
            lines.append(
                f"[dim]  EV: {game_analysis.ev_favourite:+.1%} (fav) | "
                f"{game_analysis.ev_underdog:+.1%} (dog) | "
                f"Kelly: {game_analysis.kelly_favourite:.1%}[/dim]"
            )
            lines.append(
                f"[dim]  Spread: {game_analysis.market_spread:.1%} "
                f"({game_analysis.market_confidence_label})[/dim]"
            )
        else:
            lines.append(
                f"[dim]  (after overround removal)[/dim]"
            )
    else:
        lines.append("[dim]MARKET SNAPSHOT: No odds available[/dim]")

    # Quant Signal
    if game_analysis:
        lines.append("")
        lines.append(f"[bold magenta]QUANT SIGNAL:[/bold magenta] {game_analysis.quant_signal}")

    if tip.rationale:
        lines.append("")
        lines.append(f"RATIONALE:\n{tip.rationale}")

    return "\n".join(lines)


def _format_desk_console(round_analysis: RoundAnalysis) -> str:
    """Format THE DESK round overview as a rich-markup string."""
    ra = round_analysis
    lines = [
        "[bold cyan]=== THE DESK — Round Overview ===[/bold cyan]",
        "",
        f"  Difficulty: [bold]{ra.difficulty_label}[/bold]"
        f" (score: {ra.round_difficulty_score:.2f})",
        f"  Round volatility: {ra.round_volatility:.1%}",
        f"  Chalk rate: {ra.chalk_rate:.0%} of games have a clear favourite",
        f"  Upset watch: {ra.upset_watch_count} game(s) with genuine uncertainty",
    ]

    warning = ra.portfolio_warning
    if warning:
        lines.append(f"  [yellow]Portfolio warning:[/yellow] {warning}")

    return "\n".join(lines)


def format_round_console(
    round_tips: RoundTips,
    market_views: list[MarketView],
    season_record: dict | None = None,
    round_analysis: RoundAnalysis | None = None,
) -> str:
    """Format the full round as a rich-markup string."""
    parts: list[str] = []

    # Header
    generated = round_tips.generated_at.strftime("%Y-%m-%d %H:%M")
    header = (
        f"[bold green]NRL_FOOTIEFORECASTER[/bold green]\n"
        f"NRL {round_tips.season} — Round {round_tips.round_number} Tips\n"
        f"Generated: {generated}"
    )
    parts.append(header)
    parts.append("")

    # THE DESK — Round Overview
    if round_analysis:
        parts.append(_format_desk_console(round_analysis))
        parts.append("")

    game_analyses = round_analysis.game_analyses if round_analysis else None

    # Per-game tips
    for i, (tip, mv) in enumerate(zip(round_tips.tips, market_views)):
        ga = _lookup_game_analysis(game_analyses, mv)
        parts.append(format_tip_console(tip, mv, game_number=i + 1, game_analysis=ga))
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
        '[dim]"The market is the model. Everything else is noise."[/dim]'
    )
    parts.append(f"[dim]— NRL_FOOTIEFORECASTER v{__version__}[/dim]")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Markdown formatting
# ---------------------------------------------------------------------------


def _format_desk_markdown(round_analysis: RoundAnalysis) -> list[str]:
    """Format THE DESK round overview as Markdown lines."""
    ra = round_analysis
    lines = [
        "## THE DESK — Round Overview",
        "",
        f"**Difficulty:** {ra.difficulty_label}"
        f" (score: {ra.round_difficulty_score:.2f})",
        f"- Round volatility: {ra.round_volatility:.1%}",
        f"- Chalk rate: {ra.chalk_rate:.0%} of games have a clear favourite",
        f"- Upset watch: {ra.upset_watch_count} game(s) with genuine uncertainty",
    ]

    warning = ra.portfolio_warning
    if warning:
        lines.append(f"- **Portfolio warning:** {warning}")

    lines.append("")
    lines.append("---")
    lines.append("")
    return lines


def format_round_markdown(
    round_tips: RoundTips,
    market_views: list[MarketView],
    season_record: dict | None = None,
    round_analysis: RoundAnalysis | None = None,
) -> str:
    """Generate the full tip sheet as a Markdown string."""
    lines: list[str] = []

    generated = round_tips.generated_at.strftime("%Y-%m-%d %H:%M")

    # Header
    lines.append(
        f"# NRL_FOOTIEFORECASTER — NRL {round_tips.season}"
        f" Round {round_tips.round_number} Tips"
    )
    lines.append("")
    lines.append(f"*Generated {generated}*")
    lines.append("")
    lines.append("---")
    lines.append("")

    # THE DESK — Round Overview
    if round_analysis:
        lines.extend(_format_desk_markdown(round_analysis))

    game_analyses = round_analysis.game_analyses if round_analysis else None

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

        ga = _lookup_game_analysis(game_analyses, mv)

        lines.append(f"## GAME {game_num}: {game.home_team} vs {game.away_team}")
        lines.append(f"**{game.venue}** | {kickoff_str}")
        lines.append("")
        lines.append(f"**THE TIP:** {tip.pick} ({conf_pct} confidence — {label})")
        lines.append("")

        if home_odds > 0 and away_odds > 0:
            lines.append("**MARKET SNAPSHOT:**")
            lines.append(
                f"- Consensus: {game.home_team} {home_prob_pct} | "
                f"{game.away_team} {away_prob_pct}"
            )
            lines.append(
                f"- Best odds: {game.home_team} ${home_odds:.2f} | "
                f"{game.away_team} ${away_odds:.2f}"
            )
            if ga:
                lines.append(
                    f"- EV: {ga.ev_favourite:+.1%} (fav) | "
                    f"{ga.ev_underdog:+.1%} (dog) | "
                    f"Kelly: {ga.kelly_favourite:.1%}"
                )
                lines.append(
                    f"- Spread: {ga.market_spread:.1%} ({ga.market_confidence_label})"
                )
            else:
                lines.append("- (after overround removal)")
        else:
            lines.append("**MARKET SNAPSHOT:** No odds available")

        lines.append("")

        # Quant Signal
        if ga:
            lines.append(f"**QUANT SIGNAL:** {ga.quant_signal}")
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
        lines.append(f"*Season Record: {correct}/{total} ({overall:.0%})*")
        lines.append(f"*Lock: {lock_pct:.0%} | Lean: {lean_pct:.0%} | Coin Flip: {cf_pct:.0%}*")
    else:
        lines.append("*Season Record: No results yet — check back after the round!*")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append('*"The market is the model. Everything else is noise."*')
    lines.append(f"*— NRL_FOOTIEFORECASTER v{__version__}*")
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
    round_analysis: RoundAnalysis | None = None,
) -> Path:
    """Write the Markdown tip sheet to disk."""
    if data_dir is not None:
        out_dir = data_dir
    else:
        out_dir = _DEFAULT_TIPS_DIR

    out_dir.mkdir(parents=True, exist_ok=True)

    filename = f"round_{round_tips.round_number:02d}.md"
    filepath = out_dir / filename

    markdown = format_round_markdown(
        round_tips, market_views, season_record, round_analysis
    )
    filepath.write_text(markdown, encoding="utf-8")

    return filepath
