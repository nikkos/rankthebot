from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from rich.progress import track

from rankthebot.core.llms.openai import OpenAIClient
from rankthebot.core.llms.anthropic import AnthropicClient
from rankthebot.core.parser import parse_mentions
from rankthebot.db.store import Store


@dataclass
class ScanSettings:
    runs: int
    llms: list[str]
    dry_run: bool = False


def run_scan(
    store: Store,
    openai_client: OpenAIClient,
    settings: ScanSettings,
    anthropic_client: Optional[AnthropicClient] = None,
) -> tuple[int, int]:
    queries = store.list_queries()
    if not queries:
        return (0, 0)

    supported = {"chatgpt", "claude"}
    requested = [llm.strip().lower() for llm in settings.llms if llm.strip()]
    llms = [llm for llm in requested if llm in supported] or ["chatgpt"]

    # Drop claude if no client was provided
    if anthropic_client is None and "claude" in llms:
        llms = [llm for llm in llms if llm != "claude"]

    total_calls = len(queries) * settings.runs * len(llms)
    if settings.dry_run:
        return (total_calls, 0)

    completed = 0
    for query in track(queries, description="Running scan"):
        query_id = int(query["id"])
        query_text = str(query["query_text"])
        for _ in range(settings.runs):
            for llm in llms:
                if llm == "chatgpt":
                    raw = openai_client.complete(query_text)
                elif llm == "claude" and anthropic_client is not None:
                    raw = anthropic_client.complete(query_text)
                else:
                    continue

                run_id = store.add_query_run(
                    query_id=query_id,
                    query_text=query_text,
                    llm=llm,
                    raw_response=raw,
                )
                mentions = parse_mentions(raw, parser_client=openai_client)
                if mentions:
                    store.add_mentions(run_id, mentions)
                completed += 1

    return (total_calls, completed)
