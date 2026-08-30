from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .policy import Classification, Event, classify_event


class EventStore:
    """Small idempotent ledger for replayable contest-event decisions."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.connection = sqlite3.connect(str(path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS event_decisions (
                event_id TEXT PRIMARY KEY,
                event_json TEXT NOT NULL,
                decision_json TEXT NOT NULL
            )
            """
        )

    def process(self, event: Event) -> tuple[Classification, bool]:
        existing = self.connection.execute(
            "SELECT decision_json FROM event_decisions WHERE event_id = ?", (event.event_id,)
        ).fetchone()
        if existing:
            data = json.loads(existing["decision_json"])
            return Classification(**data), True

        classification = classify_event(event)
        with self.connection:
            self.connection.execute(
                "INSERT INTO event_decisions(event_id, event_json, decision_json) VALUES (?, ?, ?)",
                (
                    event.event_id,
                    json.dumps(event.to_dict(), sort_keys=True),
                    json.dumps(classification.to_dict(), sort_keys=True),
                ),
            )
        return classification, False

    def metrics(self) -> dict[str, int | float]:
        rows = self.connection.execute("SELECT decision_json FROM event_decisions").fetchall()
        decisions = [json.loads(row["decision_json"])["decision"] for row in rows]
        total = len(decisions)
        interruptions = decisions.count("ESCALATE")
        avoided = total - interruptions
        return {
            "unique_events": total,
            "human_interruptions": interruptions,
            "interruptions_avoided": avoided,
            "avoidance_rate": round(avoided / total, 3) if total else 0.0,
        }

