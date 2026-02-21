from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from llmvis.db.models import SCHEMA_SQL


class Store:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)

    def add_query(self, query_text: str) -> tuple[int, bool]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT OR IGNORE INTO queries(query_text, created_at) VALUES(?, ?)",
                (query_text, now),
            )
            if cur.lastrowid:
                return int(cur.lastrowid), True
            row = conn.execute(
                "SELECT id FROM queries WHERE query_text = ?",
                (query_text,),
            ).fetchone()
            assert row is not None
            return int(row["id"]), False

    def list_queries(self) -> list[sqlite3.Row]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, query_text, created_at FROM queries ORDER BY id"
            ).fetchall()
            return list(rows)

    def add_query_run(self, *, query_id: Optional[int], query_text: str, llm: str, raw_response: str) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO query_runs(query_id, query_text, llm, timestamp, raw_response)
                VALUES(?, ?, ?, ?, ?)
                """,
                (query_id, query_text, llm, now, raw_response),
            )
            return int(cur.lastrowid)

    def add_mentions(self, query_run_id: int, mentions: Iterable[dict]) -> None:
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO parsed_mentions(query_run_id, brand, position, sentiment, context)
                VALUES(?, ?, ?, ?, ?)
                """,
                [
                    (
                        query_run_id,
                        m["brand"],
                        int(m["position"]),
                        m["sentiment"],
                        m["context"],
                    )
                    for m in mentions
                ],
            )

    def visibility_for_brand(self, brand_term: str) -> list[sqlite3.Row]:
        like_term = f"%{brand_term.lower()}%"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                  qr.llm AS llm,
                  COUNT(DISTINCT qr.id) AS total_runs,
                  COUNT(DISTINCT CASE WHEN LOWER(pm.brand) LIKE ? THEN qr.id END) AS mentioned_runs,
                  AVG(CASE WHEN LOWER(pm.brand) LIKE ? THEN pm.position END) AS avg_position
                FROM query_runs qr
                LEFT JOIN parsed_mentions pm ON pm.query_run_id = qr.id
                GROUP BY qr.llm
                ORDER BY qr.llm
                """,
                (like_term, like_term),
            ).fetchall()
            return list(rows)

    def top_competitors(self, limit: int = 15, exclude: Optional[str] = None) -> list[sqlite3.Row]:
        with self._connect() as conn:
            if exclude:
                rows = conn.execute(
                    """
                    SELECT
                      brand,
                      COUNT(DISTINCT query_run_id) AS mentioned_runs,
                      ROUND(AVG(position), 2) AS avg_position,
                      (SELECT COUNT(*) FROM query_runs) AS total_runs
                    FROM parsed_mentions
                    WHERE LOWER(brand) NOT LIKE ?
                    GROUP BY LOWER(brand)
                    ORDER BY mentioned_runs DESC
                    LIMIT ?
                    """,
                    (f"%{exclude.lower()}%", limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT
                      brand,
                      COUNT(DISTINCT query_run_id) AS mentioned_runs,
                      ROUND(AVG(position), 2) AS avg_position,
                      (SELECT COUNT(*) FROM query_runs) AS total_runs
                    FROM parsed_mentions
                    GROUP BY LOWER(brand)
                    ORDER BY mentioned_runs DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            return list(rows)

    def top_zero_visibility_queries(self, brand_term: str, limit: int = 10) -> list[sqlite3.Row]:
        like_term = f"%{brand_term.lower()}%"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT qr.query_text AS query_text, qr.llm AS llm, COUNT(*) AS runs
                FROM query_runs qr
                WHERE qr.id NOT IN (
                  SELECT query_run_id FROM parsed_mentions WHERE LOWER(brand) LIKE ?
                )
                GROUP BY qr.query_text, qr.llm
                ORDER BY runs DESC, qr.query_text
                LIMIT ?
                """,
                (like_term, limit),
            ).fetchall()
            return list(rows)
