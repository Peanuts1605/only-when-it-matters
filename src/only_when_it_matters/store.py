from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock

from .policy import Classification, Decision, Event, classify_event


class EventStore:
    """Small idempotent ledger for replayable contest-event decisions."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        # Strands dispatches synchronous tools on worker threads. Serialize every
        # operation on this shared connection, including the read/insert pair.
        self._lock = RLock()
        self.connection = sqlite3.connect(str(path), check_same_thread=False)
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
        with self._lock:
            return self._process_locked(event)

    def _process_locked(self, event: Event) -> tuple[Classification, bool]:
        existing = self.connection.execute(
            "SELECT decision_json FROM event_decisions WHERE event_id = ?", (event.event_id,)
        ).fetchone()
        if existing:
            # Keep the first decision in the ledger without replaying its action.
            return Classification(
                Decision.RECORD,
                "duplicate event; repeated interruption suppressed",
                None,
                False,
            ), True

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
        """Count unique-event policy decisions, not delivered human notifications."""
        with self._lock:
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
