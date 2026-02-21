from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

from rankthebot.core.scorer import visibility_score


def _write_csv(path: str, headers: list, rows: list) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def print_competitors(console: Console, rows: list, output: Optional[str] = None) -> None:
    table = Table(title="Top Competitors by LLM Visibility")
    table.add_column("#", style="dim")
    table.add_column("Brand")
    table.add_column("Mention Rate %")
    table.add_column("Mentioned / Total Runs")
    table.add_column("Avg Position")
    table.add_column("Score")

    csv_rows: list = []

    for i, row in enumerate(rows, start=1):
        total_runs = int(row["total_runs"])
        mentioned_runs = int(row["mentioned_runs"])
        avg_position = row["avg_position"]
        mention_rate = (mentioned_runs / total_runs * 100) if total_runs else 0.0
        score = visibility_score(mention_rate, avg_position)
        avg_pos_str = "-" if avg_position is None else f"{float(avg_position):.2f}"
        table.add_row(
            str(i),
            row["brand"],
            f"{mention_rate:.1f}%",
            f"{mentioned_runs}/{total_runs}",
            avg_pos_str,
            f"{score:.1f}",
        )
        csv_rows.append([i, row["brand"], f"{mention_rate:.1f}", mentioned_runs, total_runs, avg_pos_str, f"{score:.1f}"])

    console.print(table)

    if output:
        _write_csv(output, ["Rank", "Brand", "Mention Rate %", "Mentioned Runs", "Total Runs", "Avg Position", "Score"], csv_rows)
        console.print(f"[green]Saved to[/green] {output}")


def print_visibility(console: Console, rows: list, brand: str, output: Optional[str] = None) -> None:
    table = Table(title=f"Visibility Report - {brand}")
    table.add_column("LLM")
    table.add_column("Mention Rate %")
    table.add_column("Mentioned / Total Runs")
    table.add_column("Avg Position")
    table.add_column("Score")

    overall_rates: list[float] = []
    overall_positions: list[float] = []
    csv_rows: list = []

    for row in rows:
        total_runs = int(row["total_runs"])
        mentioned_runs = int(row["mentioned_runs"])
        avg_position = row["avg_position"]
        mention_rate = (mentioned_runs / total_runs * 100) if total_runs else 0.0
        score = visibility_score(mention_rate, avg_position)
        avg_pos_str = "-" if avg_position is None else f"{float(avg_position):.2f}"
        overall_rates.append(mention_rate)
        if avg_position is not None:
            overall_positions.append(float(avg_position))

        table.add_row(
            row["llm"],
            f"{mention_rate:.1f}%",
            f"{mentioned_runs}/{total_runs}",
            avg_pos_str,
            f"{score:.1f}",
        )
        csv_rows.append([row["llm"], f"{mention_rate:.1f}", mentioned_runs, total_runs, avg_pos_str, f"{score:.1f}"])

    console.print(table)

    if overall_rates:
        avg_rate = sum(overall_rates) / len(overall_rates)
        avg_pos = (sum(overall_positions) / len(overall_positions)) if overall_positions else None
        overall_score = visibility_score(avg_rate, avg_pos)
        console.print(f"[bold]Overall Score:[/bold] {overall_score:.1f}/100")
        csv_rows.append(["OVERALL", f"{avg_rate:.1f}", "", "", "", f"{overall_score:.1f}"])

    if output:
        _write_csv(output, ["LLM", "Mention Rate %", "Mentioned Runs", "Total Runs", "Avg Position", "Score"], csv_rows)
        console.print(f"[green]Saved to[/green] {output}")
