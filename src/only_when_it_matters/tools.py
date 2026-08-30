from __future__ import annotations

from pathlib import Path

from strands import tool

from .policy import Event
from .store import EventStore

_store = EventStore(Path(".only-when-it-matters.sqlite3"))


@tool
def triage_contest_event(
    event_id: str,
    contest: str,
    kind: str,
    sender: str,
    subject: str,
    received_at: str,
    deadline_at: str | None = None,
    actionable: bool = False,
) -> dict[str, object]:
    """Classify one contest-delivery event and return the exact human-attention boundary."""
    classification, duplicate = _store.process(
        Event(
            event_id=event_id,
            contest=contest,
            kind=kind,
            sender=sender,
            subject=subject,
            received_at=received_at,
            deadline_at=deadline_at,
            actionable=actionable,
        )
    )
    return {**classification.to_dict(), "duplicate": duplicate}


@tool
def campaign_attention_metrics() -> dict[str, int | float]:
    """Return measured human interruptions and avoided interruptions for unique events."""
    return _store.metrics()

