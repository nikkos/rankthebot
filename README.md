
<div align="center">

<img src="logo.svg" width="64" alt="rankthebot" />

**Track how visible your brand is when people ask ChatGPT or Claude — and outrank your competitors.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Made by Nikos Lamprakakis](https://img.shields.io/badge/made%20by-Nikos%20Lamprakakis-orange)](https://github.com/nikkos)

</div>

---

## What is rankthebot?

People are increasingly asking ChatGPT, Claude, and other AI assistants things like *"What's the best CRM software?"* or *"Which project management tool should I use?"* — and your brand may or may not be showing up in those answers.

**rankthebot** is a command-line tool that:

- Runs hundreds of relevant queries against **ChatGPT and/or Claude**
- Detects which brands get mentioned — and in what position
- Scores your brand's **LLM visibility** from 0 to 100, per LLM
- Shows you exactly **which competitors** are winning in AI responses
- Exports everything to **CSV** for easy analysis in Excel or Google Sheets

---

## How It Works

Understanding the process helps you get better results. Here is what happens under the hood when you run RankTheBot:

### Step 1 — Query expansion

You start with a broad intent like *"CRM software"*. RankTheBot generates dozens of realistic query variants by combining different **personas** (small business owner, developer, enterprise buyer, agency) and **phrasings** (best X for Y, X comparison, what X should I use). This simulates the wide range of ways real users ask ChatGPT about a topic.

### Step 2 — Scanning

For each query, RankTheBot sends it to your chosen LLM(s) — **ChatGPT (GPT-5.2)** and/or **Claude (claude-sonnet-4-6)** — and collects the response. Each query is run multiple times (default: 3) to account for the natural variability in LLM responses — the same question can produce different answers on different runs. Running both LLMs lets you compare how your brand is perceived across different AI assistants.

### Step 3 — Brand extraction

Each response is passed to a second AI model (**GPT-5-mini**) that acts as a parser. It reads the response and extracts every brand mentioned, along with:
- **Position** — the order in which the brand was mentioned (1 = first)
- **Sentiment** — whether the mention was positive, neutral, negative, or qualified
- **Context** — the exact phrase where the brand appeared

All results are stored locally in a SQLite database on your machine.

### Step 4 — Scoring

The visibility score (0–100) is calculated from two signals:

- **Mention rate** — what percentage of runs included your brand
- **Position weight** — brands mentioned first score higher; position 1 keeps full weight, each subsequent position decays by ~18%

This means a brand that is mentioned in every response but always listed 5th scores lower than a brand mentioned in 80% of responses but always listed first.

### Step 5 — Reporting

Results are displayed as a ranked table in your terminal and can be exported to CSV for further analysis in Google Sheets or Excel.

```
You  →  define queries
         ↓
ChatGPT / Claude  →  generate responses
         ↓
GPT-5.2-mini  →  extracts brand mentions
         ↓
SQLite  →  stores everything locally (tagged by LLM)
         ↓
rankthebot  →  scores and ranks brands, per LLM
```

---

## Requirements

- A Mac or Linux computer (Windows via WSL also works)
- Python 3.9 or higher ([download here](https://www.python.org/downloads/))
- An OpenAI API key ([get one here](https://platform.openai.com/api-keys)) — required for scanning with ChatGPT and for brand extraction
- An Anthropic API key ([get one here](https://console.anthropic.com/settings/keys)) — optional, required only if you want to scan with Claude

### Check your Python version

Open your terminal and run:

```bash
python3 --version
```

You should see `Python 3.9.x` or higher. If not, [download Python here](https://www.python.org/downloads/).

---

## Installation

### Step 1 — Download rankthebot

Clone the repository or download it as a ZIP:

```bash
git clone https://github.com/nikkos/rankthebot.git
cd rankthebot
```

Or [click here to download the ZIP](https://github.com/nikkos/rankthebot/archive/refs/heads/main.zip), unzip it, and open your terminal in that folder.

### Step 2 — Install rankthebot

Run this command inside the project folder:

```bash
pip3 install -e .
```

### Step 3 — Add rankthebot to your PATH

After installation, you may need to add the install location to your PATH so you can run `rankthebot` from anywhere.

**On Mac (zsh):**

```bash
echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**On Linux:**

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Step 4 — Verify the installation

```bash
rankthebot --help
```

You should see the rankthebot command menu. You are ready to go!

---

## Security — Protecting your API keys

> **Your API keys are stored locally on your machine only.**
> They are saved in `~/.rankthebot/config.json` — a hidden folder in your home directory, **outside** the project folder.
> This means they are **never** committed to Git or uploaded to GitHub.

Never share your `~/.rankthebot/config.json` file with anyone.
If you accidentally expose a key, rotate it immediately:
- OpenAI: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- Anthropic: [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)

---

## Quick Start

### 1. Connect your API key(s)

Connect OpenAI (required):

```bash
rankthebot auth connect --openai
```

Connect Anthropic (optional — needed to scan with Claude):

```bash
rankthebot auth connect --anthropic
```

You will be prompted to paste your API key. It is hidden while you type.

---

### 2. Add the queries you want to track

Add queries one by one:

```bash
rankthebot queries add "best CRM software"
rankthebot queries add "best project management tool"
```

Or automatically generate dozens of variants from a single intent:

```bash
rankthebot queries expand "CRM software"
```

This generates queries like:
- *"best CRM software for small business owner"*
- *"CRM software comparison for enterprise buyer"*
- *"what CRM software should I use as a developer"*

See all saved queries:

```bash
rankthebot queries list
```

---

### 3. Run a scan

First, do a dry run to see how many API calls it will make (and estimate cost):

```bash
rankthebot scan --dry-run
```

Then run the actual scan:

```bash
rankthebot scan
```

Scan with Claude instead of (or in addition to) ChatGPT:

```bash
rankthebot scan --llms claude
rankthebot scan --llms chatgpt,claude
```

By default it runs **3 passes per query**. You can change this:

```bash
rankthebot scan --runs 5
```

Scans run **10 concurrent workers** by default, reducing a typical scan from 40+ minutes to 3–5 minutes. Raise or lower the limit if needed:

```bash
rankthebot scan --workers 20   # faster, higher API burst
rankthebot scan --workers 3    # slower, conservative rate limiting
```

> **Typical cost:** ~$0.80–$1.50 for 65 queries × 3 runs using GPT-5.2. Claude costs vary by model — claude-sonnet-4-6 is comparable to GPT-5.2.

---

### 4. View your brand's visibility report

```bash
rankthebot report visibility --brand "hubspot"
```

**Example output (with both LLMs):**

```
         Visibility Report - hubspot
┌──────────┬───────────────┬──────────────┬───────┐
│ LLM      │ Mention Rate  │ Avg Position │ Score │
├──────────┼───────────────┼──────────────┼───────┤
│ chatgpt  │ 100.0%        │ 1.91         │ 83.7  │
│ claude   │ 87.5%         │ 2.10         │ 71.4  │
└──────────┴───────────────┴──────────────┴───────┘
Overall Score: 77.6/100
```

Save to CSV for Google Sheets or Excel:

```bash
rankthebot report visibility --brand "hubspot" --output visibility.csv
```

---

### 5. See your top competitors

```bash
rankthebot report competitors
```

Exclude your own brand to focus on the competition:

```bash
rankthebot report competitors --exclude "hubspot"
```

Save to CSV:

```bash
rankthebot report competitors --output competitors.csv
```

**Example output:**

```
           Top Competitors by LLM Visibility
┌────┬─────────────────────────┬───────────┬─────────────┬──────────────┬───────┐
│  # │ Brand                   │ Mention % │ Runs        │ Avg Position │ Score │
├────┼─────────────────────────┼───────────┼─────────────┼──────────────┼───────┤
│  1 │ HubSpot CRM             │ 93.8%     │ 183/195     │ 1.70         │ 82.0  │
│  2 │ Zoho CRM                │ 93.3%     │ 182/195     │ 2.59         │ 66.6  │
│  3 │ Pipedrive               │ 66.7%     │ 130/195     │ 4.22         │ 28.0  │
└────┴─────────────────────────┴───────────┴─────────────┴──────────────┴───────┘
```

---

## Understanding the Score

The **visibility score (0–100)** combines two factors:

| Factor | What it measures |
|--------|-----------------|
| **Mention rate** | How often your brand appears across all queries |
| **Avg position** | How early in the response your brand is mentioned (position 1 = first) |

A brand mentioned in 100% of responses at position 1 scores **100/100**.
A brand mentioned in 50% of responses at position 5 scores much lower.

---

## Full Command Reference

```
rankthebot auth connect --openai              Connect your OpenAI API key (required)
rankthebot auth connect --anthropic           Connect your Anthropic API key (for Claude)

rankthebot queries add "query text"          Add a single query
rankthebot queries expand "intent"           Generate query variants from an intent
rankthebot queries list                      List all saved queries

rankthebot scan                              Run the scan (ChatGPT by default)
rankthebot scan --llms claude                Scan with Claude only
rankthebot scan --llms chatgpt,claude        Scan with both LLMs
rankthebot scan --dry-run                    Estimate API calls without running
rankthebot scan --runs 5                     Set number of runs per query (default: 3)
rankthebot scan --workers 20                 Set concurrent API workers (default: 10)

rankthebot report visibility --brand NAME    Show your brand's visibility score
rankthebot report competitors                Show top brands by LLM visibility
rankthebot report competitors --exclude NAME Exclude a brand (e.g. your own)
rankthebot report competitors --limit 10     Show top 10 only (default: 15)

All report commands support:
  --output results.csv                   Save results to CSV file
```

---

## CSV Export — Google Sheets

After exporting, open the CSV directly in Google Sheets:

1. Go to [sheets.google.com](https://sheets.google.com)
2. Click **File → Import**
3. Upload your CSV file
4. Select **"Comma"** as the separator

---

## License

MIT License — free to use, modify, and distribute.

---

<div align="center">
Built by <a href="https://github.com/nikkos">Nikos Lamprakakis</a>
</div>
