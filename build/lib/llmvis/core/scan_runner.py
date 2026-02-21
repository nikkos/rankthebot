from __future__ import annotations

from dataclasses import dataclass

from rich.progress import track

from llmvis.core.llms.openai import OpenAIClient
from llmvis.core.parser import parse_mentions
from llmvis.db.store import Store


@dataclass
class ScanSettings:
    runs: int
    llms: list[str]
    dry_run: bool = False


def run_scan(store: Store, openai_client: OpenAIClient, settings: ScanSettings) -> tuple[int, int]:
    queries = store.list_queries()
    if not queries:
        return (0, 0)

    supported = {"chatgpt"}
    requested = [llm.strip().lower() for llm in settings.llms if llm.strip()]
    llms = [llm for llm in requested if llm in supported] or ["chatgpt"]

    total_calls = len(queries) * settings.runs * len(llms)
    if settings.dry_run:
        return (total_calls, 0)

    completed = 0
    for query in track(queries, description="Running scan"):
        query_id = int(query["id"])
        query_text = str(query["query_text"])
        for _ in range(settings.runs):
            for llm in llms:
                if llm != "chatgpt":
                    continue
                raw = openai_client.complete(query_text)
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
