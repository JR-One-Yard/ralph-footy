# Spec 05: Learn Something New

**Activity:** Learn Something New
**One-liner:** Get one teaching moment per round that explains a concept from probability, markets, AI, or behavioural science.

---

## User Story

> As a workplace footy tipper, I want Ralph to teach me something interesting about probability, betting markets, or AI each round so that I can share it at the office and actually learn how this stuff works.

---

## Scope

### IN (SLC v1)

- One "Did You Know?" teaching snippet per round (not per game).
- Pre-written teaching snippets stored in a JSON file (`data/teaching_topics.json`).
- Each snippet is 2-4 sentences, written in Ralph's voice.
- Snippets rotate through the topic library from GENESIS.md, one per round.
- Each snippet includes placeholder variables that reference that week's actual numbers where applicable.
- The snippet is attached to the `RoundTips` output and displayed once per tip sheet.

### OUT (Deferred)

- LLM-generated teaching content.
- Adaptive topic selection based on the round's games (e.g., teaching overround when a heavy favourite appears).
- Teaching content per game (one per round is sufficient for SLC).
- Interactive or multi-part teaching sequences.
- Audience complexity adaptation.

---

## Teaching Topics File

### File Location

```
data/teaching_topics.json
```

### Schema

```json
{
  "topics": [
    {
      "id": 1,
      "title": "Implied Probability",
      "category": "Statistics & Probability",
      "template": "When a bookie offers {example_odds} on a team, they're implying that team wins about {example_raw_pct} of the time. But bookies build in a margin (called the 'overround'), so the TRUE implied probability is closer to {example_true_pct}. That overround is how bookmakers guarantee a profit no matter who wins — same concept as a casino's house edge. This week, the biggest favourite is {biggest_fav} at {biggest_fav_odds}, implying a {biggest_fav_prob} chance of winning.",
      "fallback": "When a bookie offers $1.50 on a team, they're implying that team wins about 67% of the time. But bookies build in a margin (called the 'overround'), so the TRUE implied probability is closer to 64%. That overround is how bookmakers guarantee a profit no matter who wins — same concept as a casino's house edge."
    }
  ]
}
```

**Fields:**
- `id` (int): Unique identifier, 1-indexed, determines rotation order.
- `title` (str): Short topic name for reference.
- `category` (str): One of the categories from GENESIS.md teaching library.
- `template` (str): The teaching text with optional `{variable}` placeholders for that week's data.
- `fallback` (str): A version with no placeholders, used if the required data is unavailable.

### Template Variables Available

| Variable | Source | Description |
|----------|--------|-------------|
| `{example_odds}` | Largest favourite's raw odds | e.g., "$1.45" |
| `{example_raw_pct}` | 1/odds as % | e.g., "69%" |
| `{example_true_pct}` | Overround-removed probability | e.g., "66%" |
| `{biggest_fav}` | Team with highest consensus prob | e.g., "Panthers" |
| `{biggest_fav_odds}` | Best odds on the biggest favourite | e.g., "$1.35" |
| `{biggest_fav_prob}` | Consensus probability of biggest favourite | e.g., "72%" |
| `{closest_game_home}` | Home team of the tightest game | e.g., "Raiders" |
| `{closest_game_away}` | Away team of the tightest game | e.g., "Warriors" |
| `{closest_game_prob}` | Consensus prob of favourite in tightest game | e.g., "52%" |
| `{num_games}` | Number of games this round | e.g., "8" |
| `{round_number}` | Current round number | e.g., "1" |
| `{num_locks}` | Number of Lock-tier picks | e.g., "2" |
| `{num_coin_flips}` | Number of Coin Flip-tier picks | e.g., "3" |

---

## Pre-Written Teaching Snippets (First 10 Rounds)

The following 10 snippets ship with SLC. They cover the first 10 weeks of the season. Additional topics can be added to the JSON file at any time.

### Round 1: Implied Probability (Statistics & Probability)

> When a bookie offers {example_odds} on a team, they're implying that team wins about {example_raw_pct} of the time. But bookies build in a margin (called the 'overround'), so the TRUE implied probability is closer to {example_true_pct}. That gap between the raw number and the true number? That's the bookie's cut. This week, the biggest favourite is the {biggest_fav} at {biggest_fav_odds}.

### Round 2: Overround / Vig / Juice (Statistics & Probability)

> Here's a sneaky trick: add up the implied probabilities from any bookie and you'll get MORE than 100%. That extra bit is called the 'overround' (or 'vig' or 'juice' if you're American). It's how the bookie guarantees profit regardless of who wins. Ralph strips out the overround to get the TRUE implied probabilities — that's why his numbers always add to exactly 100%.

### Round 3: Wisdom of Crowds (Market Efficiency)

> Ever wonder why Ralph trusts the bookies? It's not because bookies are geniuses — it's because their odds reflect the bets of thousands of punters. This 'wisdom of crowds' effect means the market prices in team form, injuries, weather, and more. This round has {num_coin_flips} coin-flip game(s), which shows even the crowd can't always pick a winner.

### Round 4: Confidence Calibration (AI & Machine Learning)

> When Ralph says he's {biggest_fav_prob} confident in the {biggest_fav}, that should mean they win about {biggest_fav_prob} of the time in similar situations. This concept is called 'calibration' — it's how you judge whether a forecaster is honest. A perfectly calibrated tipper's 70% picks should win roughly 70% of the time over a full season. We'll track Ralph's calibration as the season goes on.

### Round 5: Expected Value (Statistics & Probability)

> Here's a concept that separates smart punters from mug punters: Expected Value (EV). If a team has a true 60% chance of winning but the odds imply only 55%, that's a positive EV bet — over time, you'd profit backing that team repeatedly. Ralph doesn't bet, but he uses this logic to spot where the market might be slightly off.

### Round 6: The Law of Large Numbers (Statistics & Probability)

> After {round_number} rounds, you might be tempted to judge Ralph on his record so far. But here's the thing: in statistics, small samples lie. The Law of Large Numbers says predictions only converge on their true accuracy over many, many trials. A 60% tipper could easily go 3/8 in a single round. Judge Ralph after Round 15, not Round 6.

### Round 7: Efficient Market Hypothesis (Market Efficiency)

> Ralph's entire philosophy rests on the Efficient Market Hypothesis (EMH): the idea that market prices already reflect all available information. In footy terms, the bookmaker odds have already factored in team form, injuries, weather, and everything else. Ralph's job isn't to outsmart the market — it's to READ the market well and explain what it's saying.

### Round 8: What an LLM Actually Is (AI & Machine Learning)

> Ralph is powered by a Large Language Model (LLM), but what IS that? Think of it as a system trained on billions of words that's learned the patterns of language incredibly well. It doesn't 'know' footy the way a coach does — it recognises patterns in how footy is discussed. That's why Ralph is better at explaining probabilities than at scouting players.

### Round 9: Regression to the Mean (Statistics & Probability)

> If a team starts the season winning every game, they probably won't keep it up forever. This is 'regression to the mean' — extreme results tend to pull back toward average over time. It doesn't mean good teams become bad; it means lucky streaks cool off. This week, watch for teams coming off big wins or big losses — the market often prices in regression that fans don't see.

### Round 10: Anchoring Bias (Behavioural / Decision Science)

> Here's a trap Ralph tries to avoid: anchoring. The first number you hear about a game — say, a mate says "Broncos by 20" — subconsciously shapes your expectations. You end up anchored to that number even when the evidence says otherwise. Ralph starts with the bookmaker odds precisely because they're the most information-rich anchor available.

---

## Topic Selection Logic

```python
def select_topic(round_number: int, total_topics: int) -> int:
    """Return the 0-based index of the topic for this round.

    Uses modular arithmetic so topics cycle after the library is exhausted.
    Round 1 gets topic index 0, Round 2 gets topic index 1, etc.
    After all topics are used, the cycle restarts.
    """
    return (round_number - 1) % total_topics
```

---

## Input Contract

- `round_number: int` — The current round number.
- `market_views: list[MarketView]` — The market data for this round (used to populate template variables).

---

## Output Contract

A `str` containing the teaching snippet for this round, with all template variables resolved. If a template variable cannot be resolved (e.g., no games have odds), the `fallback` text is used instead.

This string is stored on a new field: `RoundTips.teaching_moment: str`.

---

## Acceptance Criteria

1. **AC-01**: Given round 1, the teaching topic returned is "Implied Probability" (topic id 1).
2. **AC-02**: Given round 11 with 10 topics in the library, the teaching topic returned is "Implied Probability" (cycle restarts: (11-1) % 10 = 0).
3. **AC-03**: Template variables like `{biggest_fav}` are replaced with actual data from the round's market views.
4. **AC-04**: If a template variable references data that does not exist (e.g., no games in the round have odds), the fallback text is used.
5. **AC-05**: The `data/teaching_topics.json` file exists and contains at least 10 topics.
6. **AC-06**: Each teaching snippet, after variable resolution, is between 100 and 600 characters.
7. **AC-07**: The teaching snippet is accessible on the `RoundTips` object (new field or property).
8. **AC-08**: The teaching snippet does not contain any unresolved `{variable}` placeholders.
9. **AC-09**: The `data/teaching_topics.json` file validates: every topic has `id`, `title`, `category`, `template`, and `fallback` fields.

---

## Implementation Notes

### Files to Create

- `data/teaching_topics.json` — The pre-written teaching snippets (at least 10 topics, matching the content above).
- `ralph/teaching.py` — Teaching content logic:
  - `load_teaching_topics() -> list[dict]` — Load topics from JSON.
  - `select_topic(round_number: int, total_topics: int) -> int` — Return the topic index.
  - `build_teaching_context(market_views: list[MarketView]) -> dict` — Extract template variables from the round's market data.
  - `generate_teaching_snippet(round_number: int, market_views: list[MarketView]) -> str` — Main entry point: select topic, resolve variables, return text.
- `tests/test_teaching.py` — Unit tests covering all acceptance criteria.

### Files to Modify

- `ralph/models.py` — Add `teaching_moment: str = ""` field to `RoundTips` (this is a round-level field, not a per-tip field). Note: the existing `Tip` dataclass has a `teaching_moment` field per tip. For SLC, the teaching moment is per-round, not per-tip. Consider whether to keep the per-tip field (for future use) and add a per-round field, or repurpose the per-tip field. Recommendation: keep the per-tip field empty and add a `teaching_moment: str = ""` field to `RoundTips`.
- `ralph/output.py` — The teaching snippet is rendered once per tip sheet (see Spec 07).

### Design Decisions

- **JSON, not YAML.** The project already uses JSON for fixture/odds data. Consistency matters more than YAML's readability advantage.
- **Fallback text is mandatory.** Every topic must have a `fallback` field with no template variables. This is the safety net if data extraction fails.
- **10 topics for SLC.** The NRL season has 27 rounds. 10 topics covers the first 10 rounds and cycles. Adding more topics is trivially easy (just add entries to the JSON file). The goal is to ship with enough variety for the first third of the season.
- **Template resolution uses `str.format_map()` with a `defaultdict`.** Unknown keys return the fallback marker `"???"` which triggers the fallback text. This is safer than `.format(**kwargs)` which raises `KeyError` on missing keys.
