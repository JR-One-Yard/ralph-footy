# Agent Configuration — Ralph SLC v1

Operational instructions for the autonomous coding loop.

---

## Environment

| Setting | Value |
|---------|-------|
| **Python version** | 3.11+ |
| **Package manager** | pip with pyproject.toml (hatchling build backend) |
| **Install command** | `pip install -e ".[dev]"` |
| **Test command** | `pytest` |
| **Test (verbose)** | `pytest -v` |
| **Lint command** | `ruff check ralph/ tests/` |
| **Format command** | `ruff format ralph/ tests/` |
| **Format check** | `ruff format --check ralph/ tests/` |
| **Run Ralph** | `ralph tip --round 1` (after install) |

---

## Key Libraries

| Library | Purpose | Notes |
|---------|---------|-------|
| `rich` | CLI output styling | Required dependency. Import directly — no try/except guards. |
| `anthropic` | Claude API client | Listed in pyproject.toml but **NOT USED in SLC**. Do not import or call it. |
| `requests` | HTTP requests | Listed in pyproject.toml but **NOT USED in SLC**. Do not import or call it. |
| `pytest` | Test framework | Dev dependency. |
| `ruff` | Linter and formatter | Dev dependency. |

---

## Conventions

### Code Style

- **Type hints everywhere.** Every function signature must have type annotations for parameters and return value.
- **Dataclasses for models.** All data structures in `ralph/models.py` use `@dataclass`. Do not use dicts where a dataclass is appropriate.
- **`from __future__ import annotations`** at the top of every module (already present in existing files — maintain this).
- **Docstrings on all public functions and classes.** Use Google-style docstrings.
- **No classes with methods beyond `@property` for simple computed fields.** Keep logic in plain functions, not methods. The dataclasses are data containers, not service objects.
- **Line length: 100 characters** (configured in pyproject.toml).
- **Import sorting: isort-compatible** (ruff handles this with the "I" rule).

### Project Structure

```
ralph/
  __init__.py          # Package init, __version__
  cli.py               # CLI entry point (argparse)
  models.py            # Dataclasses: Game, Odds, Tip, RoundTips, MarketView
  fixtures.py          # [NEW] Fixture loading and validation
  market.py            # Odds-to-probability conversion, consensus engine
  tips.py              # Tip generation (pick + confidence)
  rationale.py         # [NEW] Template-driven rationale generation
  teaching.py          # [NEW] Teaching snippet selection and rendering
  tracking.py          # [NEW] Result tracking and accuracy calculation
  output.py            # Rich console output and Markdown file generation
  calibration.py       # STUB — not implemented in SLC
  sentiment.py         # STUB — not implemented in SLC

data/
  rounds/              # Input: fixture + odds JSON files (user-created)
  results/             # Input: result JSON files (user-created)
  tips/                # Output: Markdown tip sheets (generated)
  tips_log/            # Output: Machine-readable tips log (generated)
  teaching_topics.json # Pre-written teaching snippets

tests/
  conftest.py          # Shared pytest fixtures
  test_fixtures.py     # Spec 01 tests
  test_market.py       # Spec 02 tests
  test_tips.py         # Spec 03 tests
  test_rationale.py    # Spec 04 tests
  test_teaching.py     # Spec 05 tests
  test_tracking.py     # Spec 06 tests
  test_output.py       # Spec 07 tests
  test_e2e.py          # End-to-end integration test

specs/                 # Spec files (reference only, do not modify)
```

### Data Format

- **All data files are JSON.** No YAML, no CSV, no SQLite.
- **File naming:** `round_<NN>.json` with zero-padded round numbers (01-27).
- **Dates in JSON:** ISO 8601 format `YYYY-MM-DDTHH:MM` (no timezone, no seconds).
- **Probabilities:** Stored as floats between 0.0 and 1.0 in code. Displayed as percentages (e.g., "66%") in output.
- **Odds:** Stored as floats > 1.0 (decimal/Australian format). Displayed with dollar sign prefix (e.g., "$1.55") in output.

---

## Critical Rules

1. **Do NOT use the Claude API (anthropic library) in SLC.** All teaching content is pre-written templates. All rationale is template-driven. There is no LLM integration in this release.

2. **Do NOT add web scraping or HTTP requests.** All input is from local JSON files. No `requests.get()`, no `urllib`, no external APIs.

3. **Do NOT add new dependencies to pyproject.toml.** The existing dependencies (`anthropic`, `requests`, `rich`, `pytest`, `ruff`) are sufficient. Do not add `jsonschema`, `pydantic`, `click`, or any other library.

4. **Do NOT modify the stubs in `calibration.py` or `sentiment.py`.** These are placeholders for future iterations. Leave them as `raise NotImplementedError(...)`.

5. **Keep it deterministic.** Same input file must always produce the same output. No `random.choice()`, no `time.time()` in logic paths, no non-deterministic behaviour.

6. **Rich is required, not optional.** Import `rich` directly. Remove any `try/except ImportError` guards around rich imports in existing code.

7. **Tests derive from acceptance criteria.** Every acceptance criterion in a spec becomes at least one test function. Name tests `test_ac{NN}_{description}`.

8. **Error messages must be actionable.** When validation fails, tell the user exactly what is wrong and how to fix it. Include the expected format and the file path.

---

## Workflow for the Coding Agent

1. Read `IMPLEMENTATION_PLAN.md` to understand the task order.
2. For each task, read the corresponding spec in `specs/`.
3. Implement the code changes described in the task.
4. Write tests covering all acceptance criteria.
5. Run `pytest` to verify tests pass.
6. Run `ruff check` and `ruff format` to ensure lint/format compliance.
7. Move to the next task.
8. After Task 8 (CLI wiring), run the end-to-end smoke test: `ralph tip --round 1`.
9. After Task 9, verify the Definition of Done from `IMPLEMENTATION_PLAN.md`.

---

## Test Data Guidance

When creating test fixtures in `tests/conftest.py`, use realistic NRL data:

- **Teams:** Use actual 2025 NRL team names (e.g., "Penrith Panthers", "Sydney Roosters", "Melbourne Storm").
- **Venues:** Use actual NRL venue names (e.g., "BlueBet Stadium", "Allianz Stadium", "AAMI Park").
- **Odds:** Use realistic head-to-head odds ranges (typically $1.10 to $8.00 for NRL).
- **Rounds:** Use Round 1, 2025 as the primary test round.

---

## File I/O Conventions

- **Reading JSON:** Use `pathlib.Path` and `json.loads(path.read_text())`.
- **Writing JSON:** Use `json.dumps(data, indent=2)` and `path.write_text(content)`.
- **Data directory base:** All data paths resolve relative to the project root. Use `Path(__file__).resolve().parent.parent / "data"` from within the `ralph/` package to locate the data directory.
- **Create directories on write:** When writing output files (tips, tips_log), create parent directories with `path.parent.mkdir(parents=True, exist_ok=True)`.
