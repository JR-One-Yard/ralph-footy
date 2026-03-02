# Implementation Plan — Ralph SLC v1

## Overview

We are building the SLC (Simple, Lovable, Complete) first release of Ralph, an NRL Footy Forecaster. The SLC slice delivers a CLI tool that:

1. Reads manually-entered fixture and odds data from a JSON file.
2. Converts bookmaker odds to true implied probabilities (removing overround).
3. Picks the team with the higher probability for each game.
4. Assigns confidence tiers (Lock / Lean / Coin Flip).
5. Generates template-driven rationale in Ralph's voice.
6. Selects a pre-written teaching snippet for the round.
7. Tracks tips and results for season-long accuracy.
8. Outputs a styled tip sheet to the terminal and a Markdown file.

The user workflow: manually create a round JSON file, run `ralph tip --round N`, get a formatted tip sheet, paste it into Slack. After the round, create a results JSON file, run `ralph results --round N`, then run `ralph record` to see the season record.

---

## Task List

### Task 1: Data Models & Foundation

**Spec:** 01_check_fixtures.md, 02_see_market_odds.md, 03_get_ralphs_pick.md
**Complexity:** S

Update the existing data models to support the full SLC pipeline.

**Files to modify:**
- `ralph/models.py` — Add `MarketView` dataclass. Update `Tip.confidence_label` thresholds (>=0.70 Lock, >=0.55 Lean, <0.55 Coin Flip). Add `teaching_moment: str = ""` field to `RoundTips`.

**Done when:**
- `MarketView` dataclass exists with `game`, `odds_sources`, `consensus_home_prob`, `consensus_away_prob`, `favourite`, and `favourite_prob` properties.
- `Tip.confidence_label` returns "Lock" for confidence >= 0.70, "Lean" for >= 0.55, "Coin Flip" for < 0.55.
- `RoundTips` has a `teaching_moment` string field.
- All existing tests still pass (if any).

---

### Task 2: Fixture Loading & Validation

**Spec:** 01_check_fixtures.md
**Complexity:** M

Build the fixture loading system that reads round JSON files and returns validated `Game` objects.

**Files to create:**
- `ralph/fixtures.py` — `load_fixtures()`, `validate_fixture_data()`, `_parse_kickoff()`.
- `tests/test_fixtures.py` — Tests for all 9 acceptance criteria from spec.
- `data/rounds/round_01.json` — Example fixture file with 8 games (Round 1, 2025).

**Files to modify:**
- None yet (CLI wiring happens in Task 8).

**Done when:**
- `load_fixtures(1)` reads `data/rounds/round_01.json` and returns a list of `Game` objects.
- Invalid files produce clear `ValueError` messages.
- All 9 acceptance criteria from spec 01 pass as tests.

**Depends on:** Task 1.

---

### Task 3: Market Consensus Engine

**Spec:** 02_see_market_odds.md
**Complexity:** M

Implement the odds-to-probability conversion, overround removal, and multi-bookmaker consensus averaging.

**Files to modify:**
- `ralph/market.py` — Replace all three stub functions with working implementations. Add `build_market_views()` function that takes fixture data (games + odds) and returns `list[MarketView]`.
- `ralph/fixtures.py` — Extend to parse the `odds` array from fixture JSON and return `Odds` objects alongside `Game` objects.

**Files to create:**
- `tests/test_market.py` — Tests for all 10 acceptance criteria from spec.

**Done when:**
- `odds_to_implied_probability(1.55)` returns 0.6452 (4dp).
- `remove_overround(0.6452, 0.4000)` returns (0.6173, 0.3827) (4dp).
- Output of `remove_overround` sums to 1.0 within 1e-9 tolerance.
- `market_consensus()` correctly averages across multiple sources and re-normalises.
- Odds <= 1.0 raise `ValueError`.
- All 10 acceptance criteria from spec 02 pass as tests.

**Depends on:** Task 1, Task 2.

---

### Task 4: Tip Generation

**Spec:** 03_get_ralphs_pick.md
**Complexity:** S

Implement the pick logic: select the team with the higher consensus probability, assign confidence tier.

**Files to modify:**
- `ralph/tips.py` — Replace stub functions. Update signatures to accept `MarketView` objects.

**Files to create:**
- `tests/test_tips.py` — Tests for all 12 acceptance criteria from spec.

**Done when:**
- `generate_tip()` picks the team with the higher consensus probability.
- Home team tie-break works when probabilities are exactly equal.
- `generate_round_tips()` returns a `RoundTips` with the correct number of `Tip` objects.
- All confidence tier boundaries are correct (AC-04 through AC-09).
- Rationale and teaching_moment fields are empty strings.

**Depends on:** Task 1, Task 3.

---

### Task 5: Rationale Generation

**Spec:** 04_understand_why.md
**Complexity:** M

Build the template-driven rationale system with Ralph's voice.

**Files to create:**
- `ralph/rationale.py` — Templates for all three tiers (4 each = 12 total), `team_short_name()`, `generate_rationale()`.
- `tests/test_rationale.py` — Tests for all 9 acceptance criteria from spec.

**Files to modify:**
- `ralph/tips.py` — Call `generate_rationale()` after generating each tip to populate the `rationale` field.

**Done when:**
- Each confidence tier has 4 templates.
- Templates are populated with actual game data (team names, probabilities, odds).
- `team_short_name("South Sydney Rabbitohs")` returns "Rabbitohs".
- No two games in the same round get identical rationale text.
- Output is deterministic (same input produces same output).
- All 9 acceptance criteria from spec 04 pass as tests.

**Depends on:** Task 4.

---

### Task 6: Teaching Content

**Spec:** 05_learn_something.md
**Complexity:** M

Create the pre-written teaching snippets and the selection/rendering system.

**Files to create:**
- `data/teaching_topics.json` — At least 10 teaching topics with templates and fallbacks.
- `ralph/teaching.py` — `load_teaching_topics()`, `select_topic()`, `build_teaching_context()`, `generate_teaching_snippet()`.
- `tests/test_teaching.py` — Tests for all 9 acceptance criteria from spec.

**Done when:**
- `data/teaching_topics.json` contains 10 topics covering the first 10 rounds.
- `select_topic(1, 10)` returns 0 (index of first topic).
- `select_topic(11, 10)` returns 0 (cycle restarts).
- Template variables are resolved with actual round data.
- Fallback text is used when variables cannot be resolved.
- No unresolved `{variable}` placeholders in output.
- All 9 acceptance criteria from spec 05 pass as tests.

**Depends on:** Task 3 (needs MarketView for context variables).

---

### Task 7: Result Tracking & Accuracy

**Spec:** 06_track_accuracy.md
**Complexity:** M

Build the result recording and accuracy calculation system.

**Files to create:**
- `ralph/tracking.py` — `save_tips_log()`, `load_tips_log()`, `load_results()`, `match_results()`, `calculate_accuracy()`, `get_season_record()`.
- `tests/test_tracking.py` — Tests for all 11 acceptance criteria from spec.
- `data/results/.gitkeep`
- `data/tips_log/.gitkeep`

**Files to modify:**
- None yet (CLI wiring happens in Task 8).

**Done when:**
- `save_tips_log()` writes a valid JSON file to `data/tips_log/`.
- `load_results()` validates results files and raises on invalid data.
- `match_results()` correctly identifies correct/incorrect picks.
- `calculate_accuracy()` returns overall and per-tier accuracy.
- `get_season_record()` scans all completed rounds.
- All 11 acceptance criteria from spec 06 pass as tests.

**Depends on:** Task 4 (needs `RoundTips` to save).

---

### Task 8: CLI Wiring & Output Formatting

**Spec:** 07_share_tip_sheet.md
**Complexity:** L

Wire everything together through the CLI. Build the rich console output and Markdown file generation.

**Files to modify:**
- `ralph/output.py` — Replace all stub functions. Implement `format_tip_console()`, `format_round_console()`, `format_round_markdown()`, `save_tip_sheet()`.
- `ralph/cli.py` — Rewrite `cmd_tip()` to run the full pipeline. Add `cmd_results()` and `cmd_record()` subcommands. Add `--round` argument. Remove `try/except` guards around rich imports.

**Files to create:**
- `tests/test_output.py` — Tests for key acceptance criteria (content correctness, file creation).
- `data/tips/.gitkeep`

**Done when:**
- `ralph tip --round 1` runs the full pipeline: load fixtures, build market views, generate tips, generate rationale, generate teaching snippet, save tips log, output to console and Markdown file.
- Terminal output uses rich styling with correct colours per confidence tier.
- `data/tips/round_01.md` is created with valid Markdown.
- `ralph results --round 1` processes a results file and prints the match summary.
- `ralph record` shows the season record.
- Kickoff times display as "Friday 7:55pm" format.
- All 15 acceptance criteria from spec 07 pass as tests.

**Depends on:** Tasks 2, 3, 4, 5, 6, 7 (this is the integration task).

---

### Task 9: End-to-End Test & Example Data

**Spec:** All specs
**Complexity:** S

Create a full end-to-end test with realistic data and verify the complete pipeline.

**Files to create:**
- `data/rounds/round_01.json` — Complete Round 1 fixture file with odds from 2 bookmakers (if not already created in Task 2, finalise it here).
- `tests/test_e2e.py` — End-to-end test that runs `ralph tip --round 1` and validates:
  - 8 tips generated.
  - All tips have non-empty rationale.
  - Teaching snippet is present.
  - Markdown file is created.
  - Tips log is created.

**Done when:**
- The end-to-end test passes.
- Running `ralph tip --round 1` from the command line produces valid output.
- A human reviewer can read the Markdown file and it looks good.

**Depends on:** Task 8.

---

## Dependency Graph

```
Task 1: Data Models
  |
  +---> Task 2: Fixture Loading
  |       |
  |       +---> Task 3: Market Engine
  |               |
  |               +---> Task 4: Tip Generation
  |               |       |
  |               |       +---> Task 5: Rationale
  |               |       |
  |               |       +---> Task 7: Tracking
  |               |
  |               +---> Task 6: Teaching Content
  |
  +---> (All tasks above)
          |
          +---> Task 8: CLI & Output (integration)
                  |
                  +---> Task 9: E2E Test
```

**Critical path:** 1 -> 2 -> 3 -> 4 -> 5 -> 8 -> 9

**Parallel work possible:**
- Task 5 (Rationale) and Task 7 (Tracking) can proceed in parallel after Task 4.
- Task 6 (Teaching) can proceed in parallel with Task 4 after Task 3.

---

## Testing Strategy

### Unit Tests (per task)

Each task creates its own test file in `tests/`. Tests are derived directly from the acceptance criteria in each spec. Every acceptance criterion becomes at least one test function.

**Naming convention:** `test_{module}::test_{ac_number}_{brief_description}`

Example:
```python
# tests/test_market.py
def test_ac01_odds_to_implied_probability():
    assert round(odds_to_implied_probability(1.55), 4) == 0.6452

def test_ac06_invalid_odds_raises_value_error():
    with pytest.raises(ValueError):
        odds_to_implied_probability(0.95)
```

### Integration Test (Task 9)

One end-to-end test that exercises the full pipeline with realistic fixture data. This test catches integration issues that unit tests miss (e.g., data format mismatches between modules).

### Test Data

- `tests/conftest.py` — Shared pytest fixtures providing sample `Game`, `Odds`, `MarketView`, `Tip`, and `RoundTips` objects.
- Test data should use realistic NRL team names, venues, and odds.

### Running Tests

```bash
pytest                  # Run all tests
pytest tests/test_market.py   # Run one module
pytest -v               # Verbose output
ruff check ralph/ tests/    # Lint
ruff format ralph/ tests/   # Format
```

---

## Definition of Done

The SLC v1 release is shippable when ALL of the following are true:

1. **All 9 tasks are complete** and their "done when" criteria are met.
2. **All tests pass**: `pytest` exits with 0 errors, 0 failures.
3. **Lint clean**: `ruff check ralph/ tests/` reports 0 errors.
4. **Format clean**: `ruff format --check ralph/ tests/` reports no changes needed.
5. **End-to-end smoke test**: Running `ralph tip --round 1` with the example fixture file produces:
   - 8 game tips printed to the terminal with rich styling.
   - Each tip has a rationale in Ralph's voice.
   - One teaching moment per sheet.
   - A Markdown file at `data/tips/round_01.md`.
   - A tips log at `data/tips_log/round_01.json`.
6. **Result tracking works**: After creating `data/results/round_01.json`, running `ralph results --round 1` shows which picks were correct, and `ralph record` shows the season record.
7. **Copy-paste test**: The Markdown file content, when pasted into a Slack channel, renders readably without manual editing.
8. **Ralph has personality**: The rationale text sounds like a cheeky Australian footy mate, not a spreadsheet.
9. **No external dependencies beyond pip**: No API keys, no web scraping, no database. Just `pip install -e .` and go.
