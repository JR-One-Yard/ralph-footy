"""Ralph CLI — entry point for the footy forecaster."""

from __future__ import annotations

import argparse

from rich.console import Console
from rich.panel import Panel

from ralph import __version__
from ralph.fixtures import load_fixtures
from ralph.market import build_market_views
from ralph.output import format_round_console, save_tip_sheet
from ralph.teaching import generate_teaching_snippet
from ralph.tips import generate_round_tips
from ralph.tracking import (
    calculate_accuracy,
    get_season_record,
    load_results,
    load_tips_log,
    match_results,
    save_tips_log,
)


def _print_banner(console: Console) -> None:
    """Print the Ralph startup banner using rich."""
    console.print(
        Panel.fit(
            f"[bold green]\U0001f3c9 RALPH \u2014 Footy Forecaster v{__version__}[/bold green]",
            border_style="green",
        )
    )


def _fetch_live_data(round_number: int, console: Console) -> tuple[list, dict]:
    """Fetch live fixtures and odds, normalise names, and return (games, odds_map).

    Prints progress messages to *console*.
    """
    from ralph.apis.champion_data import get_round_fixtures
    from ralph.apis.odds_api import fetch_live_odds
    from ralph.team_names import build_game_key

    # --- 1. Fixtures from Champion Data ---
    console.print("[bold cyan]Fetching live fixtures from Champion Data...[/bold cyan]")
    games = get_round_fixtures(round_number)
    console.print(f"  Found {len(games)} games for round {round_number}.")

    # --- 2. Odds from The Odds API ---
    console.print("[bold cyan]Fetching live odds from The Odds API...[/bold cyan]")
    raw_odds_map = fetch_live_odds()
    console.print(f"  Received odds for {len(raw_odds_map)} upcoming games.")

    # --- 3. Build normalised odds_map keyed by "NormHome v NormAway" ---
    # raw_odds_map keys are already normalised by parse_odds_for_round,
    # but we need to check which games have matching odds.
    odds_map = raw_odds_map  # keys already normalised via build_game_key

    # --- 4. Report any games missing odds ---
    for game in games:
        key = build_game_key(game.home_team, game.away_team)
        if key not in odds_map:
            console.print(
                f"  [yellow]Warning:[/yellow] No odds found for {key}. Using 50/50 default."
            )

    return games, odds_map


def cmd_tip(args: argparse.Namespace) -> None:
    """Handle the 'tip' subcommand — full pipeline."""
    console = Console()
    round_number = args.round
    live = getattr(args, "live", False)

    try:
        # 1. Load fixtures and odds
        if live:
            games, odds_map = _fetch_live_data(round_number, console)
        else:
            games, odds_map = load_fixtures(round_number)

        # 2. Build market views
        market_views = build_market_views(games, odds_map)

        # 3. Generate tips (includes rationale via tips.py -> rationale.py)
        season = games[0].kickoff.year if games else 2025
        round_tips = generate_round_tips(market_views, round_number, season)

        # 4. Generate teaching snippet and attach to round_tips
        teaching = generate_teaching_snippet(round_number, market_views)
        round_tips.teaching_moment = teaching

        # 5. Save tips log
        tips_log_path = save_tips_log(round_tips)
        console.print(f"[dim]Tips log saved: {tips_log_path}[/dim]")

        # 6. Load season record (may be empty if first round)
        season_record = get_season_record()

        # 7. Save Markdown tip sheet
        tip_sheet_path = save_tip_sheet(round_tips, market_views, season_record)
        console.print(f"[dim]Tip sheet saved: {tip_sheet_path}[/dim]")

        # 8. Print to console
        console.print()
        output = format_round_console(round_tips, market_views, season_record)
        console.print(output)

    except (ValueError, FileNotFoundError) as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise SystemExit(1) from exc


def cmd_results(args: argparse.Namespace) -> None:
    """Handle the 'results' subcommand — process results for a round."""
    console = Console()
    round_number = args.round

    try:
        # 1. Load tips log
        tips_log = load_tips_log(round_number)

        # 2. Load results
        results = load_results(round_number)

        # 3. Match results
        matched = match_results(tips_log, results)

        # 4. Calculate accuracy
        accuracy = calculate_accuracy(matched)

        # 5. Print summary
        console.print()
        console.print(f"[bold green]Round {round_number} Results[/bold green]")
        console.print()

        for m in matched:
            tick = "\u2705" if m["correct"] else "\u274c"
            console.print(
                f"  {tick} {m['game']} — Picked: {m['pick']}, "
                f"Winner: {m['result']} ({m['confidence_label']})"
            )

        console.print()
        total = accuracy["total"]
        correct = accuracy["correct"]
        overall = accuracy["overall"]
        console.print(
            f"[bold]Round {round_number}: {correct}/{total} correct ({overall:.0%})[/bold]"
        )

        by_tier = accuracy.get("by_tier", {})
        for tier in ("Lock", "Lean", "Coin Flip"):
            pct = by_tier.get(tier, 0.0)
            console.print(f"  {tier}: {pct:.0%}")

    except (ValueError, FileNotFoundError) as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise SystemExit(1) from exc


def cmd_record(args: argparse.Namespace) -> None:
    """Handle the 'record' subcommand — show season record."""
    console = Console()

    record = get_season_record()

    console.print()
    if not record.get("rounds_completed"):
        console.print("[yellow]No results yet — check back after the round![/yellow]")
        return

    completed = record["rounds_completed"]
    total = record["total"]
    correct = record["correct"]
    overall = record["overall"]
    by_tier = record.get("by_tier", {})

    console.print("[bold green]Ralph's Season Record[/bold green]")
    console.print(f"  Rounds completed: {', '.join(str(r) for r in completed)}")
    console.print(f"  Overall: {correct}/{total} ({overall:.0%})")
    console.print()

    for tier in ("Lock", "Lean", "Coin Flip"):
        pct = by_tier.get(tier, 0.0)
        console.print(f"  {tier}: {pct:.0%}")


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="ralph",
        description="Ralph \u2014 NRL Footy Forecaster. Tip well. Teach well.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"ralph {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")

    # tip subcommand
    tip_parser = subparsers.add_parser(
        "tip",
        help="Generate tips for an NRL round",
    )
    tip_parser.add_argument(
        "--round",
        type=int,
        required=True,
        help="Round number to generate tips for (1-27)",
    )
    tip_parser.add_argument(
        "--live",
        action="store_true",
        default=False,
        help="Fetch live fixtures from Champion Data and odds from The Odds API",
    )

    # results subcommand
    results_parser = subparsers.add_parser(
        "results",
        help="Process results for an NRL round",
    )
    results_parser.add_argument(
        "--round",
        type=int,
        required=True,
        help="Round number to process results for (1-27)",
    )

    # record subcommand
    subparsers.add_parser(
        "record",
        help="Show Ralph's season record",
    )

    return parser


def main() -> None:
    """Main entry point for the Ralph CLI."""
    parser = build_parser()
    args = parser.parse_args()

    console = Console()
    _print_banner(console)

    if args.command == "tip":
        cmd_tip(args)
    elif args.command == "results":
        cmd_results(args)
    elif args.command == "record":
        cmd_record(args)
    else:
        console.print("Ralph is thinking about this week's NRL tips...")
        console.print(
            "\nRun [bold cyan]ralph tip --round N[/bold cyan] to generate tips for a round"
        )
        console.print("Run [bold cyan]ralph tip --round N --live[/bold cyan] to use live API data")
        console.print("Run [bold cyan]ralph results --round N[/bold cyan] to process results")
        console.print("Run [bold cyan]ralph record[/bold cyan] to see the season record")


if __name__ == "__main__":
    main()
