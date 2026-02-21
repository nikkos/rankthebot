# LLM Visibility Tracker — Project Brief

## What This Is

A CLI tool that measures how often and how well a brand is mentioned across major LLM platforms (ChatGPT, Claude, Perplexity, Gemini) when users ask product discovery questions.

The core insight: Google rankings are tracked obsessively. LLM "rankings" — who gets recommended when someone asks an AI for a product — are tracked by nobody. This tool fixes that.

---

## The Problem It Solves

When a user asks ChatGPT *"what's the best email marketing tool for a small business?"* — your brand may or may not appear. It might appear third. It might be described as "expensive" or "hard to use." You have no visibility into any of this today.

Meanwhile, LLMs are capturing a growing share of product discovery queries that previously went through Google. Brands are losing pipeline to AI-driven recommendations they can't see or measure.

---

## Core Concepts

### Mention Rate
Out of N times a query is run, how often does the brand appear in the response? This is the primary visibility metric.

### Position
First mention in a response carries disproportionate weight. Position 1 vs Position 3 matters.

### Sentiment Context
LLMs attach qualifiers to brand mentions — *"best for enterprises," "affordable but limited," "complex setup."* These shape buyer perception.

### Share of Voice
For any query set, which brands dominate? If you're not mentioned, who is?

---

## Query Matrix

The tool doesn't just run one query. It expands a single intent into a matrix of variants:

```
Intent: "find CRM software"

Personas:
  - small business owner
  - enterprise buyer
  - developer
  - agency

Phrasings:
  - "best CRM for {persona}"
  - "recommend a CRM for {persona}"
  - "what CRM should I use for {use_case}"
  - "CRM comparison for {persona}"

Modifiers:
  - budget / enterprise / beginner / advanced
```

Each intent expands to ~40–60 query variants. Each is run 3–5 times per LLM to smooth out non-determinism.

---

## LLMs Targeted

| LLM | API | Notes |
|---|---|---|
| ChatGPT (GPT-4o) | OpenAI API | Largest user base |
| Perplexity | Perplexity API | Research-heavy, product discovery |
| Claude | Anthropic API | Professional/technical users |
| Gemini | Google AI API | Mobile, Google ecosystem |

---

## Data Model

```
QueryRun
  ├── query_text         (str)
  ├── llm                (chatgpt | perplexity | claude | gemini)
  ├── timestamp          (datetime)
  ├── raw_response       (str)
  └── parsed_mentions[]
        ├── brand         (str)
        ├── position      (int — order of first mention)
        ├── sentiment     (positive | neutral | negative | qualified)
        └── context       (str — the surrounding sentence)
```

Responses are parsed by a cheap LLM (GPT-4o mini or Claude Haiku) that extracts structured mention data from free-form text.

---

## CLI Interface

```bash
# Authentication
llmvis auth connect --openai
llmvis auth connect --anthropic
llmvis auth connect --perplexity
llmvis auth connect --gemini

# Query management
llmvis queries add "best email marketing tool"
llmvis queries list
llmvis queries expand          # auto-generate persona/phrasing variants
llmvis queries expand --review # review before saving

# Running scans
llmvis scan                          # run all queries across all LLMs
llmvis scan --llms chatgpt,perplexity
llmvis scan --runs 5                 # runs per query (default: 3)
llmvis scan --dry-run                # estimate cost before running

# Reports
llmvis report visibility --brand yourcompany.com
llmvis report competitors
llmvis report queries               # which queries show zero visibility
llmvis report timeline              # visibility score over time
llmvis report export --format csv
llmvis report export --format pdf
```

---

## Project Structure

```
llmvis/
├── cli/
│   ├── __init__.py
│   ├── auth.py          # API key management
│   ├── queries.py       # query CRUD + expansion
│   ├── scan.py          # orchestrate LLM calls
│   └── report.py        # report generation commands
├── core/
│   ├── llms/
│   │   ├── openai.py    # ChatGPT adapter
│   │   ├── anthropic.py # Claude adapter
│   │   ├── perplexity.py
│   │   └── gemini.py
│   ├── expander.py      # query matrix generation
│   ├── parser.py        # LLM response → structured mentions
│   ├── scorer.py        # visibility score calculation
│   └── reporter.py      # report formatting
├── db/
│   ├── models.py        # SQLite schema
│   └── store.py         # read/write layer
├── main.py
└── config.py
```

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| CLI framework | Typer | Type hints, clean API, auto-docs |
| Terminal output | Rich | Tables, progress bars, color |
| Database | SQLite (local) | Zero setup, portable, stores raw responses |
| LLM SDKs | openai, anthropic, google-generativeai | Official SDKs |
| HTTP | httpx | Async support for parallel LLM calls |
| Data processing | pandas | Aggregation and scoring |
| Config/secrets | python-dotenv | API key storage |

---

## Key Engineering Challenges

### Non-determinism
LLMs return different answers to the same question. Running each query 3–5 times and averaging mention rates is the solution. More runs = more stable data, higher cost.

### Parsing accuracy
Extracting brand mentions and sentiment from free-form text requires a parsing LLM. Prompt engineering here is critical — the parser must handle mentions that are implicit ("the Salesforce alternative everyone uses") not just explicit.

### API cost management
1,000 API calls per full scan is realistic. Cost controls needed:
- `--dry-run` flag estimates cost before executing
- Query deduplication (don't run near-identical queries)
- Tiered scan frequency (run full matrix weekly, quick scan daily)
- Cache raw responses so re-parsing is free

### Model update detection
When OpenAI or Anthropic updates a model, mention patterns shift. The tool should flag statistically significant changes in visibility score between scan dates and attribute them to known model release dates.

---

## Output Example

```
$ llmvis report visibility --brand acme.com

Visibility Report — acme.com
Scan: Feb 21 2026 | Queries: 48 | Runs per query: 5 | LLMs: 4
────────────────────────────────────────────────────────────────
LLM           Mention Rate   Avg Position   Sentiment
ChatGPT           64%            1.8          Positive
Perplexity        41%            2.4          Neutral
Claude            58%            2.1          Positive
Gemini            29%            3.1          Qualified
────────────────────────────────────────────────────────────────
Overall Score: 48 / 100

Top queries with zero visibility:
  - "best CRM for freelancers"
  - "affordable marketing tool for agencies"
  - "email tool with API access"

Competitors dominating your invisible queries:
  - HubSpot     (mentioned in 71% of queries where you're absent)
  - Mailchimp   (mentioned in 43%)
```

---

## Build Phases

### Phase 1 — Working prototype (2 weeks)
- Connect to OpenAI API only
- Hardcoded query list
- Run queries, store raw responses in SQLite
- Parse mentions with a simple prompt
- Print a basic table in terminal

### Phase 2 — Multi-LLM + query expansion (2 weeks)
- Add Perplexity, Claude, Gemini adapters
- Build query expander (persona × phrasing matrix)
- Add `--dry-run` cost estimation
- Improve parser accuracy

### Phase 3 — Scoring + reports (2 weeks)
- Visibility score algorithm
- Competitor share of voice
- Timeline view (score over time)
- CSV/PDF export

### Phase 4 — Polish (1 week)
- `pip install llmvis` distribution
- Config file support
- Scheduled scan support (cron-friendly output)

---

## What Success Looks Like

A marketer at a SaaS company runs `llmvis scan` on Monday morning and sees their visibility score dropped 12 points since last week. They drill into `llmvis report queries` and find three high-volume intents where they've gone invisible. They brief their content team that afternoon on what to publish. That's the core workflow this tool enables.

---

## Notes for the Developer

- Start with `cli/scan.py` and `core/llms/openai.py` — get one end-to-end flow working before touching anything else
- The parser prompt in `core/parser.py` is the most important piece of logic in the whole project — invest time here
- Store **all raw responses** permanently — you will want to re-parse them as the parser improves
- Use `rich.progress` for scan progress — LLM calls are slow and users need feedback
- Keep the SQLite schema simple early; resist normalizing too aggressively until the data model is stable
