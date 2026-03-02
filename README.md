# Ralph -- NRL Footy Forecaster

Ralph is an NRL tipping tool that uses betting market odds and LLM-powered sentiment analysis to generate weekly tips -- and, more importantly, to teach your colleagues about AI, probability, and how markets work.

> "I don't know everything about footy, but I learned a few things from the quant desk."

## How it works

- **Market consensus**: Ralph pulls H2H odds from multiple bookmakers, converts them to implied probabilities (removing the overround), and averages across sources to establish a baseline view.
- **LLM sentiment layer**: Claude analyses team news, injuries, suspensions, and recent form to apply small adjustments (+/- 1-5%) to the market consensus via lightweight Bayesian updating.
- **Tip generation**: Each game gets a final pick, a confidence level (Lock / Lean / Coin Flip), and a plain-English rationale explaining why.
- **Teaching moments**: Every round includes a rotating "Did You Know?" segment covering probability, market efficiency, machine learning, or behavioural science -- footy is the hook, education is the payload.

## Quick start

```bash
# Install in development mode
pip install -e ".[dev]"

# Run Ralph
ralph

# Generate tips for the current round (coming soon)
ralph tip
```

## Project vision

See [GENESIS.md](GENESIS.md) for the full vision, architecture, teaching topics library, and iterative build plan.
