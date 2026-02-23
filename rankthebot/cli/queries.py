from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from rankthebot.config import DB_PATH, Config
from rankthebot.core.expander import expand_intent
from rankthebot.core.llms.openai import OpenAIClient
from rankthebot.db.store import Store

app = typer.Typer(help="Manage query set")
console = Console()


@app.command("add")
def add(query: str = typer.Argument(..., help="Query text")) -> None:
    store = Store(DB_PATH)
    query_id, inserted = store.add_query(query.strip())
    if inserted:
        console.print(f"[green]Saved query[/green] #{query_id}: {query}")
    else:
        console.print(f"[yellow]Query already exists[/yellow] as #{query_id}: {query}")


@app.command("list")
def list_queries() -> None:
    store = Store(DB_PATH)
    rows = store.list_queries()
    if not rows:
        console.print("No queries yet. Add one with [bold]rankthebot queries add[/bold].")
        return

    table = Table(title="Saved Queries")
    table.add_column("ID")
    table.add_column("Query")
    table.add_column("Created")
    for row in rows:
        table.add_row(str(row["id"]), row["query_text"], row["created_at"])
    console.print(table)


@app.command("clear")
def clear(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Delete all saved queries and their scan history."""
    store = Store(DB_PATH)
    rows = store.list_queries()
    if not rows:
        console.print("No queries to clear.")
        return

    if not yes:
        typer.confirm(
            f"This will permanently delete all {len(rows)} queries and their scan data. Continue?",
            abort=True,
        )

    deleted = store.clear_queries()
    console.print(f"[green]Cleared {deleted} queries and all associated scan data.[/green]")


@app.command("expand")
def expand(
    intent: str = typer.Argument(..., help="Base intent, e.g. 'CRM software'"),
    count: int = typer.Option(40, "--count", "-n", min=5, max=100, help="Number of queries to generate (default: 40)"),
    review: bool = typer.Option(False, "--review", help="Show generated queries without saving"),
) -> None:
    """Use AI to generate realistic query variants from an intent."""
    cfg = Config.load()
    if not cfg.openai_api_key:
        raise typer.BadParameter("Missing OpenAI key. Run: rankthebot auth connect --openai")

    client = OpenAIClient(cfg.openai_api_key)

    console.print(f"Generating [bold]{count}[/bold] queries for: [italic]{intent}[/italic]...")
    variants = expand_intent(intent, client, count=count)

    if not variants:
        console.print("[red]No queries generated. Check your OpenAI key and try again.[/red]")
        raise typer.Exit(1)

    if review:
        console.print(f"\nGenerated [bold]{len(variants)}[/bold] queries:")
        for v in variants:
            console.print(f"  - {v}")
        return

    store = Store(DB_PATH)
    inserted = 0
    for v in variants:
        _, is_new = store.add_query(v)
        if is_new:
            inserted += 1

    console.print(
        f"Generated [bold]{len(variants)}[/bold] queries. "
        f"Inserted [bold]{inserted}[/bold] new queries."
    )
