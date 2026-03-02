# Spec 02: See What the Market Says

**Activity:** See What the Market Says
**One-liner:** Understand who the bookmakers favour in each game and by how much.

---

## User Story

> As a workplace footy tipper, I want to see the bookmaker odds converted into real probabilities so that I understand how likely each team is to win according to the market.

---

## Scope

### IN (SLC v1)

- User manually adds head-to-head odds from 1-3 bookmakers into the round fixture file (same JSON file from Spec 01, extended with an `odds` array).
- Ralph converts decimal odds to raw implied probabilities.
- Ralph removes the bookmaker overround (vig/juice) to derive "true" implied probabilities.
- Ralph averages across multiple bookmaker sources to produce a consensus probability for each team.
- Each game gets a `consensus_home_prob` and `consensus_away_prob` that sum to 1.0.

### OUT (Deferred)

- Automated odds scraping from bookmaker websites or APIs.
- Monte Carlo confidence intervals from cross-bookmaker spread.
- Line movement detection (comparing odds at different times).
- Margin/spread odds, totals (over/under), or any market beyond head-to-head.
- Sharp vs square money analysis.

---

## Input Contract

### Extended Fixture JSON Schema

The `odds` array is added to each fixture object in the round file:

```json
{
  "round_number": 1,
  "season": 2025,
  "fixtures": [
    {
      "home_team": "Sydney Roosters",
      "away_team": "Brisbane Broncos",
      "venue": "Allianz Stadium",
      "kickoff": "2025-03-06T20:00",
      "odds": [
        {
          "source": "Sportsbet",
          "home_odds": 1.55,
          "away_odds": 2.50
        },
        {
          "source": "TAB",
          "home_odds": 1.52,
          "away_odds": 2.55
        }
      ]
    }
  ]
}
```

**Odds field requirements:**
- `odds` is a required array on each fixture (minimum 1 bookmaker, maximum 5).
- Each odds entry requires `source` (string), `home_odds` (float > 1.0), and `away_odds` (float > 1.0).
- Decimal (Australian) odds format only. No fractional or American odds.

---

## The Maths

### Step 1: Odds to Raw Implied Probability

```
implied_probability = 1 / decimal_odds
```

Example: Roosters at $1.55

```
implied_home = 1 / 1.55 = 0.6452 (64.52%)
implied_away = 1 / 2.50 = 0.4000 (40.00%)
sum = 1.0452 (the overround is 4.52%)
```

### Step 2: Remove Overround (Normalisation)

The sum of raw implied probabilities exceeds 1.0 because the bookmaker builds in a margin. To get "true" implied probabilities, normalise by dividing each by the sum:

```
true_home_prob = implied_home / (implied_home + implied_away)
true_away_prob = implied_away / (implied_home + implied_away)
```

Example:

```
true_home = 0.6452 / 1.0452 = 0.6173 (61.73%)
true_away = 0.4000 / 1.0452 = 0.3827 (38.27%)
sum = 1.0000 (exact)
```

This is called the **multiplicative method** of overround removal. It is the simplest and most common approach. More sophisticated methods (Shin, power, odds ratio) are deferred.

### Step 3: Consensus Averaging

When odds from multiple bookmakers are available, average the true implied probabilities:

```
consensus_home = mean(true_home_prob_source_1, true_home_prob_source_2, ...)
consensus_away = mean(true_away_prob_source_1, true_away_prob_source_2, ...)
```

Then re-normalise to ensure the consensus sums to exactly 1.0:

```
total = consensus_home + consensus_away
consensus_home = consensus_home / total
consensus_away = consensus_away / total
```

The re-normalisation step handles floating-point drift. In practice the deviation is negligible, but the output must always sum to 1.0.

---

## Output Contract

For each game, the market engine produces a `MarketView` (new dataclass to be added to `ralph/models.py`):

```python
@dataclass
class MarketView:
    """Market consensus probabilities for a single game."""
    game: Game
    odds_sources: list[Odds]
    consensus_home_prob: float  # True implied probability, 0.0-1.0
    consensus_away_prob: float  # True implied probability, 0.0-1.0

    @property
    def favourite(self) -> str:
        """The team the market favours."""
        if self.consensus_home_prob >= self.consensus_away_prob:
            return self.game.home_team
        return self.game.away_team

    @property
    def favourite_prob(self) -> float:
        """Probability assigned to the favourite."""
        return max(self.consensus_home_prob, self.consensus_away_prob)
```

---

## Acceptance Criteria

1. **AC-01**: Given home odds of $1.55, `odds_to_implied_probability(1.55)` returns `0.6452` (to 4 decimal places).
2. **AC-02**: Given raw implied probs of 0.6452 and 0.4000, `remove_overround(0.6452, 0.4000)` returns `(0.6173, 0.3827)` (to 4 decimal places).
3. **AC-03**: The output of `remove_overround` always sums to exactly 1.0 (within floating-point tolerance of 1e-9).
4. **AC-04**: Given odds from two bookmakers (Sportsbet: $1.55/$2.50, TAB: $1.52/$2.55), `market_consensus()` returns the mean of each source's true implied probabilities, re-normalised to sum to 1.0.
5. **AC-05**: Given odds from a single bookmaker, `market_consensus()` returns that bookmaker's overround-removed probabilities (no averaging needed).
6. **AC-06**: Given `home_odds <= 1.0`, the system raises a `ValueError` (odds below 1.0 are impossible in decimal format).
7. **AC-07**: Given `away_odds <= 1.0`, the system raises a `ValueError`.
8. **AC-08**: The `odds` field is required in the fixture file. A fixture missing the `odds` array raises a `ValueError` with a clear message.
9. **AC-09**: Each odds entry must have `source`, `home_odds`, and `away_odds`. Missing fields raise a `ValueError` identifying the game and missing field.
10. **AC-10**: The `MarketView` dataclass is added to `ralph/models.py` and correctly computes `favourite` and `favourite_prob`.

---

## Implementation Notes

### Files to Modify

- `ralph/market.py` — Replace the three stub functions with working implementations:
  - `odds_to_implied_probability(odds: float) -> float`
  - `remove_overround(home_implied: float, away_implied: float) -> tuple[float, float]`
  - `market_consensus(odds_list: list[Odds]) -> tuple[float, float]`
- `ralph/models.py` — Add the `MarketView` dataclass.
- `ralph/fixtures.py` (created in Spec 01) — Extend `load_fixtures()` to also parse and validate the `odds` array from each fixture, returning `Odds` instances alongside `Game` instances. The function signature should become `load_round(round_number: int) -> list[tuple[Game, list[Odds]]]` or alternatively return a list of `MarketView` objects directly.

### Files to Create

- `tests/test_market.py` — Unit tests covering all acceptance criteria.

### Design Decisions

- **Multiplicative overround removal only.** Shin's method and other approaches are academically interesting but add complexity without meaningful accuracy improvement for a tipping comp. Deferred.
- **Consensus is a simple arithmetic mean.** No weighting by bookmaker "sharpness" or reputation. All sources are treated equally.
- **Re-normalisation after averaging.** Even though the theoretical deviation is tiny, always re-normalise. This provides a guarantee that downstream consumers (tips, output) can rely on probs summing to 1.0.
- **Decimal odds only.** Australian bookmakers quote in decimal. No need to support fractional (UK) or American (US) formats.
