"""Quick smoke test: verify gpt-5-mini works for parser and expander."""
from rankthebot.config import Config
from rankthebot.core.llms.openai import OpenAIClient
from rankthebot.core.parser import parse_mentions
from rankthebot.core.expander import expand_intent

config = Config.load()
if not config.openai_api_key:
    raise SystemExit("No OpenAI API key found. Set OPENAI_API_KEY or run `rankthebot auth`.")

client = OpenAIClient(api_key=config.openai_api_key)

# --- Expander test ---
print("Testing expander (gpt-5-mini)...")
queries = expand_intent("project management software", client, count=5)
assert queries, "Expander returned no queries"
print(f"  OK — got {len(queries)} queries")
for q in queries:
    print(f"    - {q}")

# --- Parser test ---
print("\nTesting parser (gpt-5-mini)...")
sample = (
    "For project management I'd recommend Notion, Asana, or Linear. "
    "Trello is also popular for smaller teams. Monday.com is great for enterprises."
)
mentions = parse_mentions(sample, parser_client=client)
assert mentions, "Parser returned no mentions"
print(f"  OK — got {len(mentions)} mentions")
for m in mentions:
    print(f"    [{m['position']}] {m['brand']} ({m['sentiment']})")

print("\nAll tests passed.")
