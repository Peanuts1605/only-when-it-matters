"""One model-selected tool batch, validated before execution; no model final prose."""

from __future__ import annotations

import asyncio
import json
from copy import deepcopy

from strands import Agent, tool
from strands.hooks import AfterToolsEvent, BeforeToolsEvent

from .policy import Event
from .store import EventStore


def make_bound_tools(store: EventStore):
    @tool
    def triage_contest_event(event_id: str, contest: str, kind: str, sender: str,
                             subject: str, received_at: str, actionable: bool = False,
                             deadline_at: str | None = None) -> dict:
        """Classify one event and save its first decision; repeated IDs return no action."""
        classification, duplicate = store.process(Event(
            event_id=event_id, contest=contest, kind=kind, sender=sender,
            subject=subject, received_at=received_at, actionable=actionable,
            deadline_at=deadline_at))
        return {**classification.to_dict(), "duplicate": duplicate}

    @tool
    def campaign_attention_metrics() -> dict:
        """Return unique-event policy counts from the ledger, not delivered notifications."""
        return store.metrics()

    return {item.tool_name: item for item in (triage_contest_event, campaign_attention_metrics)}


class SingleBatchGate:
    def __init__(self, tool_name: str, arguments: dict, expected_result: dict):
        self.tool_name = tool_name
        self.arguments = deepcopy(arguments)
        self.expected_result = deepcopy(expected_result)
        self.proposed = []
        self.results = []
        self.payload = None
        self.accepted = False
        self.rejection = None

    def before(self, event: BeforeToolsEvent):
        self.proposed = [deepcopy(block["toolUse"]) for block in event.message["content"]
                         if "toolUse" in block]
        if (len(self.proposed) != 1 or self.proposed[0].get("name") != self.tool_name
                or json.dumps(self.proposed[0].get("input"), sort_keys=True)
                != json.dumps(self.arguments, sort_keys=True)):
            self.rejection = "Unexpected tool batch or changed input; nothing executed."
            event.cancel = self.rejection

    def after(self, event: AfterToolsEvent):
        self.results = [deepcopy(block["toolResult"]) for block in event.message["content"]
                        if "toolResult" in block]
        if not self.rejection and len(self.results) == 1:
            result = self.results[0]
            if (result.get("status") == "success"
                    and result.get("toolUseId") == self.proposed[0].get("toolUseId")):
                try:
                    self.payload = json.loads(result["content"][0]["text"])
                    self.accepted = (isinstance(self.payload, dict)
                                     and json.dumps(self.payload, sort_keys=True)
                                     == json.dumps(self.expected_result, sort_keys=True))
                except (KeyError, IndexError, TypeError, ValueError):
                    self.rejection = "Invalid tool result."
        if not self.accepted:
            self.rejection = self.rejection or "Tool execution failed; result not accepted."
        event.end_turn = json.dumps({
            "status": "PASS" if self.accepted else "FAIL",
            "result": self.payload if self.accepted else None,
            "failure": self.rejection,
            "completion_origin": "application_after_tools_hook",
        }, sort_keys=True)


async def run_guarded_request(model, store: EventStore, tool_name: str, arguments: dict,
                              timeout: float = 90) -> dict:
    """Fresh context per request, shared caller-owned ledger, one validated batch."""
    tools = make_bound_tools(store)
    if tool_name not in tools:
        raise ValueError("Unsupported request tool.")
    if tool_name == "triage_contest_event":
        classification, duplicate = store.preview(Event(**arguments))
        expected = {**classification.to_dict(), "duplicate": duplicate}
    else:
        expected = store.metrics()
    gate = SingleBatchGate(tool_name, arguments, expected)
    agent = Agent(model=model, tools=[tools[tool_name]], callback_handler=None,
                  system_prompt="Use the available tool exactly once with unchanged supplied JSON. "
                  "The application validates the call and returns its result. Do not add fields.")
    agent.add_hook(gate.before, BeforeToolsEvent)
    agent.add_hook(gate.after, AfterToolsEvent)
    failure = None
    stop_reason = None
    try:
        result = await asyncio.wait_for(agent.invoke_async(
            f"Call {tool_name} once. Arguments: {json.dumps(arguments, sort_keys=True)}",
            limits={"turns": 1, "output_tokens": 4000}), timeout=timeout)
        stop_reason = result.stop_reason
    except Exception as error:  # noqa: BLE001 -- redacted failure, no fallback success
        failure = type(error).__name__
    accepted = failure is None and stop_reason == "end_turn" and gate.accepted
    return {
        "status": "PASS" if accepted else "FAIL",
        "result": gate.payload if accepted else None,
        "failure": failure or gate.rejection or (None if accepted else "No accepted tool result"),
        "stop_reason": stop_reason,
        "completion_origin": "application_after_tools_hook" if gate.results else "none",
        "trace": [{"toolUse": use} for use in gate.proposed]
                 + [{"toolResult": value} for value in gate.results],
    }
