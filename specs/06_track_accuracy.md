# Spec 06: Track How Ralph Is Going

**Activity:** Track How Ralph Is Going
**One-liner:** See Ralph's season accuracy and whether his confidence levels are honest.

---

## User Story

> As a workplace footy tipper, I want to see how Ralph's picks have performed over the season so that I know whether his confidence levels mean anything and whether he's actually any good.

---

## Scope

### IN (SLC v1)

- Manual result entry: after a round is complete, the user enters the actual winner for each game.
- Results are stored in a JSON log file alongside the original tips.
- Running accuracy calculation: `correct / total` across all completed rounds.
- Per-tier accuracy: separate accuracy for Lock, Lean, and Coin Flip picks.
- CLI subcommand `ralph results --round <N>` to enter results.
- CLI subcommand `ralph record` to display the season record.

### OUT (Deferred)

- Brier Score calculation (deferred until Round 6+ when there's enough data).
- Calibration curves.
- Comparison to a "just pick the favourite" baseline.
- Weekly accuracy trend charts.
- LLM-generated performance narrative.
- Automatic result fetching from NRL data sources.
- ROI/Sharpe ratio calculations.

---

## Data Model

### Results File Location

```
data/results/round_<NN>.json
```

### Results JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "NRL Round Results",
  "type": "object",
  "required": ["round_number", "season", "results"],
  "properties": {
    "round_number": {
      "type": "integer",
      "minimum": 1,
      "maximum": 27
    },
    "season": {
      "type": "integer",
      "minimum": 2025
    },
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["home_team", "away_team", "winner"],
        "properties": {
          "home_team": {
            "type": "string"
          },
          "away_team": {
            "type": "string"
          },
          "winner": {
            "type": "string",
            "description": "The full team name of the winner. Must match either home_team or away_team exactly."
          }
        }
      }
    }
  }
}
```

### Example Results File

```json
{
  "round_number": 1,
  "season": 2025,
  "results": [
    {
      "home_team": "Sydney Roosters",
      "away_team": "Brisbane Broncos",
      "winner": "Sydney Roosters"
    },
    {
      "home_team": "Penrith Panthers",
      "away_team": "Cronulla Sharks",
      "winner": "Penrith Panthers"
    },
    {
      "home_team": "Melbourne Storm",
      "away_team": "Canterbury Bulldogs",
      "winner": "Canterbury Bulldogs"
    }
  ]
}
```

### Tips Log File (Generated Automatically)

When Ralph generates tips for a round, the tips are saved to:

```
data/tips_log/round_<NN>.json
```

This is a machine-readable log of Ralph's predictions, separate from the human-readable Markdown output (Spec 07). Schema:

```json
{
  "round_number": 1,
  "season": 2025,
  "generated_at": "2025-03-05T14:30:00",
  "tips": [
    {
      "home_team": "Sydney Roosters",
      "away_team": "Brisbane Broncos",
      "pick": "Sydney Roosters",
      "confidence": 0.6173,
      "confidence_label": "Lean"
    }
  ]
}
```

---

## Accuracy Calculations

### Overall Accuracy

```
accuracy = correct_picks / total_picks
```

Where:
- `correct_picks` = number of games where `tip.pick == result.winner`
- `total_picks` = total number of games tipped across all completed rounds

### Per-Tier Accuracy

Calculate accuracy separately for each confidence tier:

```
lock_accuracy = lock_correct / lock_total
lean_accuracy = lean_correct / lean_total
coin_flip_accuracy = coin_flip_correct / coin_flip_total
```

### Season Record Display Format

```
Ralph's Season Record
=====================
Overall: 14/24 (58.3%) after 3 rounds

By Confidence:
  Lock:      5/6  (83.3%)
  Lean:      7/12 (58.3%)
  Coin Flip: 2/6  (33.3%)

Ralph says: "Not bad for a robot who's never held a footy."
```

---

## Input Contract

### For Result Entry (`ralph results --round <N>`)

The user creates a `data/results/round_<NN>.json` file manually (same workflow as fixture entry). The CLI command validates the file and matches results against the tips log.

### For Record Display (`ralph record`)

No input required. The command scans `data/tips_log/` and `data/results/` for all rounds that have both tips and results.

---

## Output Contract

### `ralph results --round <N>`

- Validates that tips exist for the round (in `data/tips_log/`).
- Validates the results file.
- Matches each result to the corresponding tip.
- Prints a per-game summary showing Ralph's pick, the actual winner, and whether it was correct.
- Saves the match results internally for the `ralph record` command.

### `ralph record`

- Scans all completed rounds (those with both tips and results).
- Calculates overall and per-tier accuracy.
- Prints the season record in the format above.

---

## Acceptance Criteria

1. **AC-01**: When `ralph tip --round 1` generates tips, a `data/tips_log/round_01.json` file is created with the correct schema.
2. **AC-02**: Given a valid `data/results/round_01.json` and matching tips log, `ralph results --round 1` correctly identifies which picks were right and wrong.
3. **AC-03**: Given Ralph picked "Sydney Roosters" and the winner is "Sydney Roosters", the pick is marked correct.
4. **AC-04**: Given Ralph picked "Sydney Roosters" and the winner is "Brisbane Broncos", the pick is marked incorrect.
5. **AC-05**: Given results for rounds 1-3, `ralph record` calculates the cumulative accuracy across all three rounds.
6. **AC-06**: Per-tier accuracy is calculated correctly: Lock picks are counted separately from Lean and Coin Flip picks.
7. **AC-07**: Given no results files exist, `ralph record` prints a message like "No results recorded yet. Run `ralph results --round <N>` after each round."
8. **AC-08**: Given a results file where the `winner` field does not match either `home_team` or `away_team`, a `ValueError` is raised.
9. **AC-09**: Given a results file for a round where no tips log exists, the command prints a clear error: "No tips found for round N. Run `ralph tip --round N` first."
10. **AC-10**: The tips log file stores the `confidence` (float) and `confidence_label` (string) for each tip, enabling per-tier accuracy.
11. **AC-11**: Draws are not handled in SLC (NRL games cannot draw in regular season due to golden point). If a draw is entered, raise a `ValueError`.

---

## Implementation Notes

### Files to Create

- `ralph/tracking.py` — Result tracking and accuracy calculation:
  - `save_tips_log(round_tips: RoundTips) -> None` — Save tips to `data/tips_log/round_<NN>.json`.
  - `load_tips_log(round_number: int) -> dict` — Load a tips log file.
  - `load_results(round_number: int) -> dict` — Load and validate a results file.
  - `match_results(tips_log: dict, results: dict) -> list[dict]` — Match tips to results, return list of `{"pick": str, "winner": str, "correct": bool, "confidence_label": str}`.
  - `calculate_accuracy(matched_results: list[dict]) -> dict` — Calculate overall and per-tier accuracy.
  - `get_season_record() -> dict` — Scan all completed rounds and compute the full season record.
- `tests/test_tracking.py` — Unit tests covering all acceptance criteria.

### Files to Modify

- `ralph/cli.py` — Add `results` and `record` subcommands.
  - `ralph results --round <N>` — Process results for a round.
  - `ralph record` — Show season record.
- `ralph/tips.py` or the main pipeline — Call `save_tips_log()` after tip generation.

### Directories to Create

- `data/results/` — For result files (create with `.gitkeep`).
- `data/tips_log/` — For tips log files (create with `.gitkeep`).

### Design Decisions

- **Results are entered via file, not interactive prompt.** Keeps the workflow consistent with fixture/odds entry. The user creates a JSON file and points the CLI at it. This is simpler to implement and test than an interactive prompt.
- **Tips log is separate from Markdown output.** The Markdown tip sheet (Spec 07) is for humans. The tips log JSON is for the tracking system. They contain overlapping data but serve different purposes.
- **No Brier Score in SLC.** The `calibration.py` stub already defines the Brier Score function. It remains a stub in SLC. Basic win/loss accuracy is sufficient for the first release. Brier Score is meaningfully useful only after 6+ rounds of data.
- **Per-tier accuracy is essential.** Without it, there is no way to verify that Lock picks actually win more often than Coin Flip picks. This is the core promise of the confidence tiers.
