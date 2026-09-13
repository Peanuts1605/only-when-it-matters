"""Evaluate the guarded workflow once with a verified preinstalled loopback model."""

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from verify_local_model import phase_passes

from only_when_it_matters.guarded import run_guarded_request
from only_when_it_matters.store import EventStore

EVENT = {"event_id": "guarded-local-1", "contest": "Fictional proof contest",
         "kind": "organizer_request", "sender": "organizer@example.test",
         "subject": "Add a demo disclosure", "received_at": "2026-09-13T16:00:00Z",
         "actionable": True}


async def evaluate():
    from strands.models.ollama import OllamaModel

    model = OllamaModel(host="http://127.0.0.1:11435", model_id="qwen3:4b",
                        max_tokens=2048, temperature=0, options={"num_ctx": 8192},
                        additional_args={"think": False},
                        ollama_client_args={"timeout": 45}, keep_alive="1m")
    store = EventStore()
    phases = []
    for name, arguments, duplicate in [
        ("triage_contest_event", EVENT, False),
        ("triage_contest_event", EVENT, True),
        ("campaign_attention_metrics", {}, None),
    ]:
        outcome = await run_guarded_request(model, store, name, arguments)
        strict_pass = outcome["status"] == "PASS" and phase_passes(
            outcome["trace"], name, EVENT, duplicate, outcome["stop_reason"])
        phases.append({"tool": name, "strict_pass": strict_pass, **outcome})
        print(f"{name}: {'PASS' if strict_pass else 'FAIL'}", flush=True)
        if not strict_pass:
            break
    status = "PASS" if len(phases) == 3 and all(p["strict_pass"] for p in phases) else "FAIL"
    return {"status": status, "checked_at": datetime.now(UTC).isoformat(),
            "model": "qwen3:4b", "provider": "local Ollama / Strands 1.54.0",
            "completion_origin": "application_after_tools_hook", "phases": phases,
            "metrics": store.metrics(), "fictional_data_only": True,
            "notification_delivery": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    outcome = asyncio.run(evaluate())
    args.output.write_text(json.dumps(outcome, indent=2) + "\n")
    print(f"Strict guarded sequence: {outcome['status']}")
    if outcome["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
