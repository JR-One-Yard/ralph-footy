"""Result tracking and accuracy calculation for Ralph — NRL Footy Forecaster.

Saves tips logs after each round, loads results files entered by the user,
matches tips to results, and calculates overall and per-tier accuracy for
the season record.
"""

from __future__ import annotations

import json
from pathlib import Path

from ralph.models import RoundTips

# Default base directories, relative to the project root.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_TIPS_LOG_DIR = _PROJECT_ROOT / "data" / "tips_log"
_DEFAULT_RESULTS_DIR = _PROJECT_ROOT / "data" / "results"


def _tips_log_dir(data_dir: Path | None) -> Path:
    """Return the tips_log directory, using the override if provided."""
    if data_dir is not None:
        return data_dir / "tips_log"
    return _DEFAULT_TIPS_LOG_DIR


def _results_dir(data_dir: Path | None) -> Path:
    """Return the results directory, using the override if provided."""
    if data_dir is not None:
        return data_dir / "results"
    return _DEFAULT_RESULTS_DIR


# ---------------------------------------------------------------------------
# save_tips_log
# ---------------------------------------------------------------------------


def save_tips_log(round_tips: RoundTips, data_dir: Path | None = None) -> Path:
    """Serialise a RoundTips object to JSON in the tips_log directory.

    Parameters
    ----------
    round_tips:
        The generated tips for the round.
    data_dir:
        Override the base data directory.  When provided, files are
        written to ``<data_dir>/tips_log/round_NN.json``.

    Returns
    -------
    The :class:`Path` of the file that was written.
    """
    out_dir = _tips_log_dir(data_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = f"round_{round_tips.round_number:02d}.json"
    filepath = out_dir / filename

    payload = {
        "round_number": round_tips.round_number,
        "season": round_tips.season,
        "generated_at": round_tips.generated_at.isoformat(),
        "tips": [
            {
                "home_team": tip.game.home_team,
                "away_team": tip.game.away_team,
                "pick": tip.pick,
                "confidence": tip.confidence,
                "confidence_label": tip.confidence_label,
            }
            for tip in round_tips.tips
        ],
    }

    filepath.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return filepath


# ---------------------------------------------------------------------------
# load_tips_log
# ---------------------------------------------------------------------------


def load_tips_log(round_number: int, data_dir: Path | None = None) -> dict:
    """Load a tips log JSON file for the given round.

    Parameters
    ----------
    round_number:
        The round to load.
    data_dir:
        Override the base data directory.

    Returns
    -------
    The parsed JSON as a dict.

    Raises
    ------
    FileNotFoundError
        If the tips log file does not exist.
    """
    directory = _tips_log_dir(data_dir)
    filepath = directory / f"round_{round_number:02d}.json"

    if not filepath.exists():
        raise FileNotFoundError(
            f"No tips found for round {round_number}. Run `ralph tip --round {round_number}` first."
        )

    return json.loads(filepath.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# load_results
# ---------------------------------------------------------------------------

_REQUIRED_RESULT_FIELDS = {"home_team", "away_team", "winner"}


def load_results(round_number: int, data_dir: Path | None = None) -> list[dict]:
    """Load and validate a results JSON file for the given round.

    Parameters
    ----------
    round_number:
        The round to load.
    data_dir:
        Override the base data directory.

    Returns
    -------
    A list of result dicts, each with ``home_team``, ``away_team``,
    and ``winner`` keys.

    Raises
    ------
    FileNotFoundError
        If the results file does not exist.
    ValueError
        If the file is malformed, missing required fields, or the
        ``winner`` does not match either team.
    """
    directory = _results_dir(data_dir)
    filepath = directory / f"round_{round_number:02d}.json"

    if not filepath.exists():
        raise FileNotFoundError(
            f"Results file not found: {filepath}\n"
            f"Please create {filepath} with the round's results."
        )

    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {filepath}: {exc}") from exc

    results = data.get("results")
    if not isinstance(results, list):
        raise ValueError(f"Expected a 'results' list in {filepath}")

    for idx, result in enumerate(results):
        missing = _REQUIRED_RESULT_FIELDS - set(result.keys())
        if missing:
            raise ValueError(f"Result {idx}: missing required fields: {sorted(missing)}")

        home = result["home_team"]
        away = result["away_team"]
        winner = result["winner"]

        # AC-08: winner must match one of the two teams.
        if winner not in (home, away):
            raise ValueError(
                f"Result {idx}: winner '{winner}' does not match "
                f"home_team '{home}' or away_team '{away}'."
            )

        # AC-11: NRL games cannot draw in regular season (golden point).
        # A draw is implied if home_score == away_score, but since we
        # only have the winner field, the only way to signal a draw is
        # if someone sets winner to something other than home/away,
        # which is already caught above.  We also check for an explicit
        # "draw" field if provided.
        if result.get("draw", False):
            raise ValueError(
                f"Result {idx}: draws are not supported in SLC. "
                f"NRL games cannot draw in regular season due to golden point."
            )

        # Also check scores if present — if scores are equal, that is a draw.
        home_score = result.get("home_score")
        away_score = result.get("away_score")
        if home_score is not None and away_score is not None:
            if home_score == away_score:
                raise ValueError(
                    f"Result {idx}: home_score ({home_score}) equals "
                    f"away_score ({away_score}). NRL games cannot draw "
                    f"in regular season due to golden point."
                )

    return results


# ---------------------------------------------------------------------------
# match_results
# ---------------------------------------------------------------------------


def match_results(tips_log: dict, results: list[dict]) -> list[dict]:
    """Match each tip in the tips log to its result.

    Parameters
    ----------
    tips_log:
        The loaded tips log dict (from :func:`load_tips_log`).
    results:
        The loaded results list (from :func:`load_results`).

    Returns
    -------
    A list of dicts, one per matched game::

        {
            "game": "Sydney Roosters v Brisbane Broncos",
            "pick": "Sydney Roosters",
            "result": "Sydney Roosters",
            "correct": True,
            "confidence": 0.6173,
            "confidence_label": "Lean",
        }
    """
    # Build a lookup from (home_team, away_team) -> result dict.
    result_lookup: dict[tuple[str, str], dict] = {}
    for r in results:
        key = (r["home_team"], r["away_team"])
        result_lookup[key] = r

    matched: list[dict] = []
    for tip in tips_log.get("tips", []):
        key = (tip["home_team"], tip["away_team"])
        result = result_lookup.get(key)

        if result is None:
            # No matching result for this tip — skip.
            continue

        matched.append(
            {
                "game": f"{tip['home_team']} v {tip['away_team']}",
                "pick": tip["pick"],
                "result": result["winner"],
                "correct": tip["pick"] == result["winner"],
                "confidence": tip.get("confidence", 0.0),
                "confidence_label": tip.get("confidence_label", "Unknown"),
            }
        )

    return matched


# ---------------------------------------------------------------------------
# calculate_accuracy
# ---------------------------------------------------------------------------


def calculate_accuracy(matched: list[dict]) -> dict:
    """Calculate overall and per-tier accuracy from matched results.

    Parameters
    ----------
    matched:
        List of matched result dicts from :func:`match_results`.

    Returns
    -------
    A dict with::

        {
            "overall": 0.625,       # float (0.0 to 1.0)
            "by_tier": {
                "Lock": 0.833,
                "Lean": 0.583,
                "Coin Flip": 0.333,
            },
            "total": 8,
            "correct": 5,
        }

    If there are no matched results, ``overall`` is 0.0 and tier
    values are also 0.0.
    """
    total = len(matched)
    correct = sum(1 for m in matched if m["correct"])
    overall = correct / total if total > 0 else 0.0

    # Per-tier accuracy.
    tiers = ("Lock", "Lean", "Coin Flip")
    by_tier: dict[str, float] = {}
    for tier in tiers:
        tier_matches = [m for m in matched if m["confidence_label"] == tier]
        tier_total = len(tier_matches)
        tier_correct = sum(1 for m in tier_matches if m["correct"])
        by_tier[tier] = tier_correct / tier_total if tier_total > 0 else 0.0

    return {
        "overall": overall,
        "by_tier": by_tier,
        "total": total,
        "correct": correct,
    }


# ---------------------------------------------------------------------------
# get_season_record
# ---------------------------------------------------------------------------


def get_season_record(data_dir: Path | None = None) -> dict:
    """Scan all completed rounds and aggregate accuracy.

    A round is considered "completed" when both a tips log and a results
    file exist for that round number.

    Parameters
    ----------
    data_dir:
        Override the base data directory.

    Returns
    -------
    A dict with::

        {
            "rounds_completed": [1, 3],   # which rounds are done
            "overall": 0.625,
            "by_tier": {"Lock": ..., "Lean": ..., "Coin Flip": ...},
            "total": 16,
            "correct": 10,
        }

    If no rounds have both tips and results, returns a dict with
    ``rounds_completed`` as an empty list and zeroed-out stats.
    """
    tips_dir = _tips_log_dir(data_dir)
    results_dir = _results_dir(data_dir)

    # Discover which round numbers have tips logs.
    tips_rounds: set[int] = set()
    if tips_dir.exists():
        for f in tips_dir.glob("round_*.json"):
            try:
                rn = int(f.stem.split("_")[1])
                tips_rounds.add(rn)
            except (IndexError, ValueError):
                continue

    # Discover which round numbers have results.
    results_rounds: set[int] = set()
    if results_dir.exists():
        for f in results_dir.glob("round_*.json"):
            try:
                rn = int(f.stem.split("_")[1])
                results_rounds.add(rn)
            except (IndexError, ValueError):
                continue

    # Only completed rounds (both exist).
    completed = sorted(tips_rounds & results_rounds)

    if not completed:
        return {
            "rounds_completed": [],
            "overall": 0.0,
            "by_tier": {"Lock": 0.0, "Lean": 0.0, "Coin Flip": 0.0},
            "total": 0,
            "correct": 0,
        }

    # Aggregate all matched results across completed rounds.
    all_matched: list[dict] = []
    for rn in completed:
        tips_log = load_tips_log(rn, data_dir)
        results = load_results(rn, data_dir)
        matched = match_results(tips_log, results)
        all_matched.extend(matched)

    accuracy = calculate_accuracy(all_matched)

    return {
        "rounds_completed": completed,
        **accuracy,
    }
