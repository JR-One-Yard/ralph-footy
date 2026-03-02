# Spec 01: Check This Week's Fixtures

**Activity:** Check This Week's Fixtures
**One-liner:** See which NRL teams are playing, where, and when this round.

---

## User Story

> As a workplace footy tipper, I want to load this week's NRL fixtures into Ralph so that the system knows which games to generate tips for.

---

## Scope

### IN (SLC v1)

- User manually creates a JSON file with the round's fixtures.
- Ralph validates the file against a strict schema.
- Ralph loads the fixtures into `Game` dataclass instances.
- CLI subcommand `ralph tip --round <N>` reads the fixture file from `data/rounds/round_<NN>.json`.
- Validation errors produce clear, actionable error messages.

### OUT (Deferred)

- Automated fixture scraping from NRL.com or any API.
- Auto-detection of the current round number.
- Handling of byes, postponements, or schedule changes beyond what the user types.
- LLM parsing of fixture announcements.

---

## Input Contract

### File Location

```
data/rounds/round_<NN>.json
```

Where `<NN>` is the zero-padded round number (e.g., `round_01.json`, `round_12.json`).

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "NRL Round Fixtures",
  "type": "object",
  "required": ["round_number", "season", "fixtures"],
  "properties": {
    "round_number": {
      "type": "integer",
      "minimum": 1,
      "maximum": 27
    },
    "season": {
      "type": "integer",
      "minimum": 2025
    },
    "fixtures": {
      "type": "array",
      "minItems": 1,
      "maxItems": 9,
      "items": {
        "type": "object",
        "required": ["home_team", "away_team", "venue", "kickoff"],
        "properties": {
          "home_team": {
            "type": "string",
            "minLength": 1
          },
          "away_team": {
            "type": "string",
            "minLength": 1
          },
          "venue": {
            "type": "string",
            "minLength": 1
          },
          "kickoff": {
            "type": "string",
            "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}$",
            "description": "ISO 8601 local time without timezone, e.g. 2025-03-06T20:00"
          }
        }
      }
    }
  }
}
```

### Example Fixture File

```json
{
  "round_number": 1,
  "season": 2025,
  "fixtures": [
    {
      "home_team": "Sydney Roosters",
      "away_team": "Brisbane Broncos",
      "venue": "Allianz Stadium",
      "kickoff": "2025-03-06T20:00"
    },
    {
      "home_team": "Penrith Panthers",
      "away_team": "Cronulla Sharks",
      "venue": "BlueBet Stadium",
      "kickoff": "2025-03-07T18:00"
    },
    {
      "home_team": "Melbourne Storm",
      "away_team": "Canterbury Bulldogs",
      "venue": "AAMI Park",
      "kickoff": "2025-03-07T19:55"
    },
    {
      "home_team": "Parramatta Eels",
      "away_team": "North Queensland Cowboys",
      "venue": "CommBank Stadium",
      "kickoff": "2025-03-08T15:00"
    },
    {
      "home_team": "Gold Coast Titans",
      "away_team": "Wests Tigers",
      "venue": "Cbus Super Stadium",
      "kickoff": "2025-03-08T17:30"
    },
    {
      "home_team": "Manly Sea Eagles",
      "away_team": "South Sydney Rabbitohs",
      "venue": "4 Pines Park",
      "kickoff": "2025-03-08T19:35"
    },
    {
      "home_team": "Canberra Raiders",
      "away_team": "New Zealand Warriors",
      "venue": "GIO Stadium",
      "kickoff": "2025-03-09T14:00"
    },
    {
      "home_team": "Newcastle Knights",
      "away_team": "St George Illawarra Dragons",
      "venue": "McDonald Jones Stadium",
      "kickoff": "2025-03-09T16:05"
    }
  ]
}
```

---

## Output Contract

A `list[Game]` where each `Game` is a populated instance of the `Game` dataclass from `ralph/models.py`:

```python
Game(
    home_team="Sydney Roosters",
    away_team="Brisbane Broncos",
    venue="Allianz Stadium",
    kickoff=datetime(2025, 3, 6, 20, 0),
    round_number=1,
)
```

---

## Acceptance Criteria

1. **AC-01**: Given a valid `round_01.json` file in `data/rounds/`, calling the fixture loader returns a list of `Game` objects matching the file contents.
2. **AC-02**: Given a fixture file missing a required field (e.g., no `venue`), the loader raises a `ValueError` with a message identifying the missing field and the game index.
3. **AC-03**: Given a fixture file with an invalid `kickoff` format (e.g., `"Friday 8pm"`), the loader raises a `ValueError` with a message explaining the expected format.
4. **AC-04**: Given a fixture file where `round_number` is outside 1-27, the loader raises a `ValueError`.
5. **AC-05**: Given a round number passed via CLI (`ralph tip --round 1`), the system looks for `data/rounds/round_01.json` and loads it.
6. **AC-06**: Given a round number with no corresponding file, the system prints a clear error message telling the user where the file should be and what format it should use.
7. **AC-07**: The loader correctly parses the `kickoff` string into a Python `datetime` object.
8. **AC-08**: The `round_number` from the file is injected into each `Game` instance.
9. **AC-09**: Fixture files with 1-9 games are accepted (accommodates bye rounds with fewer than 8 games).

---

## Implementation Notes

### Files to Create

- `ralph/fixtures.py` — Fixture loading and validation logic. Functions:
  - `load_fixtures(round_number: int) -> list[Game]` — Main entry point. Reads JSON, validates, returns Game list.
  - `validate_fixture_data(data: dict) -> None` — Schema validation. Raises `ValueError` on failures.
  - `_parse_kickoff(kickoff_str: str) -> datetime` — Parse ISO 8601 kickoff string.
- `data/rounds/.gitkeep` — Already exists. Example fixture files live here.
- `tests/test_fixtures.py` — Unit tests covering all acceptance criteria.

### Files to Modify

- `ralph/cli.py` — Add `--round` argument to the `tip` subcommand. Wire up to `load_fixtures()`.

### Existing Files Referenced

- `ralph/models.py` — The `Game` dataclass is already defined and requires no changes.

### Design Decisions

- **No external validation library.** Use plain Python `isinstance` / `KeyError` checks. The schema is simple enough that adding `jsonschema` as a dependency is not worth it for SLC.
- **Zero-padded filenames.** `round_01.json` not `round_1.json`. Ensures alphabetical sorting matches numerical order.
- **Kickoff as naive datetime.** All NRL games are in AEST/AEDT. Timezone handling is deferred. Store as naive `datetime` parsed from `YYYY-MM-DDTHH:MM`.
- **No team name validation.** The system does not maintain a list of valid NRL team names in SLC. If the user types "Penrith Panfers", Ralph will happily tip the Panfers. This is acceptable for a manually-entered system.
