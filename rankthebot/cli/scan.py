from __future__ import annotations

import typer
from rich.console import Console

from rankthebot.config import Config, DB_PATH
from rankthebot.core.llms.openai import OpenAIClient
from rankthebot.core.llms.anthropic import AnthropicClient
from rankthebot.core.scan_runner import ScanSettings, run_scan
from rankthebot.db.store import Store

console = Console()

SUPPORTED_LLMS = {"chatgpt", "claude"}


def scan(
    llms: str = typer.Option("chatgpt", "--llms", help="Comma-separated LLMs (chatgpt, claude)"),
    runs: int = typer.Option(3, min=1, max=20, help="Runs per query"),
    workers: int = typer.Option(10, min=1, max=50, help="Concurrent API workers (default: 10)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Estimate calls without executing"),
) -> None:
    cfg = Config.load()
    if not cfg.openai_api_key:
        raise typer.BadParameter("Missing OpenAI key. Run: rankthebot auth connect --openai")

    llm_list = [x.strip().lower() for x in llms.split(",") if x.strip()]

    unsupported = [x for x in llm_list if x not in SUPPORTED_LLMS]
    if unsupported:
        console.print(f"[yellow]Unsupported LLMs, ignoring:[/yellow] {', '.join(unsupported)}")
        llm_list = [x for x in llm_list if x in SUPPORTED_LLMS]

    if "claude" in llm_list and not cfg.anthropic_api_key:
        console.print(
            "[yellow]No Anthropic API key configured — skipping Claude.[/yellow] "
            "Run: rankthebot auth connect --anthropic"
        )
        llm_list = [x for x in llm_list if x != "claude"]

    if not llm_list:
        llm_list = ["chatgpt"]

    store = Store(DB_PATH)
    openai_client = OpenAIClient(cfg.openai_api_key)
    anthropic_client = AnthropicClient(cfg.anthropic_api_key) if cfg.anthropic_api_key else None

    settings = ScanSettings(runs=runs, llms=llm_list, dry_run=dry_run, workers=workers)
    total_calls, completed = run_scan(store, openai_client, settings, anthropic_client=anthropic_client)

    if dry_run:
        console.print(f"Estimated API calls: [bold]{total_calls}[/bold]")
    else:
        console.print(f"Completed [bold]{completed}[/bold] of [bold]{total_calls}[/bold] calls.")
