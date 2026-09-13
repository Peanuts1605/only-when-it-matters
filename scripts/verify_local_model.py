"""Bounded real-model tool-use probe; only a preinstalled loopback Ollama model is used."""

import argparse
import asyncio
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

MODEL_ID = "qwen3:4b"


def phase_passes(trace, tool_name, event, duplicate=None, stop_reason="end_turn"):
    if stop_reason != "end_turn":
        return False
    uses = [entry["toolUse"] for entry in trace if "toolUse" in entry]
    results = [entry["toolResult"] for entry in trace if "toolResult" in entry]
    if len(uses) != 1 or len(results) != 1:
        return False
    use, result = uses[0], results[0]
    if (use["name"] != tool_name or result["toolUseId"] != use["toolUseId"]
            or result["status"] != "success"):
        return False
    try:
        payload = json.loads(result["content"][0]["text"])
        if tool_name == "triage_contest_event":
            return (use["input"] == event and payload["duplicate"] is duplicate
                    and payload["interrupt_human"] is (not duplicate)
                    and payload["decision"] == ("RECORD" if duplicate else "ESCALATE")
                    and payload["exact_action"] == (None if duplicate else
                         f"Respond to the organizer requirement in: {event['subject']}"))
        return use["input"] == {} and payload == {
            "unique_events": 1, "human_interruptions": 1,
            "interruptions_avoided": 0, "avoidance_rate": 0.0,
        }
    except (KeyError, IndexError, TypeError, ValueError):
        return False


async def probe(host: str, model_id: str) -> dict:
    from strands.models.ollama import OllamaModel

    if urlparse(host).hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("This proof runner accepts loopback hosts only.")
    if model_id != MODEL_ID:
        raise ValueError("Only the verified preinstalled qwen3:4b model is allowed.")
    # Import the application only after changing into an isolated temporary directory.
    from only_when_it_matters.agent import build_agent
    from only_when_it_matters.tools import _store

    model = OllamaModel(
        host=host,
        model_id=model_id,
        max_tokens=2048,
        temperature=0,
        options={"num_ctx": 8192},
        additional_args={"think": False},
        ollama_client_args={"timeout": 45},
        keep_alive="1m",
    )
    agent = build_agent(model)
    event = {
        "event_id": "local-model-organizer-1",
        "contest": "Fictional proof contest",
        "kind": "organizer_request",
        "sender": "organizer@example.test",
        "subject": "Add a demo disclosure",
        "received_at": "2026-09-13T10:00:00Z",
        "actionable": True,
    }
    stop_reasons = []
    phases = []
    failure = None
    for instruction, tool_name, duplicate in (
        ("Process this one fictional event using ONLY your triage tool once. "
        "Do not invent or change any event fields. No message is sent. Event: " + json.dumps(event),
         "triage_contest_event", False),
        ("Process the exact same event again using ONLY the triage tool once. "
         "This is a delivery retry with the same event ID, not a new event. Event: "
         + json.dumps(event), "triage_contest_event", True),
        ("Fetch campaign_attention_metrics once, with no other tool calls.",
         "campaign_attention_metrics", None),
    ):
        start = len(agent.messages)
        try:
            result = await asyncio.wait_for(
                agent.invoke_async(instruction, limits={"turns": 3, "output_tokens": 4000}),
                timeout=90,
            )
            stop_reasons.append(result.stop_reason)
        except Exception as error:  # noqa: BLE001 -- record a redacted FAIL receipt, never PASS
            failure = type(error).__name__
        phase_trace = []
        for message in agent.messages[start:]:
            for content in message["content"]:
                for key in ("toolUse", "toolResult"):
                    if key in content:
                        phase_trace.append({key: content[key]})
        passed = failure is None and phase_passes(
            phase_trace, tool_name, event, duplicate, result.stop_reason
        )
        phases.append({"tool": tool_name, "passed": passed, "trace": phase_trace})
        if not passed:
            failure = failure or "ToolAcceptanceFailed"
            break
    # Keep only tool inputs/results. Do not publish hidden reasoning or whole conversations.
    trace = []
    for message in agent.messages:
        for content in message["content"]:
            for key in ("toolUse", "toolResult"):
                if key in content:
                    trace.append({key: content[key]})
    return {
        "checked_at": datetime.now(UTC).isoformat(),
        "model": model_id,
        "provider": "local Ollama via real Strands Agent",
        "fictional_data_only": True,
        "trace": trace,
        "metrics": _store.metrics(),
        "notification_delivery": False,
        "stop_reasons": stop_reasons,
        "failure": failure,
        "phases": phases,
        "status": "PASS" if failure is None and len(phases) == 3 else "FAIL",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="http://127.0.0.1:11435")
    parser.add_argument("--model", default=MODEL_ID, choices=[MODEL_ID])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    previous = Path.cwd()
    try:
        with tempfile.TemporaryDirectory(prefix="owim-model-proof-") as temporary:
            os.chdir(temporary)
            result = asyncio.run(probe(args.host, args.model))
    finally:
        os.chdir(previous)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Captured real-model tool trace: {output}")
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
