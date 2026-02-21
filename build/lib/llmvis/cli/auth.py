from __future__ import annotations

import typer
from rich.console import Console

from llmvis.config import Config

app = typer.Typer(help="Manage API credentials")
console = Console()


@app.command("connect")
def connect(
    openai: bool = typer.Option(False, "--openai", help="Connect OpenAI API key"),
    key: str | None = typer.Option(None, "--key", help="API key value (optional)")
) -> None:
    if not openai:
        raise typer.BadParameter("Only --openai is supported in Phase 1")

    cfg = Config.load()
    if key is None:
        key = typer.prompt("Enter OpenAI API key", hide_input=True)

    cfg.openai_api_key = key.strip()
    cfg.save()
    console.print("[green]Saved OpenAI API key.[/green]")
