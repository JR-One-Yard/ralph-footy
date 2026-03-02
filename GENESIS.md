# GENESIS PROMPT — "Ralph" the Footy Forecaster

## Mission

Build **Ralph** — an NRL Footy Forecaster that enters a workplace tipping competition and, more importantly, uses footy as a Trojan horse to teach non-technical colleagues about AI, machine learning, statistics, probability, and betting markets.

There is **no money at stake**. The downside of getting picks wrong is zero. The upside of getting people curious about how the tool thinks is enormous. Ralph's job is to **tip well AND teach well**.

---

## Core Philosophy

> "Markets are efficient. We're not trying to outsmart the bookies — we're trying to explain how the bookies think, and then show what an LLM can layer on top."

Ralph embraces the **Efficient Market Hypothesis** as its foundation. Betting odds from established markets already encode an enormous amount of information — team form, injuries, weather, venue, historical matchups, and the collective wisdom of thousands of punters. Ralph's baseline is simply to read the market well.

The LLM layer (news search, sentiment analysis, narrative reasoning) exists to:
1. Demonstrate what AI can do beyond number-crunching
2. Occasionally catch edges the market might be slow to price (e.g., a key player ruled out after odds were set)
3. Generate the **teaching content** that makes this project worthwhile

---

## Quant Desk Influence

Ralph draws selectively from institutional quant techniques — Monte Carlo simulation, Bayesian updating, calibration scoring, agent-based market intuition — but always through the lens of simplicity and teaching. The goal is never to replicate a hedge fund's infrastructure. It's to borrow the *ideas* that make those systems powerful and translate them into plain-English footy insights.

The motto: **"Don't build a quant desk. Build a footy tipping mate who learned a few things from a quant desk."**

For the full institutional-grade methodology that Ralph simplifies, see the companion reference document: `Quant_Desk_Simulation.md`.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   RALPH PIPELINE                     │
│                                                      │
│  1. FIXTURE FETCH                                    │
│     └─ Get this week's NRL round & matchups          │
│                                                      │
│  2. MARKET CONSENSUS (Primary Signal)                │
│     ├─ Source 1: Sportsbet / TAB                     │
│     ├─ Source 2: Ladbrokes / Neds                    │
│     └─ Source 3: Pointsbet / bet365                  │
│     └─ → Derive implied probabilities from H2H odds  │
│     └─ → Average across sources = Market Consensus %  │
│     └─ → Monte Carlo confidence intervals             │
│          (bootstrap from cross-bookmaker spread)      │
│                                                      │
│  3. LLM SENTIMENT LAYER (Secondary Signal)           │
│     ├─ News search (injuries, suspensions, weather)  │
│     ├─ Recent form narrative analysis                │
│     └─ "Gut feel" reasoning from LLM                 │
│     └─ → Small adjustment (+/- 1-5%) to consensus    │
│     └─ → Lightweight Bayesian updating               │
│          (prior = market, signal = news,              │
│           posterior = adjusted probability)            │
│                                                      │
│  4. TIP GENERATION                                   │
│     ├─ Final pick for each game                      │
│     ├─ Confidence level (Lock / Lean / Coin Flip)    │
│     └─ Margin prediction (optional stretch goal)     │
│                                                      │
│  5. RATIONALE & TEACHING OUTPUT                      │
│     ├─ WHY Ralph picked each team (2-3 sentences)    │
│     ├─ WHAT the market is saying (odds breakdown)    │
│     └─ LEARN: A "Did You Know?" teaching moment      │
│        about probability, markets, ML, or LLMs       │
│        (expanded library drawing from quant concepts) │
└─────────────────────────────────────────────────────┘
```

---

## Output Format (Per Game)

Each game Ralph tips should produce output like this:

```
🏉 GAME 3: Penrith Panthers vs Sydney Roosters
📍 BlueBet Stadium | Friday 7:55pm

🎯 RALPH'S TIP: Panthers (68% confidence)
💰 MARKET SAYS: Panthers $1.45 | Roosters $2.75
   → Implied: Panthers 66.2% | Roosters 33.8% (after margin removal)

📝 RATIONALE:
Markets have Penrith as clear favourites at home, and Ralph agrees.
The Panthers are 4-1 this season with dominant forward stats.
However, the Roosters' halves have been in career-best form — this
one might be closer than the odds suggest.

🎓 DID YOU KNOW?
"When a bookie offers $1.45 on a team, they're implying that team
wins about 69% of the time. But bookies build in a margin (their
profit), so the TRUE implied probability is closer to 66%. This
'overround' is how bookmakers guarantee profit regardless of the
outcome. It's the same concept as a casino's house edge."
```

---

## Teaching Topics Library

Ralph should rotate through these concepts across the season, one per round:

### Statistics & Probability
- Implied probability (converting odds to %)
- Overround / vig / juice (the bookie's margin)
- Expected value (EV) — why +EV bets matter long-term
- Regression to the mean — why hot streaks cool off
- Base rates vs recency bias
- The law of large numbers
- Bayes' theorem in plain English (updating beliefs with new info)
- Simpson's paradox (why stats can mislead)

### Market Efficiency
- Efficient Market Hypothesis — what it means for sports betting
- Wisdom of crowds — why the market is hard to beat
- Line movement — what it means when odds shift
- Sharp vs square money — who moves the line
- Closing line value — the gold standard of betting skill

### AI & Machine Learning
- What an LLM actually is (and isn't)
- How sentiment analysis works
- Training data vs inference — what the model "knows"
- Confidence calibration — when AI says 70%, is it right 70% of the time?
- The difference between prediction and explanation
- Feature engineering — what inputs matter for sports prediction
- Overfitting — why more data isn't always better
- Ensemble methods — why combining models beats any single model

### Quantitative Methods (from the Quant Desk)
- Monte Carlo simulation — running 10,000 imaginary seasons to estimate probability
- Brier Score — the gold standard for measuring forecast calibration
- Central Limit Theorem — why you need a whole season to judge a tipper
- Importance sampling — how quants price extremely rare events
- Particle filtering — updating beliefs in real-time as new information arrives
- Tail dependence — when extreme outcomes move together (and when they don't)
- Zero-intelligence markets — why markets are accurate even when individual bettors aren't
- Bayesian updating in practice — starting with odds and adjusting for late team news

### Behavioural / Decision Science
- Confirmation bias in tipping
- Anchoring — why the first number you see matters
- The hot hand fallacy
- Sunk cost and chasing losses
- Dunning-Kruger in footy tipping

---

## Ralph Loop — Iterative Build Plan

### Iteration 0: Foundation
- [x] Genesis prompt (this document)
- [ ] Project scaffold (Python or Node — TBD)
- [ ] Basic CLI that prints "Ralph is thinking..."
- [ ] README with project vision

### Iteration 1: Market Consensus Engine
- [ ] Scrape or API-fetch odds from 2-3 bookmakers
- [ ] Convert odds to implied probabilities
- [ ] Remove overround to get "true" implied probabilities
- [ ] Average across sources for consensus view
- [ ] Output: ranked tips by confidence
- [ ] Add Monte Carlo confidence intervals (bootstrap from cross-bookmaker spread)

### Iteration 2: Fixture & Schedule
- [ ] Fetch current NRL round and fixtures
- [ ] Match fixture data to odds data
- [ ] Handle byes, postponements, etc.
- [ ] Output: structured round data

### Iteration 3: LLM Sentiment Layer
- [ ] Web search for team news (injuries, suspensions)
- [ ] Summarise recent form per team
- [ ] Generate a small probability adjustment (+/- 1-5%)
- [ ] Output: adjusted probabilities with reasoning
- [ ] Frame LLM adjustment as lightweight Bayesian update (prior → signal → posterior)

### Iteration 4: Output & Teaching
- [ ] Format output per the template above
- [ ] Implement teaching topic rotation
- [ ] Generate "Did You Know?" segments via LLM
- [ ] Output: complete weekly tipping report
- [ ] Include Quant Desk teaching topics in rotation library

### Iteration 5: Tracking & Calibration
- [ ] Record Ralph's tips vs actual results
- [ ] Track accuracy over time
- [ ] Calibration analysis (are 70% picks winning 70%?)
- [ ] Sharpe ratio / ROI if we were hypothetically betting
- [ ] Publish a mid-season "How's Ralph Going?" report
- [ ] Implement Brier Score as primary calibration metric (target: < 0.20)
- [ ] Benchmark against Quant Desk calibration standards (FiveThirtyEight: 0.06-0.12)

### Iteration 6: Polish & Share
- [ ] Simple web UI or Slack bot for the office
- [ ] Weekly email/post format
- [ ] Season summary and lessons learned

---

## Technical Decisions (To Resolve in Iteration 0)

| Decision | Options | Leaning |
|---|---|---|
| Language | Python / TypeScript | Python (data libs) |
| Odds source | Web scraping / API / Manual input | Start manual, automate later |
| LLM | Claude API / Local model | Claude API |
| Output | CLI / Web / Slack / Email | CLI first, then Slack |
| Data store | JSON files / SQLite / Postgres | JSON files to start |
| Deployment | Local / Cloud / GitHub Actions | Local first |

---

## Key Principles for Ralph

1. **Humility first.** Ralph should never claim to "know" who will win. It estimates probabilities and explains its reasoning. Language matters: "Ralph leans towards..." not "Ralph guarantees..."

2. **Teaching > Tipping.** If Ralph gets 60% of tips right but teaches the office about implied probability, that's a massive win. The tips are the hook; the education is the payload.

3. **Simplicity > Sophistication.** A simple model that people understand beats a complex model that's a black box. Every decision Ralph makes should be explainable to someone with zero technical background.

4. **Transparent uncertainty.** Ralph should be honest about what it doesn't know. "This is basically a coin flip" is a valid and useful output.

5. **Market respect.** The default position is that the market is right. Ralph needs a good reason to deviate, and should explain that reason clearly.

6. **Fun.** This is footy tipping. Ralph should have personality. A bit cheeky, a bit nerdy, very Australian. Think: the stats-loving mate at the pub who explains things without being condescending.

---

## NRL 2025 Season Context

- **Season start:** Round 1 kicks off March 6, 2025
- **Teams:** 17 teams (The Dolphins are the newest, entering their 3rd season)
- **Rounds:** 27 rounds + finals
- **Games per round:** 8 games (one team has a bye each week due to odd number of teams)

---

## What Success Looks Like

| Metric | Target |
|---|---|
| Tip accuracy | >55% (beat a coin flip meaningfully) |
| Beat the office average | Top quartile of the tipping comp |
| Teaching engagement | At least 3 colleagues ask "how does Ralph work?" |
| Calibration | 70% confidence picks win between 60-80% of the time |
| Fun factor | People look forward to Ralph's weekly output |

---

## Companion Documents

- `Quant_Desk_Simulation.md` — Institutional-grade simulation methodology. Ralph draws selectively from Parts II (Monte Carlo, Brier Score), IV (Bayesian updating concept), and VII (agent-based market intuition). The full document serves as a deep-dive reference for anyone who wants to understand the quantitative foundations Ralph simplifies.

---

## Next Step

**Iteration 0 is complete with this Genesis prompt.**

The next Ralph Loop iteration should:
1. Scaffold the project (language, structure, dependencies)
2. Build a basic CLI entry point
3. Create a README for the repo
4. Decide on odds data sources (user to provide bookmaker links)

Invoke the next iteration with:
> "Ralph, let's start Iteration 1. Here are the bookmaker links: [...]"

---

*Ralph v0.2 — Genesis + Quant Desk Integration — March 2025*
*"I don't know everything about footy, but I learned a few things from the quant desk."*
