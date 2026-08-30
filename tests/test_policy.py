from datetime import UTC, datetime
from pathlib import Path

from only_when_it_matters.cli import run_scenario
from only_when_it_matters.policy import Decision, Event, classify_event
from only_when_it_matters.store import EventStore

NOW = datetime(2026, 8, 30, 12, tzinfo=UTC)


def make_event(**overrides):
    values = {
        "event_id": "evt-1",
        "contest": "Example",
        "kind": "status_update",
        "sender": "organizer@example.test",
        "subject": "Status",
        "received_at": "2026-08-30T12:00:00Z",
    }
    values.update(overrides)
    return Event(**values)


def test_false_positive_noise_does_not_interrupt():
    result = classify_event(make_event(kind="newsletter"), now=NOW)
    assert result.decision is Decision.IGNORE
    assert result.interrupt_human is False


def test_organizer_request_escalates_with_exact_action():
    result = classify_event(make_event(kind="organizer_request"), now=NOW)
    assert result.decision is Decision.ESCALATE
    assert result.interrupt_human is True
    assert "Respond" in result.exact_action


def test_imminent_deadline_escalates():
    result = classify_event(
        make_event(deadline_at="2026-09-01T12:00:00Z"), now=NOW
    )
    assert result.decision is Decision.ESCALATE
    assert "48.0 hours" in result.reason


def test_duplicate_is_idempotent_and_not_counted_twice():
    store = EventStore()
    event = make_event()
    first, first_duplicate = store.process(event)
    second, second_duplicate = store.process(event)
    assert first == second
    assert first_duplicate is False
    assert second_duplicate is True
    assert store.metrics()["unique_events"] == 1


def test_fixture_quantifies_avoided_interruptions():
    result = run_scenario(Path(__file__).with_name("fixtures.json"))
    assert result["metrics"] == {
        "unique_events": 4,
        "human_interruptions": 2,
        "interruptions_avoided": 2,
        "avoidance_rate": 0.5,
    }
    assert result["outcomes"][-1]["duplicate"] is True

