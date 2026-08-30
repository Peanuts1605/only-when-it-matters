from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum


class Decision(StrEnum):
    IGNORE = "IGNORE"
    RECORD = "RECORD"
    ESCALATE = "ESCALATE"


@dataclass(frozen=True)
class Event:
    event_id: str
    contest: str
    kind: str
    sender: str
    subject: str
    received_at: str
    deadline_at: str | None = None
    actionable: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class Classification:
    decision: Decision
    reason: str
    exact_action: str | None
    interrupt_human: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


RESULT_KINDS = {"acceptance", "rejection", "winner", "eligibility_action"}
ROUTINE_KINDS = {"status_update", "receipt", "registration_confirmation"}
NOISE_KINDS = {"newsletter", "marketing", "social", "unrelated"}


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def classify_event(event: Event, *, now: datetime | None = None) -> Classification:
    """Apply the deterministic attention boundary before model interpretation."""
    current = (now or datetime.now(UTC)).astimezone(UTC)

    if event.kind in NOISE_KINDS:
        return Classification(Decision.IGNORE, "non-delivery noise", None, False)

    if event.kind in RESULT_KINDS:
        return Classification(
            Decision.ESCALATE,
            f"contest {event.kind} requires human awareness",
            f"Review {event.contest}: {event.subject}",
            True,
        )

    if event.kind == "organizer_request" or event.actionable:
        return Classification(
            Decision.ESCALATE,
            "organizer requested a concrete action",
            f"Respond to the organizer requirement in: {event.subject}",
            True,
        )

    if event.deadline_at:
        hours = (_parse_timestamp(event.deadline_at) - current).total_seconds() / 3600
        if hours <= 72:
            return Classification(
                Decision.ESCALATE,
                f"deadline is {max(hours, 0):.1f} hours away",
                f"Complete the next verified submission step for {event.contest}",
                True,
            )

    if event.kind in ROUTINE_KINDS:
        return Classification(
            Decision.RECORD,
            "useful delivery evidence without a human decision",
            None,
            False,
        )

    return Classification(
        Decision.RECORD,
        "retained for campaign context; no immediate human action",
        None,
        False,
    )

