from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

from llmvis.config import DB_PATH
from llmvis.core.reporter import print_competitors, print_visibility
from llmvis.db.store import Store

app = typer.Typer(help="Generate reports")
console = Console()


@app.command("competitors")
def competitors(
    limit: int = typer.Option(15, "--limit", help="Number of competitors to show"),
    exclude: Optional[str] = typer.Option(None, "--exclude", help="Brand term to exclude (e.g. your own brand)"),
) -> None:
    store = Store(DB_PATH)
    rows = store.top_competitors(limit=limit, exclude=exclude)
    if not rows:
        console.print("No scan data yet. Run [bold]llmvis scan[/bold] first.")
        return
    print_competitors(console, rows)


@app.command("visibility")
def visibility(brand: str = typer.Option(..., "--brand", help="Brand domain/name to measure")) -> None:
    store = Store(DB_PATH)
    rows = store.visibility_for_brand(brand)
    if not rows:
        console.print("No scan data yet. Run [bold]llmvis scan[/bold] first.")
        return

    print_visibility(console, rows, brand)

    zero_rows = store.top_zero_visibility_queries(brand, limit=8)
    if zero_rows:
        console.print("\n[bold]Top queries with zero visibility:[/bold]")
        for row in zero_rows:
            console.print(f"- {row['query_text']} ({row['llm']})")
