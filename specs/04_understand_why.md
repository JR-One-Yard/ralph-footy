# Spec 04: Understand Why

**Activity:** Understand Why
**One-liner:** Read a short, plain-English rationale for each pick explaining what drove the decision.

---

## User Story

> As a workplace footy tipper, I want Ralph to explain WHY he picked each team in 2-3 sentences so that I understand the reasoning and can talk about it with colleagues.

---

## Scope

### IN (SLC v1)

- Template-driven rationale for each game.
- Templates are parameterised with actual numbers from the market analysis.
- Ralph's voice: cheeky, Australian, humble, conversational. NOT robotic or academic.
- Multiple templates per confidence tier to avoid repetitive output across games in the same round.
- Rationale references: the picked team, the consensus probability, the odds range, and the confidence tier.

### OUT (Deferred)

- LLM-generated bespoke rationale.
- References to team form, head-to-head records, or specific player performance.
- Bayesian update explanations ("prior was X, news shifted to Y").
- Any rationale that references data beyond what is in the fixture/odds file.

---

## Template System

### Template Variables

The following variables are available for interpolation in every template:

| Variable | Type | Example | Description |
|----------|------|---------|-------------|
| `{pick}` | str | `"Panthers"` | The team Ralph picked (short name derived from full team name) |
| `{other}` | str | `"Roosters"` | The opposing team (short name) |
| `{pick_prob_pct}` | str | `"66%"` | Consensus probability of the picked team, rounded to nearest whole % |
| `{other_prob_pct}` | str | `"34%"` | Consensus probability of the other team |
| `{pick_best_odds}` | str | `"$1.52"` | Best (lowest) odds offered on the picked team across all sources |
| `{other_best_odds}` | str | `"$2.55"` | Best (highest) odds offered on the other team across all sources |
| `{venue}` | str | `"BlueBet Stadium"` | The game venue |
| `{confidence_label}` | str | `"Lock"` / `"Lean"` / `"Coin Flip"` | The confidence tier |
| `{home_or_away}` | str | `"at home"` / `"on the road"` | Whether the picked team is home or away |

### Team Short Names

To make rationale sound natural, use the last word of the team name (the mascot) as the short name. Examples:
- "Penrith Panthers" -> "Panthers"
- "Sydney Roosters" -> "Roosters"
- "South Sydney Rabbitohs" -> "Rabbitohs"
- "St George Illawarra Dragons" -> "Dragons"
- "North Queensland Cowboys" -> "Cowboys"
- "New Zealand Warriors" -> "Warriors"
- "Gold Coast Titans" -> "Titans"

Implementation: `team_name.split()[-1]`

### Templates by Confidence Tier

#### Lock Templates (>= 70%)

```
Template L1:
"Ralph is backing the {pick} hard here. The market has them at {pick_prob_pct} {home_or_away} at {venue}, and that feels about right. The {other} would need something special to pull this one off."

Template L2:
"This is as close to a sure thing as footy gets (which is to say, it's still footy). The {pick} are {pick_prob_pct} favourites and Ralph reckons the bookies have read this one well. Back the {pick}."

Template L3:
"At {pick_best_odds}, the {pick} are short odds for a reason. The market says {pick_prob_pct} and Ralph is not about to argue with that {home_or_away}. Lock it in."

Template L4:
"Ralph doesn't like to use the word 'certainty' in footy, but the {pick} at {pick_prob_pct} {home_or_away} is about as confident as he gets. The {other} at {other_best_odds} are a genuine roughie here."
```

#### Lean Templates (55% - 69%)

```
Template E1:
"Ralph leans {pick} here — the market has them at {pick_prob_pct} which feels about right {home_or_away} at {venue}. The {other} are capable of making this ugly, but you'd want better odds to back them."

Template E2:
"The {pick} are favoured at {pick_prob_pct} and Ralph reckons that's fair. Not a certainty by any stretch — the {other} at {other_best_odds} aren't bad value if you fancy an upset — but Ralph's going with the market on this one."

Template E3:
"Market says {pick} at {pick_prob_pct}, Ralph says yeah, fair enough. The {pick} should get the job done {home_or_away} but the {other} won't make it easy. A solid lean, not a lock."

Template E4:
"This one leans {pick} — they're {pick_prob_pct} favourites and Ralph agrees with the market read. The {other} have a path to victory here at {other_best_odds}, but it's the harder road."
```

#### Coin Flip Templates (< 55%)

```
Template C1:
"Honestly? This one could go either way. The market has {pick} at a slight edge ({pick_prob_pct}) but Ralph wouldn't bet his house on it. Going {pick} because someone has to pick, but don't be shocked if the {other} salute."

Template C2:
"Ralph is going {pick} here, but it's basically a coin flip at {pick_prob_pct}. The bookies can't split them either — {pick_best_odds} vs {other_best_odds}. This is the kind of game that makes tipping comps fun (and frustrating)."

Template C3:
"The thinnest of margins separates these two. {pick} at {pick_prob_pct} gets the Ralph nod but he'd understand if you went the other way. {venue} could be the decider."

Template C4:
"If someone at the pub told you they KNEW who'd win this one, walk away — they're dreaming. Ralph has {pick} at {pick_prob_pct} but honestly, the {other} at {other_best_odds} are just as likely. Pencil in {pick} and hope for the best."
```

### Template Selection

Within each tier, select the template using a simple rotation based on the game's position in the round:

```python
template_index = game_position % len(templates_for_tier)
```

Where `game_position` is the 0-based index of the game in the round's fixture list. This ensures variety within a single round while remaining deterministic (same input always produces same output).

---

## Input Contract

A `Tip` object (with `pick`, `confidence`, and `game` populated) and the corresponding `MarketView` object (for odds data).

---

## Output Contract

The same `Tip` object with the `rationale` field populated with 2-3 sentences of Ralph-voiced text.

---

## Acceptance Criteria

1. **AC-01**: Given a Lock-tier tip (confidence >= 0.70), the rationale uses a Lock template and contains the picked team name and the probability percentage.
2. **AC-02**: Given a Lean-tier tip (confidence 0.55-0.69), the rationale uses a Lean template.
3. **AC-03**: Given a Coin Flip-tier tip (confidence < 0.55), the rationale uses a Coin Flip template.
4. **AC-04**: No rationale template produces identical output for two different games in the same round (template rotation ensures variety).
5. **AC-05**: Every rationale contains the actual probability percentage (not a placeholder like `{pick_prob_pct}`).
6. **AC-06**: Every rationale contains the picked team's short name (mascot).
7. **AC-07**: The `team_short_name()` function correctly extracts "Rabbitohs" from "South Sydney Rabbitohs" and "Dragons" from "St George Illawarra Dragons".
8. **AC-08**: Rationale text does not exceed 500 characters (keeps it punchy).
9. **AC-09**: Given the same round file input twice, the same rationale text is produced both times (deterministic).

---

## Implementation Notes

### Files to Create

- `ralph/rationale.py` — Rationale generation logic:
  - `LOCK_TEMPLATES: list[str]` — Lock tier templates.
  - `LEAN_TEMPLATES: list[str]` — Lean tier templates.
  - `COIN_FLIP_TEMPLATES: list[str]` — Coin Flip tier templates.
  - `team_short_name(full_name: str) -> str` — Extract mascot from full team name.
  - `generate_rationale(tip: Tip, market_view: MarketView, game_index: int) -> str` — Build the rationale string for a single tip.
- `tests/test_rationale.py` — Unit tests covering all acceptance criteria.

### Files to Modify

- `ralph/tips.py` — After generating each `Tip`, call `generate_rationale()` to populate the `rationale` field.

### Design Decisions

- **Templates live in Python code, not external files.** For SLC, there are only 12 templates. Putting them in a YAML/JSON file adds indirection without benefit. Move to external files when the template library grows beyond ~20 templates.
- **Short names use the last word.** This is a heuristic that works for all 17 NRL teams. It produces natural-sounding text: "Ralph leans Panthers" beats "Ralph leans Penrith Panthers".
- **Deterministic rotation, not random selection.** Using `game_index % template_count` is predictable and testable. Random selection would make output non-reproducible.
- **No f-string formatting at template definition time.** Templates use `{variable}` placeholders resolved at generation time via `str.format()`.
