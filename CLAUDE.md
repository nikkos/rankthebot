# RankTheBot — Claude Code Context

## What this project does

RankTheBot is a Python CLI tool that measures brand visibility in LLM responses. It:
1. Expands a single search intent into 40 query variants (via GPT-4o-mini)
2. Sends queries to ChatGPT and/or Claude concurrently (default: 3 runs/query, 10 workers)
3. Extracts brand mentions using GPT-4o-mini as a parser (position, sentiment, context)
4. Scores brands 0–100 combining mention rate + position decay
5. Reports rankings per LLM and exports CSV

## Stack

- **Language:** Python ≥3.9
- **CLI framework:** Typer + Rich
- **HTTP client:** httpx
- **Storage:** SQLite (via `rankthebot/db/`)
- **Config:** `~/.rankthebot/config.json` (API keys stored locally)
- **Entry point:** `rankthebot/main.py` → `rankthebot.main:app`

## Project structure

```
rankthebot/
├── cli/          # Typer commands: auth, queries, scan, report
├── core/
│   ├── scan_runner.py   # ThreadPoolExecutor orchestration
│   ├── parser.py        # GPT-4o-mini brand extraction
│   ├── expander.py      # Query expansion (40 variants)
│   ├── scorer.py        # Visibility score calculation
│   ├── reporter.py      # Display + CSV export
│   └── llms/
│       ├── openai.py    # GPT-5.2 (scan), gpt-4o-mini (parser/expander)
│       └── anthropic.py # claude-sonnet-4-6
├── db/
│   ├── models.py        # SQLite schema: queries, query_runs, parsed_mentions
│   └── store.py         # Data access layer
├── config.py            # API key management
└── main.py              # App entry point
```

## Key model IDs

| Purpose | Model |
|---------|-------|
| Scan (OpenAI) | `gpt-5.2` (or latest GPT main model) |
| Scan (Anthropic) | `claude-sonnet-4-6` |
| Parser & Expander | `gpt-5.2` |

## Development notes

- Run locally: `pip install -e .` then `rankthebot --help`
- No test suite currently
- SQLite DB lives in `~/.rankthebot/data.db` (or similar path — check `config.py`)
- All LLM calls are synchronous inside threads (httpx sync client)
- Errors from the parser should surface, not fail silently
