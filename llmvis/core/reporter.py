from __future__ import annotations

from rich.console import Console
from rich.table import Table

from llmvis.core.scorer import visibility_score


def print_competitors(console: Console, rows: list) -> None:
    table = Table(title="Top Competitors by LLM Visibility")
    table.add_column("#", style="dim")
    table.add_column("Brand")
    table.add_column("Mention Rate")
    table.add_column("Avg Position")
    table.add_column("Score")

    for i, row in enumerate(rows, start=1):
        total_runs = int(row["total_runs"])
        mentioned_runs = int(row["mentioned_runs"])
        avg_position = row["avg_position"]
        mention_rate = (mentioned_runs / total_runs * 100) if total_runs else 0.0
        score = visibility_score(mention_rate, avg_position)
        table.add_row(
            str(i),
            row["brand"],
            f"{mention_rate:.1f}% ({mentioned_runs}/{total_runs})",
            "-" if avg_position is None else f"{float(avg_position):.2f}",
            f"{score:.1f}",
        )

    console.print(table)


def print_visibility(console: Console, rows: list, brand: str) -> None:
    table = Table(title=f"Visibility Report - {brand}")
    table.add_column("LLM")
    table.add_column("Mention Rate")
    table.add_column("Avg Position")
    table.add_column("Score")

    overall_rates: list[float] = []
    overall_positions: list[float] = []

    for row in rows:
        total_runs = int(row["total_runs"])
        mentioned_runs = int(row["mentioned_runs"])
        avg_position = row["avg_position"]
        if total_runs == 0:
            mention_rate = 0.0
        else:
            mention_rate = (mentioned_runs / total_runs) * 100
        score = visibility_score(mention_rate, avg_position)
        overall_rates.append(mention_rate)
        if avg_position is not None:
            overall_positions.append(float(avg_position))

        table.add_row(
            row["llm"],
            f"{mention_rate:.1f}% ({mentioned_runs}/{total_runs})",
            "-" if avg_position is None else f"{float(avg_position):.2f}",
            f"{score:.1f}",
        )

    console.print(table)

    if overall_rates:
        avg_rate = sum(overall_rates) / len(overall_rates)
        avg_pos = (sum(overall_positions) / len(overall_positions)) if overall_positions else None
        console.print(
            f"[bold]Overall Score:[/bold] {visibility_score(avg_rate, avg_pos):.1f}/100"
        )
