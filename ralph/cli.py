"""Ralph CLI — entry point for the footy forecaster."""

import argparse
import sys

from ralph import __version__


def _print_banner() -> None:
    """Print the Ralph startup banner using rich."""
    try:
        from rich.console import Console
        from rich.panel import Panel

        console = Console()
        console.print(
            Panel.fit(
                f"[bold green]\U0001f3c9 RALPH \u2014 Footy Forecaster v{__version__}[/bold green]",
                border_style="green",
            )
        )
    except ImportError:
        print(f"\U0001f3c9 RALPH \u2014 Footy Forecaster v{__version__}")


def cmd_tip(args: argparse.Namespace) -> None:
    """Handle the 'tip' subcommand."""
    try:
        from rich.console import Console

        console = Console()
        console.print("[yellow]Coming soon...[/yellow]")
        console.print(
            "Ralph will generate NRL tips for the current round.\n"
            "This feature is under construction \u2014 stay tuned!"
        )
    except ImportError:
        print("Coming soon...")
        print(
            "Ralph will generate NRL tips for the current round.\n"
            "This feature is under construction \u2014 stay tuned!"
        )


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

    subparsers.add_parser(
        "tip",
        help="Generate tips for the current NRL round",
    )

    return parser


def main() -> None:
    """Main entry point for the Ralph CLI."""
    parser = build_parser()
    args = parser.parse_args()

    _print_banner()

    if args.command == "tip":
        cmd_tip(args)
    else:
        try:
            from rich.console import Console

            console = Console()
            console.print("Ralph is thinking about this week's NRL tips...")
            console.print(
                "\nRun [bold cyan]ralph tip[/bold cyan] to generate tips "
                "for the current round [dim](coming soon)[/dim]"
            )
        except ImportError:
            print("Ralph is thinking about this week's NRL tips...")
            print(
                "\nRun `ralph tip` to generate tips "
                "for the current round (coming soon)"
            )


if __name__ == "__main__":
    main()
