"""Acceptance checks do not invoke any model, network, or live ledger."""

import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "model_proof", Path(__file__).parents[1] / "scripts" / "verify_local_model.py"
)
proof = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proof)


def trace_for(payload, event):
    return [
        {"toolUse": {"name": "triage_contest_event", "input": event, "toolUseId": "1"}},
        {"toolResult": {"toolUseId": "1", "status": "success",
                        "content": [{"text": json.dumps(payload)}]}},
    ]


def test_original_and_retry_proof_require_exact_tool_results():
    event = {"event_id": "fictional", "subject": "Add a disclosure"}
    original = {"duplicate": False, "interrupt_human": True, "decision": "ESCALATE",
                "exact_action": "Respond to the organizer requirement in: Add a disclosure"}
    retry = {"duplicate": True, "interrupt_human": False, "exact_action": None,
             "decision": "RECORD"}
    assert proof.phase_passes(trace_for(original, event), "triage_contest_event", event, False)
    assert proof.phase_passes(trace_for(retry, event), "triage_contest_event", event, True)


@pytest.mark.parametrize("defect", ["missing", "error", "wrong_input", "wrong_id", "repeat",
                                  "wrong_decision", "wrong_action", "limit_output_tokens"])
def test_incomplete_or_false_model_proof_is_rejected(defect):
    event = {"event_id": "fictional", "subject": "Add a disclosure"}
    trace = trace_for({"duplicate": False, "interrupt_human": True,
                       "decision": "ESCALATE",
                       "exact_action": "Respond to the organizer requirement in: Add a disclosure"},
                      event.copy())
    stop_reason = "end_turn"
    if defect == "missing":
        trace.pop()
    elif defect == "error":
        trace[1]["toolResult"]["status"] = "error"
    elif defect == "wrong_input":
        trace[0]["toolUse"]["input"]["event_id"] = "invented"
    elif defect == "wrong_id":
        trace[1]["toolResult"]["toolUseId"] = "unpaired"
    elif defect == "repeat":
        trace += deepcopy(trace)
    elif defect in {"wrong_decision", "wrong_action"}:
        payload = json.loads(trace[1]["toolResult"]["content"][0]["text"])
        payload["decision" if defect == "wrong_decision" else "exact_action"] = "invented"
        trace[1]["toolResult"]["content"][0]["text"] = json.dumps(payload)
    else:
        stop_reason = defect
    assert not proof.phase_passes(trace, "triage_contest_event", event, False, stop_reason)
