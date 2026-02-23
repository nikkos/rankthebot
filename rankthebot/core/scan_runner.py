from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional

from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn, TimeRemainingColumn

from rankthebot.core.llms.openai import OpenAIClient
from rankthebot.core.llms.anthropic import AnthropicClient
from rankthebot.core.parser import parse_mentions
from rankthebot.db.store import Store


@dataclass
class ScanSettings:
    runs: int
    llms: list[str]
    dry_run: bool = False
    workers: int = 10


def _run_one(
    *,
    query_id: int,
    query_text: str,
    llm: str,
    openai_client: OpenAIClient,
    anthropic_client: Optional[AnthropicClient],
    store: Store,
    db_lock: threading.Lock,
) -> bool:
    if llm == "chatgpt":
        raw = openai_client.complete(query_text)
    elif llm == "gpt5":
        raw = openai_client.complete(query_text, model="gpt-5", temperature=None)
    elif llm == "claude" and anthropic_client is not None:
        raw = anthropic_client.complete(query_text)
    else:
        return False

    mentions = parse_mentions(raw, parser_client=openai_client)

    with db_lock:
        run_id = store.add_query_run(
            query_id=query_id,
            query_text=query_text,
            llm=llm,
            raw_response=raw,
        )
        if mentions:
            store.add_mentions(run_id, mentions)

    return True


def run_scan(
    store: Store,
    openai_client: OpenAIClient,
    settings: ScanSettings,
    anthropic_client: Optional[AnthropicClient] = None,
) -> tuple[int, int]:
    queries = store.list_queries()
    if not queries:
        return (0, 0)

    supported = {"chatgpt", "gpt5", "claude"}
    requested = [llm.strip().lower() for llm in settings.llms if llm.strip()]
    llms = [llm for llm in requested if llm in supported] or ["chatgpt"]

    if anthropic_client is None and "claude" in llms:
        llms = [llm for llm in llms if llm != "claude"]

    total_calls = len(queries) * settings.runs * len(llms)
    if settings.dry_run:
        return (total_calls, 0)

    # Flat list of every (query_id, query_text, llm) task
    tasks = [
        (int(q["id"]), str(q["query_text"]), llm)
        for q in queries
        for _ in range(settings.runs)
        for llm in llms
    ]

    db_lock = threading.Lock()
    completed = 0

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
    ) as progress:
        bar = progress.add_task("Running scan", total=len(tasks))

        with ThreadPoolExecutor(max_workers=settings.workers) as executor:
            futures = {
                executor.submit(
                    _run_one,
                    query_id=qid,
                    query_text=qtext,
                    llm=llm,
                    openai_client=openai_client,
                    anthropic_client=anthropic_client,
                    store=store,
                    db_lock=db_lock,
                ): (qid, qtext, llm)
                for qid, qtext, llm in tasks
            }

            for future in as_completed(futures):
                try:
                    if future.result():
                        completed += 1
                except Exception:
                    pass
                progress.advance(bar)

    return (total_calls, completed)
