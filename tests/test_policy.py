import asyncio
import importlib
import json
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
    assert first.interrupt_human is False
    assert second.decision is Decision.RECORD
    assert second.interrupt_human is False
    assert second.exact_action is None
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
    assert result["outcomes"][-1]["interrupt_human"] is False
    assert result["outcomes"][-1]["exact_action"] is None


def test_urgent_duplicate_suppresses_delivery_but_preserves_original_ledger():
    store = EventStore()
    event = make_event(kind="organizer_request")
    first, duplicate = store.process(event)
    original = tuple(store.connection.execute("SELECT * FROM event_decisions").fetchone())
    second, replayed = store.process(event)
    assert first.decision is Decision.ESCALATE
    assert first.interrupt_human is True
    assert first.exact_action
    assert duplicate is False
    assert replayed is True
    assert second.decision is Decision.RECORD
    assert second.interrupt_human is False
    assert second.exact_action is None
    assert "suppressed" in second.reason
    assert tuple(store.connection.execute("SELECT * FROM event_decisions").fetchone()) == original
    assert store.metrics()["unique_events"] == 1
    assert store.metrics()["human_interruptions"] == 1


def test_urgent_cli_replay_stays_quiet_after_database_reopen(tmp_path):
    scenario = tmp_path / "scenario.json"
    event = make_event(kind="winner").to_dict()
    scenario.write_text(json.dumps([event, event]))
    database = tmp_path / "events.sqlite3"
    first = run_scenario(scenario, database)
    reopened = run_scenario(scenario, database)
    assert [row["interrupt_human"] for row in first["outcomes"]] == [True, False]
    assert all(row["duplicate"] for row in reopened["outcomes"])
    assert all(not row["interrupt_human"] for row in reopened["outcomes"])
    assert all(row["exact_action"] is None for row in reopened["outcomes"])
    assert first["metrics"] == reopened["metrics"]


def test_strands_tool_boundary_suppresses_urgent_duplicate(tmp_path, monkeypatch):
    # Keep even the tool module's default ledger creation in a temporary directory.
    monkeypatch.chdir(tmp_path)
    tools = importlib.import_module("only_when_it_matters.tools")
    monkeypatch.setattr(tools, "_store", EventStore())
    event = make_event(kind="organizer_request").to_dict()
    first = tools.triage_contest_event(**event)
    duplicate = tools.triage_contest_event(**event)
    assert first["interrupt_human"] is True
    assert duplicate["duplicate"] is True
    assert duplicate["interrupt_human"] is False
    assert duplicate["exact_action"] is None
    assert tools.campaign_attention_metrics()["human_interruptions"] == 1


def test_strands_worker_thread_stream_and_concurrent_retries(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tools = importlib.import_module("only_when_it_matters.tools")
    store = EventStore()
    monkeypatch.setattr(tools, "_store", store)
    event = make_event(kind="organizer_request").to_dict()

    async def invoke(tool, arguments, call_id):
        chunks = [chunk async for chunk in tool.stream(
            {"toolUseId": call_id, "name": tool.tool_name, "input": arguments}, {}
        )]
        return chunks[-1]["tool_result"]

    async def run():
        results = await asyncio.gather(*[
            invoke(tools.triage_contest_event, event, f"retry-{index}")
            for index in range(12)
        ])
        metrics = await invoke(tools.campaign_attention_metrics, {}, "metrics")
        return results, metrics

    results, metrics = asyncio.run(run())
    assert all(result["status"] == "success" for result in results)
    payloads = [json.loads(result["content"][0]["text"]) for result in results]
    assert sum(row["interrupt_human"] for row in payloads) == 1
    assert sum(row["duplicate"] for row in payloads) == 11
    assert all(row["exact_action"] is None for row in payloads if row["duplicate"])
    assert metrics["status"] == "success"
    assert store.metrics()["unique_events"] == 1
    assert store.metrics()["human_interruptions"] == 1
