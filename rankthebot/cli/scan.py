from __future__ import annotations

import typer
from rich.console import Console

from rankthebot.config import Config, DB_PATH
from rankthebot.core.llms.openai import OpenAIClient
from rankthebot.core.scan_runner import ScanSettings, run_scan
from rankthebot.db.store import Store

console = Console()


def scan(
    llms: str = typer.Option("chatgpt", "--llms", help="Comma-separated LLMs"),
    runs: int = typer.Option(3, min=1, max=20, help="Runs per query"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Estimate calls without executing"),
) -> None:
    cfg = Config.load()
    if not cfg.openai_api_key:
        raise typer.BadParameter("Missing OpenAI key. Run: rankthebot auth connect --openai")

    store = Store(DB_PATH)
    llm_list = [x.strip() for x in llms.split(",") if x.strip()]

    unsupported = [x for x in llm_list if x.lower() != "chatgpt"]
    if unsupported:
        console.print(
            f"[yellow]Phase 1 supports only chatgpt. Ignoring:[/yellow] {', '.join(unsupported)}"
        )

    settings = ScanSettings(runs=runs, llms=llm_list, dry_run=dry_run)
    client = OpenAIClient(cfg.openai_api_key)
    total_calls, completed = run_scan(store, client, settings)

    if dry_run:
        console.print(f"Estimated API calls: [bold]{total_calls}[/bold]")
    else:
        console.print(f"Completed [bold]{completed}[/bold] of [bold]{total_calls}[/bold] calls.")
