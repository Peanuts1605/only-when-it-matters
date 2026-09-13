import asyncio
import json

import pytest
from strands.models.model import Model

from only_when_it_matters.guarded import run_guarded_request
from only_when_it_matters.policy import Classification, Decision, Event
from only_when_it_matters.store import EventStore

EVENT = {"event_id": "guard-test", "contest": "Fictional", "kind": "organizer_request",
         "sender": "organizer@example.test", "subject": "Add a disclosure",
         "received_at": "2026-09-13T10:00:00Z", "actionable": True}
NAME = "triage_contest_event"


class ScriptedModel(Model):
    def __init__(self, calls, stop="tool_use", failure=None):
        self.calls = calls
        self.stop = stop
        self.failure = failure
        self.invocations = 0
        self.exposed = []

    def update_config(self, **kwargs):
        pass

    def get_config(self):
        return {"model_id": "scripted-test"}

    async def structured_output(self, *args, **kwargs):
        raise NotImplementedError
        yield

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs):
        self.invocations += 1
        self.exposed = [spec["name"] for spec in tool_specs]
        if self.failure:
            raise self.failure
        yield {"messageStart": {"role": "assistant"}}
        for index, (name, arguments) in enumerate(self.calls):
            yield {"contentBlockStart": {"contentBlockIndex": index, "start": {
                "toolUse": {"toolUseId": str(index), "name": name}}}}
            yield {"contentBlockDelta": {"contentBlockIndex": index, "delta": {
                "toolUse": {"input": json.dumps(arguments)}}}}
            yield {"contentBlockStop": {"contentBlockIndex": index}}
        yield {"messageStop": {"stopReason": self.stop}}
        yield {"metadata": {"usage": {"inputTokens": 10, "outputTokens": 10, "totalTokens": 20},
                            "metrics": {"latencyMs": 1}}}


def invoke(model, store, name=NAME, arguments=None):
    return asyncio.run(run_guarded_request(model, store, name,
                                           EVENT if arguments is None else arguments))


def test_valid_tool_runs_once_without_model_continuation():
    model = ScriptedModel([(NAME, EVENT)])
    store = EventStore()
    result = invoke(model, store)
    assert result["status"] == "PASS"
    assert model.invocations == 1
    assert model.exposed == [NAME]
    assert result["completion_origin"] == "application_after_tools_hook"
    assert result["result"]["interrupt_human"] is True
    retry = invoke(ScriptedModel([(NAME, EVENT)]), store)
    assert retry["status"] == "PASS"
    assert retry["result"]["duplicate"] is True
    assert retry["result"]["exact_action"] is None
    metrics = invoke(ScriptedModel([("campaign_attention_metrics", {})]), store,
                     "campaign_attention_metrics", {})
    assert metrics["status"] == "PASS"
    assert metrics["result"]["unique_events"] == 1


@pytest.mark.parametrize("calls", [[(NAME, EVENT), (NAME, EVENT)],
                                  [("campaign_attention_metrics", {})],
                                  [(NAME, {**EVENT, "event_id": "changed"})]])
def test_bad_batch_is_rejected_before_any_ledger_mutation(calls):
    store = EventStore()
    model = ScriptedModel(calls)
    result = invoke(model, store)
    assert result["status"] == "FAIL"
    assert model.invocations == 1
    assert store.metrics()["unique_events"] == 0
    assert all(row["toolResult"]["status"] == "error"
               for row in result["trace"] if "toolResult" in row)


@pytest.mark.parametrize("stop", ["end_turn", "max_tokens"])
def test_no_tool_is_not_success(stop):
    store = EventStore()
    assert invoke(ScriptedModel([], stop=stop), store)["status"] == "FAIL"
    assert store.metrics()["unique_events"] == 0


@pytest.mark.parametrize("after_commit", [False, True])
def test_tool_failure_and_fresh_retry_preserve_ledger(monkeypatch, after_commit):
    store = EventStore()
    original_process = store.process

    def fail(event):
        if after_commit:
            original_process(event)
        raise RuntimeError("synthetic injected failure")

    monkeypatch.setattr(store, "process", fail)
    failed = invoke(ScriptedModel([(NAME, EVENT)]), store)
    assert failed["status"] == "FAIL"
    assert store.metrics()["unique_events"] == int(after_commit)
    monkeypatch.setattr(store, "process", original_process)
    recovered = invoke(ScriptedModel([(NAME, EVENT)]), store)
    assert recovered["status"] == "PASS"
    assert recovered["result"]["duplicate"] is after_commit
    assert recovered["result"]["interrupt_human"] is (not after_commit)
    assert store.metrics()["human_interruptions"] == 1


def test_provider_failure_is_visible_and_fresh_request_can_recover():
    store = EventStore()
    result = invoke(ScriptedModel([], failure=RuntimeError("synthetic provider failure")), store)
    assert result["status"] == "FAIL"
    assert result["failure"] == "RuntimeError"
    assert store.metrics()["unique_events"] == 0
    assert invoke(ScriptedModel([(NAME, EVENT)]), store)["status"] == "PASS"


@pytest.mark.parametrize("change", ["decision", "action", "boolean", "duplicate"])
def test_success_status_with_wrong_payload_is_rejected(monkeypatch, change):
    store = EventStore()
    classification, duplicate = store.preview(Event(**EVENT))
    values = classification.to_dict()
    if change == "decision":
        values["decision"] = "IGNORE"
    elif change == "action":
        values["exact_action"] = "Invented action"
    elif change == "boolean":
        values["interrupt_human"] = 1
    else:
        duplicate = True
    altered = Classification(Decision(values["decision"]), values["reason"],
                             values["exact_action"], values["interrupt_human"])
    monkeypatch.setattr(store, "process", lambda event: (altered, duplicate))
    result = invoke(ScriptedModel([(NAME, EVENT)]), store)
    assert result["status"] == "FAIL"
    assert result["result"] is None


@pytest.mark.parametrize("bad", [{}, {"unique_events": 99}])
def test_invalid_metrics_are_rejected(monkeypatch, bad):
    store = EventStore()
    good = store.metrics()
    calls = iter([good, bad])
    monkeypatch.setattr(store, "metrics", lambda: next(calls))
    result = invoke(ScriptedModel([("campaign_attention_metrics", {})]), store,
                    "campaign_attention_metrics", {})
    assert result["status"] == "FAIL"
    assert result["result"] is None


def test_tool_bearing_max_tokens_cannot_mutate_ledger():
    store = EventStore()
    result = invoke(ScriptedModel([(NAME, EVENT)], stop="max_tokens"), store)
    assert result["status"] == "FAIL"
    assert store.metrics()["unique_events"] == 0


def test_timeout_then_fresh_request():
    class SlowModel(ScriptedModel):
        async def stream(self, *args, **kwargs):
            await asyncio.sleep(1)
            async for event in super().stream(*args, **kwargs):
                yield event

    store = EventStore()
    result = asyncio.run(run_guarded_request(SlowModel([(NAME, EVENT)]), store, NAME,
                                              EVENT, timeout=0.01))
    assert result["status"] == "FAIL"
    assert result["failure"] == "TimeoutError"
    assert store.metrics()["unique_events"] == 0
    assert invoke(ScriptedModel([(NAME, EVENT)]), store)["status"] == "PASS"
