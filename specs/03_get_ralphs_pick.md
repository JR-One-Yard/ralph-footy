# Spec 03: Get Ralph's Pick

**Activity:** Get Ralph's Pick
**One-liner:** Receive a clear tip for each game with a confidence level.

---

## User Story

> As a workplace footy tipper, I want Ralph to tell me which team to pick for each game and how confident he is, so that I can submit my tips with a sense of how strong each pick is.

---

## Scope

### IN (SLC v1)

- For each game, Ralph picks the team with the higher consensus implied probability.
- Each pick is assigned a confidence tier: **Lock**, **Lean**, or **Coin Flip**.
- The confidence tiers are based on the favourite's consensus probability.
- The system is purely deterministic: same input odds always produce the same picks.
- Picks are assembled into a `RoundTips` object for downstream consumption.

### OUT (Deferred)

- LLM sentiment adjustments that could override the market pick.
- Monte Carlo confidence intervals.
- Margin/spread predictions.
- Any pick that disagrees with the market consensus (Ralph always picks the favourite in SLC).
- "Ralph's edge" explanations when deviating from market.

---

## Confidence Tier Definitions

| Tier | Favourite Probability | Ralph's Language | Meaning |
|------|-----------------------|------------------|---------|
| **Lock** | >= 70% | "Ralph is backing [team] hard." | Market has a clear favourite. Ralph is confident. |
| **Lean** | 55% to 69.99% | "Ralph leans [team]." | Market favours one team but it is not a blowout. |
| **Coin Flip** | < 55% | "This one could go either way." | Market sees a tight contest. Ralph picks the slight favourite but flags the uncertainty. |

**Important:** The thresholds are on the favourite's consensus probability (the `consensus_home_prob` or `consensus_away_prob`, whichever is larger), NOT on the gap between teams.

### Threshold Rationale

- **70% Lock threshold:** At $1.43 or shorter, the market is saying this team wins 7 out of 10 times. That is a strong signal.
- **55% Lean threshold:** At roughly $1.82 or shorter, there is a clear favourite. Below 55% (around $1.82+), the market is saying it is nearly even.
- **These thresholds are intentionally rounded and simple.** They match GENESIS.md's spirit of explainability. Fine-tuning comes in later iterations with calibration data.

### Note on GENESIS.md vs STORY_MAP.md Threshold Discrepancy

GENESIS.md mentions `>65% = Lock, 55-65% = Lean, <55% = Coin Flip`. STORY_MAP.md says `>65% = Lock`. The existing `models.py` uses `>=75% Lock, >=60% Lean`. For SLC, we standardise on `>=70% Lock, >=55% Lean` as a middle ground. This can be tuned in later iterations once calibration data is available. Update `models.py` to match these thresholds.

---

## Input Contract

A list of `MarketView` objects (from Spec 02), one per game. Each `MarketView` contains:
- `game: Game`
- `odds_sources: list[Odds]`
- `consensus_home_prob: float`
- `consensus_away_prob: float`

---

## Output Contract

A `RoundTips` object containing a list of `Tip` objects:

```python
RoundTips(
    round_number=1,
    season=2025,
    tips=[
        Tip(
            game=game,
            pick="Sydney Roosters",       # The team name Ralph picks
            confidence=0.6173,            # The consensus probability of the picked team
            rationale="",                 # Empty string — filled by Spec 04
            teaching_moment="",           # Empty string — filled by Spec 05
        ),
        ...
    ],
)
```

The `confidence_label` property on `Tip` must return the correct tier string based on the updated thresholds.

---

## Acceptance Criteria

1. **AC-01**: Given a `MarketView` where `consensus_home_prob = 0.72` and `consensus_away_prob = 0.28`, Ralph picks the home team.
2. **AC-02**: Given a `MarketView` where `consensus_home_prob = 0.45` and `consensus_away_prob = 0.55`, Ralph picks the away team.
3. **AC-03**: Given `consensus_home_prob = 0.50` and `consensus_away_prob = 0.50` (exact coin flip), Ralph picks the home team (tie-breaking rule: home team advantage).
4. **AC-04**: A pick with `confidence = 0.72` has `confidence_label == "Lock"`.
5. **AC-05**: A pick with `confidence = 0.70` has `confidence_label == "Lock"` (boundary is inclusive).
6. **AC-06**: A pick with `confidence = 0.63` has `confidence_label == "Lean"`.
7. **AC-07**: A pick with `confidence = 0.55` has `confidence_label == "Lean"` (boundary is inclusive).
8. **AC-08**: A pick with `confidence = 0.54` has `confidence_label == "Coin Flip"`.
9. **AC-09**: A pick with `confidence = 0.50` has `confidence_label == "Coin Flip"`.
10. **AC-10**: Given a round with 8 `MarketView` objects, `generate_round_tips()` returns a `RoundTips` with exactly 8 `Tip` objects.
11. **AC-11**: The `rationale` and `teaching_moment` fields on each `Tip` are empty strings (to be populated by later specs).
12. **AC-12**: The `RoundTips.generated_at` field is populated with the current datetime.

---

## Implementation Notes

### Files to Modify

- `ralph/tips.py` — Replace the two stub functions:
  - `generate_tip(game: Game, market_view: MarketView) -> Tip` — Generate a single tip from a market view. Update the signature to accept `MarketView`.
  - `generate_round_tips(market_views: list[MarketView], round_number: int, season: int) -> RoundTips` — Generate tips for a full round. Update the signature to accept `list[MarketView]`.
- `ralph/models.py` — Update the `Tip.confidence_label` property to use the new thresholds:
  - `>= 0.70` returns `"Lock"`
  - `>= 0.55` returns `"Lean"`
  - `< 0.55` returns `"Coin Flip"`

### Files to Create

- `tests/test_tips.py` — Unit tests covering all acceptance criteria.

### Design Decisions

- **Home team tie-break.** In the (rare) case of exactly 50/50 consensus, pick the home team. Home advantage is real in NRL and this is the simplest defensible rule.
- **No randomness.** The pick is deterministic. Same odds in, same tip out. This makes testing straightforward and builds user trust.
- **Confidence = favourite's probability.** The `confidence` field on `Tip` stores the consensus probability of the picked team. This is the simplest mapping and directly communicates "how confident is the market?"
- **Rationale and teaching are empty at this stage.** Tip generation is separated from rationale/teaching generation. The `Tip` object is created with placeholder empty strings, then enriched by Specs 04 and 05. This keeps the tip generation logic pure and testable.
