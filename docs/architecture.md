# Architecture and trust boundaries

As implemented September 13, 2026. The PDF in `site/architecture.pdf` is the portable judge artifact.

## Plain explanation

Contest operators need fewer repeated demands on their attention. This prototype processes fictional
events, saves each first decision in SQLite, and returns one suggested action when its rules choose
escalation. When an event ID repeats, its original record stays unchanged and the new delivery returns
no action. The public page displays a generated fixture report, not a live agent session. A separate
Strands agent registers triage and metrics tools. Real local-model triage execution is demonstrated,
but the strict sequence failed after the model called the retry tool twice; final model-driven metrics
were not reached. Counts describe policy decisions, not messages delivered or time saved.

Assumptions: event labels and IDs are trusted; one local process owns the ledger. Falsifier: any
replayed ID returns an actionable interruption, or the demo is described as a live model run.

## Implemented paths

1. `tests/fixtures.json` → `cli.run_scenario` → `EventStore.process` → `classify_event` only for a new ID.
2. The first decision is persisted in SQLite. Duplicate IDs skip classification and return a quiet
   delivery result. Metrics read only first decisions, so replay does not change the denominator.
3. `scripts/build_site.py` creates `site/report.json`; the static browser page fetches and displays it.
   The Replay button fetches this same report again. It is not a backend invocation or database mutation.
4. Separately, `agent.build_agent(model=...)` constructs a Strands agent exposing decorated
   `triage_contest_event` and `campaign_attention_metrics`. Direct decorated-tool invocation is tested;
   actual SDK worker-thread execution is also tested. Local Qwen successfully selected/executed triage;
   complete sequence reliability, provider recovery and final model prose remain unverified.

## Retry invariants and acceptance

- Original persisted event and decision bytes remain unchanged across duplicate replay.
- Duplicate result: `decision=RECORD`, `duplicate=true`, `interrupt_human=false`, `exact_action=null`.
- Reopening the same database preserves this suppression.
- Original unique-event escalation count remains available for audit; it does not increment on retry.
- The public duplicate pill says QUIET REPLAY, while first escalation rows say HUMAN NEEDED.

An RLock protects all database operations for worker threads sharing one EventStore. It covers
duplicate lookup through commit, not merely the INSERT. This repairs the SQLite thread-affinity
failure found by a real Strands run. Twelve concurrent SDK-wrapper retries produce one action.

Scope excludes coordination between separate store instances/processes, content-change detection for a reused ID, actual notification
delivery, external sender/winner verification, and overdue-event policy validation. A retry after an
unobserved first response returns quiet; this is not a transactional exactly-once notification system.
Inputs supplied by an unconstrained model would need independent source validation before live use.

## Metrics

The fixture has four unique events, two quiet decisions and two escalation decisions. A fifth
delivery is a duplicate, not another unique event. Existing JSON names are retained for compatibility:
`human_interruptions` means unique escalation decisions; `interruptions_avoided` means unique quiet
decisions. No real-world productivity or delivery claim follows from the fixture's 50% rate.

## Rebuild the PDF

Run `python scripts/build_architecture.py` with ReportLab installed. Application execution does not
need ReportLab. The generator uses built-in fonts and local code only, with no external images or data.
