from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

from rankthebot.config import DB_PATH
from rankthebot.core.reporter import print_competitors, print_visibility
from rankthebot.db.store import Store

app = typer.Typer(help="Generate reports")
console = Console()


@app.command("competitors")
def competitors(
    limit: int = typer.Option(15, "--limit", help="Number of competitors to show"),
    exclude: Optional[str] = typer.Option(None, "--exclude", help="Brand term to exclude (e.g. your own brand)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save results to a CSV file (e.g. competitors.csv)"),
) -> None:
    store = Store(DB_PATH)
    rows = store.top_competitors(limit=limit, exclude=exclude)
    if not rows:
        console.print("No scan data yet. Run [bold]rankthebot scan[/bold] first.")
        return
    print_competitors(console, rows, output=output)


@app.command("visibility")
def visibility(
    brand: str = typer.Option(..., "--brand", help="Brand domain/name to measure"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save results to a CSV file (e.g. visibility.csv)"),
) -> None:
    store = Store(DB_PATH)
    rows = store.visibility_for_brand(brand)
    if not rows:
        console.print("No scan data yet. Run [bold]rankthebot scan[/bold] first.")
        return

    print_visibility(console, rows, brand, output=output)

    zero_rows = store.top_zero_visibility_queries(brand, limit=8)
    if zero_rows:
        console.print("\n[bold]Top queries with zero visibility:[/bold]")
        for row in zero_rows:
            console.print(f"- {row['query_text']} ({row['llm']})")
