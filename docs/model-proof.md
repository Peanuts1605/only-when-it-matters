# Local Strands model proof — September 13, 2026

Status: **PARTIAL EXECUTION PROOF; STRICT SEQUENCE FAIL**.

Environment: Strands Agents SDK 1.54.0, installed Ollama 0.32.15, preinstalled local
qwen3:4b (catalog digest prefix 359d7dd4bcda), loopback port 11435. The temporary
server was started with cloud disabled and pruning disabled. No model download,
paid inference, real mailbox, external message or contest submission was involved.

## Reproduced and repaired

The first run selected both registered tools, but SQLite rejected execution from
Strands worker threads. The shared connection now permits thread use and an RLock
serializes lookup, classification, insert/commit and metrics queries. A regression
test invokes the real SDK `.stream()` wrapper with twelve concurrent deliveries:
one actionable original, eleven quiet duplicates, one saved escalation.

## Actual repaired model run

Input: fictional organizer_request, event ID local-model-organizer-1, subject
Add a demo disclosure, organizer@example.test, actionable true.

1. The model selected `triage_contest_event` with the supplied fields unchanged.
   Execution succeeded: ESCALATE, duplicate false, interrupt_human true, exact action
   Respond to the organizer requirement in: Add a demo disclosure. Normal end_turn.
2. Asked to process that same event once again, the model called the triage tool
   **twice**, with the unchanged event. Both succeeded: RECORD, duplicate true,
   interrupt_human false, exact_action null. Normal end_turn.
3. The strict checker rejected the extra call and exited nonzero. The final model-driven
   metrics phase was not run. Direct final ledger read: one unique event, one escalation,
   zero unique quiet decisions. No repeated interruption flag escaped.

This proves a real model-to-Strands-to-tool-to-SQLite path, not reliable adherence to
an exact tool-call count. It does not prove notification delivery, live source validation,
safe arbitrary model prose, complete failure recovery, or contest readiness.

## Reproduction and acceptance

`scripts/verify_local_model.py` uses an isolated temporary ledger and accepts only
the pinned model name and a loopback endpoint. The operator must independently verify
the local model contents and cloud-disabled server; an alias alone is not locality proof.
Ollama provider dependencies must already be installed. No automatic installation occurs.

The current validator requires three normally completed phases, exactly one matching
tool use/result per phase, unchanged input, exact original/retry action and decision,
and the full expected metrics object. Timeouts, limits, errors, altered inputs, extra
calls and wrong actions fail. Synthetic acceptance tests do not call a model.

The repaired run above preceded the additional stop-reason/decision/action validator
checks; its normal stop reasons and exact results were inspected directly. Its extra
retry still fails the stricter checker. No re-run is claimed for that validator-only change.

Invocation limits bound the awaiting coroutine, not guaranteed termination of underlying
worker-thread/provider computation. Stop the temporary server after a bounded run.
