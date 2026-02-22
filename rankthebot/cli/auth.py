from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

from rankthebot.config import Config

app = typer.Typer(help="Manage API credentials")
console = Console()


@app.command("connect")
def connect(
    openai: bool = typer.Option(False, "--openai", help="Connect OpenAI API key"),
    anthropic: bool = typer.Option(False, "--anthropic", help="Connect Anthropic API key"),
    key: Optional[str] = typer.Option(None, "--key", help="API key value (optional)")
) -> None:
    if not openai and not anthropic:
        raise typer.BadParameter("Specify --openai or --anthropic")

    cfg = Config.load()

    if openai:
        if key is None:
            key = typer.prompt("Enter OpenAI API key", hide_input=True)
        cfg.openai_api_key = key.strip()
        cfg.save()
        console.print("[green]Saved OpenAI API key.[/green]")

    if anthropic:
        if key is None:
            key = typer.prompt("Enter Anthropic API key", hide_input=True)
        cfg.anthropic_api_key = key.strip()
        cfg.save()
        console.print("[green]Saved Anthropic API key.[/green]")
