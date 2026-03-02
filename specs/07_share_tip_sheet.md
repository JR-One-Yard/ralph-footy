# Spec 07: Share the Tip Sheet

**Activity:** Share the Tip Sheet
**One-liner:** Get the full weekly output in a format ready to share with colleagues.

---

## User Story

> As a workplace footy tipper, I want Ralph's tip sheet formatted nicely so that I can paste it directly into Slack or email and it looks good without any manual editing.

---

## Scope

### IN (SLC v1)

- Rich CLI output to the terminal using the `rich` library.
- Markdown file output to `data/tips/round_<NN>.md`.
- Output follows the per-game template from GENESIS.md (emoji headers, odds breakdown, rationale, teaching moment).
- The tip sheet includes a header, all games in order, the teaching moment, and a footer.
- The terminal output is coloured and styled. The Markdown output is plain text compatible with Slack and email.

### OUT (Deferred)

- Slack bot integration.
- Email automation.
- Web UI.
- Interactive elements.
- Leaderboard tracking.
- "Round preview" narrative.

---

## Output Template

### Per-Game Block

```
=== GAME {game_number}: {home_team} vs {away_team} ===
{venue} | {kickoff_display}

RALPH'S TIP: {pick} ({confidence_pct} confidence — {confidence_label})

MARKET SAYS: {home_team} {home_best_odds} | {away_team} {away_best_odds}
  Implied: {home_team} {home_prob_pct} | {away_team} {away_prob_pct} (after overround removal)

RATIONALE:
{rationale}
```

### Tip Sheet Header

```
==================================================
  RALPH — Footy Forecaster
  NRL {season} — Round {round_number} Tips
  Generated: {generated_date}
==================================================
```

### Teaching Moment Block (Once Per Sheet)

```
--------------------------------------------------
DID YOU KNOW? — {topic_title}
--------------------------------------------------
{teaching_snippet}
```

### Tip Sheet Footer

```
--------------------------------------------------
Ralph's Season Record: {correct}/{total} ({accuracy_pct})
Lock: {lock_correct}/{lock_total} | Lean: {lean_correct}/{lean_total} | Coin Flip: {cf_correct}/{cf_total}
--------------------------------------------------
"I don't know everything about footy, but I know what the bookies think."
— Ralph v{version}
```

If no season record exists yet (first round, results not entered), the footer shows:

```
--------------------------------------------------
Ralph's Season Record: No results yet — check back after the round!
--------------------------------------------------
"I don't know everything about footy, but I know what the bookies think."
— Ralph v{version}
```

---

## Rich Console Output

The terminal output uses `rich` for styling:

- **Header**: `Panel` with bold green text and green border.
- **Game number**: Bold cyan text.
- **RALPH'S TIP line**: Bold green for Lock, bold yellow for Lean, bold red for Coin Flip.
- **MARKET SAYS**: Dim/grey text for the odds line.
- **RATIONALE**: Normal white text, indented.
- **DID YOU KNOW?**: Yellow header text, normal body.
- **Footer**: Dim text with the season record.
- **Separators**: Use `rich.rule.Rule` or `Console.rule()` between games.

### Colour Mapping

| Confidence Tier | Colour | Rationale |
|----------------|--------|-----------|
| Lock | Green | Strong confidence — go for it |
| Lean | Yellow | Moderate confidence — proceed with caution |
| Coin Flip | Red | Low confidence — could go either way |

---

## Markdown File Output

### File Location

```
data/tips/round_<NN>.md
```

### Markdown Format

The Markdown version uses the same structure but with Markdown formatting instead of rich styling. It uses emoji prefixes for visual distinction when pasted into Slack:

```markdown
# RALPH — NRL {season} Round {round_number} Tips

*Generated {generated_date}*

---

## GAME {game_number}: {home_team} vs {away_team}
**{venue}** | {kickoff_display}

**RALPH'S TIP:** {pick} ({confidence_pct} confidence — {confidence_label})

**MARKET SAYS:** {home_team} {home_best_odds} | {away_team} {away_best_odds}
Implied: {home_team} {home_prob_pct} | {away_team} {away_prob_pct} (after overround removal)

**RATIONALE:**
{rationale}

---

## DID YOU KNOW? — {topic_title}

{teaching_snippet}

---

*Ralph's Season Record: {correct}/{total} ({accuracy_pct})*
*Lock: {lock_correct}/{lock_total} | Lean: {lean_correct}/{lean_total} | Coin Flip: {cf_correct}/{cf_total}*

---

*"I don't know everything about footy, but I know what the bookies think."*
*— Ralph v{version}*
```

---

## Input Contract

- `RoundTips` object with all `Tip` objects populated (including `rationale`).
- Teaching snippet string (from Spec 05).
- Season record dict (from Spec 06, optional — may not exist for the first round).

---

## Output Contract

Two outputs are produced:

1. **Console**: Styled text printed to stdout via `rich.Console`.
2. **File**: Markdown file written to `data/tips/round_<NN>.md`.

Both contain identical content, differing only in formatting.

---

## Acceptance Criteria

1. **AC-01**: Running `ralph tip --round 1` prints a styled tip sheet to the terminal using `rich`.
2. **AC-02**: Running `ralph tip --round 1` creates a `data/tips/round_01.md` file.
3. **AC-03**: The terminal output includes the header with season year and round number.
4. **AC-04**: Each game in the output shows the game number, teams, venue, and kickoff.
5. **AC-05**: Each game shows Ralph's pick with the confidence percentage and tier label.
6. **AC-06**: Each game shows the market odds and implied probabilities.
7. **AC-07**: Each game shows the rationale text.
8. **AC-08**: The teaching moment appears once per tip sheet (not once per game), after all games.
9. **AC-09**: The footer shows the season record if results exist for previous rounds.
10. **AC-10**: The footer shows "No results yet" if this is the first round or no results have been entered.
11. **AC-11**: The Markdown file can be opened in any text editor and is valid Markdown.
12. **AC-12**: The terminal output uses colour: green for Lock tips, yellow for Lean, red for Coin Flip.
13. **AC-13**: The kickoff time is displayed in a human-readable format: "Friday 7:55pm" style (day of week + 12-hour time).
14. **AC-14**: Games are numbered sequentially starting from 1 in the order they appear in the fixture file.
15. **AC-15**: Odds are displayed with a dollar sign prefix: "$1.55" not "1.55".

---

## Implementation Notes

### Files to Modify

- `ralph/output.py` — Replace the three stub functions with working implementations:
  - `format_tip_console(tip: Tip, market_view: MarketView, game_number: int, console: Console) -> None` — Print a single game's tip to the console.
  - `format_round_console(round_tips: RoundTips, market_views: list[MarketView], teaching_snippet: str, season_record: dict | None, console: Console) -> None` — Print the full tip sheet to the console.
  - `format_round_markdown(round_tips: RoundTips, market_views: list[MarketView], teaching_snippet: str, season_record: dict | None) -> str` — Return the full tip sheet as a Markdown string.
  - `save_tip_sheet(round_tips: RoundTips, market_views: list[MarketView], teaching_snippet: str, season_record: dict | None) -> None` — Write the Markdown file to `data/tips/round_<NN>.md`.
- `ralph/cli.py` — Wire up the output functions to the `tip` subcommand. The `cmd_tip` function should:
  1. Load fixtures and odds (Spec 01, 02).
  2. Generate market views (Spec 02).
  3. Generate tips (Spec 03).
  4. Generate rationale for each tip (Spec 04).
  5. Generate teaching snippet (Spec 05).
  6. Save tips log (Spec 06).
  7. Load season record if available (Spec 06).
  8. Output to console and Markdown file (this spec).

### Files to Create

- `tests/test_output.py` — Unit tests covering key acceptance criteria (focus on content correctness, not styling).

### Directories to Create

- `data/tips/` — For tip sheet Markdown files (create with `.gitkeep`).

### Design Decisions

- **`rich` is a required dependency, not optional.** The current `cli.py` wraps `rich` imports in `try/except` for graceful degradation. For SLC, `rich` is listed in `pyproject.toml` dependencies and should always be available. Remove the `try/except` guards and import `rich` directly.
- **Kickoff display format.** Use `kickoff.strftime("%-I:%M%p").lower()` for the time (e.g., "7:55pm") and `kickoff.strftime("%A")` for the day (e.g., "Friday"). Combined: "Friday 7:55pm". Note: `%-I` is Unix-specific. For cross-platform compatibility, strip leading zeros manually if needed.
- **Odds display uses best available odds.** When multiple bookmakers are present, display the best (lowest) home odds and best (highest) away odds. This gives the user the most favourable view. When only one bookmaker is present, display those odds.
- **Markdown designed for Slack.** Slack renders basic Markdown (bold, italic, headers). The Markdown output should use only features that Slack supports. Avoid HTML, tables, or complex Markdown extensions.
- **Console output and Markdown output share logic.** Extract a common data preparation function that both renderers consume. Do not duplicate logic.
