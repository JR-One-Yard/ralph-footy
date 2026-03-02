# Ralph Story Map — Phases 1-3

*Generated 2 March 2026 | Ralph Methodology: JTBD, Story Map, SLC Slice*

---

## Phase 1: JTBD & Activities

### The Job to Be Done

> "When I want to enter my workplace footy tipping comp each week, help me make **informed picks** I can submit with confidence, AND **teach me something interesting** about probability, AI, or markets along the way — so that even when I lose, I learned something worth talking about at the office."

The JTBD has two halves, and both matter equally:

1. **Functional job**: Produce a complete set of weekly NRL tips that are better than guessing.
2. **Emotional/social job**: Give me something interesting to share with colleagues — make me the person at work who says "did you know how bookmaker odds actually work?"

Ralph fails if it only does one of these. A raw probability engine with no personality is a spreadsheet. A chatty personality with bad tips is a novelty that dies after Round 3.

---

### Activities (The Backbone)

The pipeline stages from GENESIS.md (Fixture Fetch, Market Consensus, LLM Sentiment, Tip Generation, Rationale & Teaching) are **technical components**. Users do not think in those terms. Here are those stages reframed as Activities — verbs in a user journey, each describing what the user experiences or does.

| # | Activity | One-Sentence Description | "And" Test |
|---|----------|--------------------------|------------|
| 1 | **Check This Week's Fixtures** | See which NRL teams are playing, where, and when this round. | Pass — single concern: what games are on. |
| 2 | **See What the Market Says** | Understand who the bookmakers favour in each game and by how much. | Pass — single concern: market-implied probabilities. |
| 3 | **Hear What the News Says** | Find out if injuries, suspensions, weather, or form changes anything the market might not have priced in yet. | Pass — single concern: late-breaking context. |
| 4 | **Get Ralph's Pick** | Receive a clear tip for each game with a confidence level (Lock / Lean / Coin Flip). | Pass — single concern: the recommendation. |
| 5 | **Understand Why** | Read a short, plain-English rationale for each pick — what drove the decision. | Pass — single concern: the reasoning behind each tip. |
| 6 | **Learn Something New** | Get one teaching moment per round that explains a concept from probability, markets, AI, or behavioural science — using that week's games as the example. | Pass — single concern: education. |
| 7 | **Track How Ralph Is Going** | See Ralph's season accuracy, calibration, and whether the confidence levels are honest. | Pass — single concern: performance over time. |
| 8 | **Share the Tip Sheet** | Get the full weekly output in a format ready to share with colleagues (Slack, email, printed). | Pass — single concern: distribution. |

**Why eight activities instead of five pipeline stages:**

- "Check This Week's Fixtures" was implicit in the pipeline but is the user's actual starting point.
- "Understand Why" and "Learn Something New" were combined in the pipeline as "Rationale & Teaching Output" but they serve different jobs. Rationale is about *this specific pick*. Teaching is about a *transferable concept*. They deserve separate rows because a user might want one without the other, and the depth axis (Basic vs Advanced vs AI-Powered) scales differently for each.
- "Track How Ralph Is Going" and "Share the Tip Sheet" were Iterations 5-6 in the build plan but are real user activities, not just technical milestones.

---

## Phase 2: User Story Map (The Graph)

The X-axis is the sequence of Activities from Phase 1. The Y-axis is depth — three tiers from bare minimum to full AI integration.

Read the table left-to-right as the weekly user journey, and top-to-bottom as increasing sophistication within each activity.

### The Map

| Depth | 1. Check This Week's Fixtures | 2. See What the Market Says | 3. Hear What the News Says | 4. Get Ralph's Pick | 5. Understand Why | 6. Learn Something New | 7. Track How Ralph Is Going | 8. Share the Tip Sheet |
|-------|-------------------------------|----------------------------|---------------------------|---------------------|-------------------|----------------------|---------------------------|----------------------|
| **Basic** | Manually type in the 8 matchups for the round (teams, venue, kickoff time) from the NRL website. Store as a simple JSON/YAML fixture file. | Manually input head-to-head odds from 1-2 bookmakers. Convert to implied probabilities. Remove overround. Output a ranked list by market confidence. | Skip entirely. Market odds are the only signal. | Pick the team with the higher implied probability in each game. Assign confidence tiers based on probability gap: >65% = Lock, 55-65% = Lean, <55% = Coin Flip. | Write a 1-2 sentence template-driven rationale per game. E.g., "Market has [Team] at [X]% implied. Ralph leans [Team]." | Manually curate one teaching paragraph per round from the topic library in GENESIS.md, tailored to that week's results. | Record tips vs results in a JSON file. Calculate running accuracy % after each round. | CLI output to terminal. Copy-paste into Slack/email. |
| **Advanced** | Scrape or API-fetch fixtures from NRL.com or a data provider. Auto-detect the current round. Handle byes and schedule changes. | Scrape odds from 2-3 bookmakers automatically. Average across sources for a consensus view. Bootstrap Monte Carlo confidence intervals from cross-bookmaker spread. Detect significant line movement between scrapes. | Automated web search for team news (injuries, suspensions, weather). Structured extraction of key facts. Present news summary alongside odds — but no probability adjustment yet. | Same probability-based picks, but with Monte Carlo confidence intervals reported alongside the point estimate. Add margin prediction (optional). | Richer rationale that references specific stats: recent form (W/L streak), head-to-head record, home/away splits. Still template-driven but with more data points. | Auto-select the teaching topic based on what is most relevant to this week's games (e.g., if a huge upset happened last round, teach regression to the mean). | Brier Score as primary calibration metric. Calibration curve (are 70% picks winning ~70% of the time?). Comparison to a "just pick the favourite" baseline. Weekly accuracy trend chart. | Formatted Markdown report. Slack bot or email integration. Includes a simple leaderboard if multiple humans are tracked. |
| **AI-Powered** | LLM parses fixture announcements and social media for late changes (moved games, COVID/weather postponements). Auto-updates fixture file. | LLM monitors odds movement and explains *why* lines are moving ("Sharp money on Roosters after Tedesco confirmed fit"). Synthesises a narrative market summary per round. | LLM sentiment analysis: scan news, podcasts, social media for signals the market may be slow to price. Generate a small Bayesian probability adjustment (+/- 1-5%) with explicit prior/posterior framing. Particle-filter-style updating as new info arrives during the week. | LLM generates picks that can *disagree* with the market when the sentiment layer provides sufficient evidence. Picks include a "Ralph's edge" explanation when deviating from market consensus. | LLM writes bespoke, personality-driven rationale in Ralph's voice — cheeky, Australian, stat-literate. References narratives, not just numbers. Explains the Bayesian update in plain English. | LLM generates original teaching content each round, using that week's actual games as worked examples. Can adapt complexity to the audience. Draws from the full topic library including quant desk concepts (Monte Carlo, Brier Score, tail dependence, zero-intelligence markets). | LLM generates a mid-season "How's Ralph Going?" narrative report. Analyses *where* Ralph is wrong (e.g., underestimates underdogs). Suggests model improvements. Benchmark against FiveThirtyEight-style calibration standards (Brier < 0.20 target). | LLM formats output with Ralph's personality. Generates a "round preview" narrative. Adapts tone to the audience. Web UI with interactive elements. |

---

## Phase 3: The SLC Slice

### Drawing the Line

The SLC slice cuts horizontally across the story map. Everything **above** the line ships in the first release. Everything below is deferred.

```
                    THE SLC LINE
                    ============

  Activity 1    Activity 2    Activity 3    Activity 4    Activity 5    Activity 6    Activity 7    Activity 8
  Fixtures      Market        News          Pick          Why           Learn         Track         Share
  ─────────     ─────────     ─────────     ─────────     ─────────     ─────────     ─────────     ─────────
  [BASIC]       [BASIC]       [skip]        [BASIC]       [BASIC+]      [BASIC+]      [BASIC]       [BASIC]
  ═══════════════════════════════════════════ SLC LINE ═════════════════════════════════════════════════════════
  [ADVANCED]    [ADVANCED]    [ADVANCED]    [ADVANCED]    [ADVANCED]    [ADVANCED]    [ADVANCED]    [ADVANCED]
  [AI-POWERED]  [AI-POWERED]  [AI-POWERED]  [AI-POWERED]  [AI-POWERED]  [AI-POWERED]  [AI-POWERED]  [AI-POWERED]
```

### What Is IN the SLC Slice

| Activity | SLC Scope | Detail |
|----------|-----------|--------|
| **1. Check This Week's Fixtures** | **Basic** | User manually enters the 8 matchups into a JSON/YAML file. No scraping, no API. The NRL website takes 2 minutes to check — automating it is not worth the complexity for V1. |
| **2. See What the Market Says** | **Basic** | User manually inputs H2H odds from 1-2 bookmakers. Ralph converts to implied probabilities, removes overround, and ranks games by confidence. This is the mathematical backbone — it must work perfectly even if the input is manual. |
| **3. Hear What the News Says** | **Skipped** | No news layer in V1. The market odds already encode most news. Adding a manual or automated news step adds complexity without proportional value for the first release. The teaching content can still reference why markets already include this information. |
| **4. Get Ralph's Pick** | **Basic** | Pick the team with the higher implied probability. Assign confidence tiers (Lock / Lean / Coin Flip) based on the probability gap. Simple, deterministic, explainable. No Monte Carlo, no margin predictions yet. |
| **5. Understand Why** | **Basic+** | Each pick gets a 2-3 sentence rationale. Template-driven but with enough personality to sound like Ralph, not a spreadsheet. References the odds, the implied probability, and the confidence tier. The "+" means we write templates with Ralph's voice baked in — not generic "Team A has higher probability." |
| **6. Learn Something New** | **Basic+** | One teaching paragraph per round, manually selected from the topic library. The "+" means the teaching content connects to that specific round's games — not a generic explainer pasted in. E.g., if the round has a heavy favourite at $1.15, teach overround. If there is a genuine coin flip, teach implied probability. |
| **7. Track How Ralph Is Going** | **Basic** | Record tips and results in a JSON file. Calculate cumulative accuracy after each round. No Brier Score, no calibration curves — just "Ralph is 14/24 (58%) after Round 3." This is essential for completeness: if you cannot see how Ralph is tracking, the project has no feedback loop. |
| **8. Share the Tip Sheet** | **Basic** | CLI output formatted per the template in GENESIS.md (with the emoji headers, the odds breakdown, the rationale, the teaching moment). Designed to be copy-pasted into Slack or email. No Slack bot, no web UI, no automation — but the output must look good when pasted. |

### What Is OUT of the SLC Slice (Deferred)

| Deferred Item | Why It Is Deferred |
|---------------|-------------------|
| Automated fixture scraping (Activity 1, Advanced) | Adds dependency on external APIs/scraping that can break. Manual entry for 8 games takes 2 minutes. |
| Automated odds scraping (Activity 2, Advanced) | Same rationale. Bookmaker websites change frequently. Manual entry for 8 games from one bookmaker takes 5 minutes. |
| Monte Carlo confidence intervals (Activity 2, Advanced) | Requires multiple bookmaker sources to bootstrap from. Valuable but not essential when the user can eyeball the cross-bookmaker spread manually. |
| News/sentiment layer (Activity 3, all tiers) | Entire activity deferred. The market signal alone is a strong V1 baseline. News adds the most value in AI-Powered tier, which is furthest from V1. |
| LLM-generated rationale (Activity 5, AI-Powered) | Templates with Ralph's voice are sufficient for V1. LLM integration is the single biggest complexity increase and should be a dedicated iteration. |
| LLM-generated teaching content (Activity 6, AI-Powered) | Manually curated content from the topic library is high quality and controllable. LLM generation risks hallucination in educational content — not acceptable for a teaching tool. |
| Brier Score and calibration analysis (Activity 7, Advanced) | Requires enough rounds of data to be meaningful. Ship basic tracking now; add Brier Score after Round 6+ when there is enough data. |
| Slack bot / web UI / email automation (Activity 8, Advanced+) | Distribution polish. The CLI output copy-pasted into Slack *is* the V1 distribution channel. |
| Bayesian probability adjustment (Activity 3-4, AI-Powered) | The crown jewel of the full system, but requires the news/sentiment layer to exist first. Deferred until the pipeline has data to update on. |
| Line movement detection (Activity 2, Advanced) | Requires multiple scrapes over time. Interesting for teaching but not essential for weekly tips. |
| Margin predictions (Activity 4, Advanced) | Nice-to-have. The tipping comp only cares about winner, not margin. |
| Season narrative reports (Activity 7, AI-Powered) | Requires both accumulated data and LLM integration. A Round 12+ feature. |

---

### SLC Evaluation

#### Simple?

**Yes.** The SLC slice requires:
- A CLI script (Python) that reads a manually-created JSON fixture+odds file.
- Pure arithmetic: odds-to-probability conversion, overround removal, ranking.
- Template-based text output.
- A JSON file for result tracking.

No APIs, no scraping, no LLM calls, no web UI, no database. A competent developer can ship this in 2-3 days. The hardest part is writing good templates with Ralph's personality — that is a writing task, not an engineering task.

#### Complete?

**Yes.** The SLC produces a full weekly tip sheet that:
- Covers all 8 games in the round.
- Shows the odds, implied probabilities, and Ralph's pick for each game.
- Includes a confidence tier (Lock / Lean / Coin Flip) for each pick.
- Explains *why* in 2-3 sentences per game.
- Teaches one concept per round.
- Tracks accuracy over the season.
- Outputs in a format ready to share.

This is end-to-end. A user can run Ralph on Monday, get a tip sheet, paste it into the office Slack, submit their tips, then record results after the round. The loop is closed.

#### Lovable?

**Yes, with one condition:** the templates must be written with genuine care. The difference between "lovable" and "meh" at this tier is entirely in the writing:

- **Not lovable**: "Panthers have 66.2% implied probability. Ralph picks Panthers."
- **Lovable**: "Ralph leans Panthers here — the market has them at 66% which feels about right for Penrith at home on a Friday night. The Roosters are capable of making this ugly, but you'd want better odds to back them."

The teaching content must also be specific to the week, not a generic paragraph. If Game 3 has odds of $1.45 vs $2.75, the teaching moment should use *those exact numbers* to explain implied probability. This is what makes it lovable — it is not a textbook, it is Ralph talking about *this week's footy*.

The CLI output format from GENESIS.md (with the emoji section headers) is already well-designed for Slack sharing. That template *is* the UX.

---

### SLC Slice Summary

```
SHIP NOW (SLC v1)                          SHIP LATER
========================                   ========================
Manual fixture input (JSON)                Automated fixture scraping
Manual odds input (1-2 bookies)            Multi-bookmaker odds scraping
Implied probability math                   Monte Carlo confidence intervals
Simple pick = highest probability          News/sentiment-adjusted picks
Template rationale (Ralph's voice)         LLM-generated rationale
Curated teaching (from topic library)      LLM-generated teaching content
JSON result tracking + accuracy %          Brier Score + calibration curves
CLI output (copy-paste to Slack)           Slack bot / web UI / email
                                           Bayesian probability updates
                                           Margin predictions
                                           Season narrative reports
```

### The V1 User Story (One Sentence)

> Each week, I manually enter this round's fixtures and odds into a file, run Ralph from the command line, and get back a formatted tip sheet with picks, confidence levels, rationale in Ralph's voice, and a teaching moment — ready to paste into the office Slack channel.

---

## Next Step: Phase 4

Phase 4 of the Ralph Methodology calls for writing detailed `specs/*.md` files for each Activity in the SLC slice, plus a prioritized `IMPLEMENTATION_PLAN.md` with acceptance-driven backpressure.

The SLC slice has 7 active cells (Activity 3 is skipped) that need specs:

1. `specs/01-fixtures.md` — Manual fixture input format and validation
2. `specs/02-market-odds.md` — Odds input, implied probability math, overround removal
3. `specs/03-picks.md` — Pick generation logic, confidence tiers
4. `specs/04-rationale.md` — Template-driven rationale with Ralph's voice
5. `specs/05-teaching.md` — Weekly teaching content selection and integration
6. `specs/06-tracking.md` — Result recording and accuracy calculation
7. `specs/07-output.md` — CLI output formatting and the tip sheet template

Invoke Phase 4 with:
> "Ralph, let's move to Phase 4. Write the specs and implementation plan for the SLC slice."

---

*Ralph Story Map v1.0 — "I don't know everything about footy, but I know what the bookies think, and I can explain it in plain English."*
