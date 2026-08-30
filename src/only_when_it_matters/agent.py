from __future__ import annotations

from strands import Agent

from .tools import campaign_attention_metrics, triage_contest_event

SYSTEM_PROMPT = """
You protect a contest operator's attention. Use the deterministic tools before writing any
recommendation. Never interrupt a human for marketing, duplicates, routine receipts, or status
noise. Escalate only a concrete deadline, organizer request, eligibility action, acceptance,
rejection, or verified win. Preserve the tool's exact action and never claim a submission or win
without provider evidence.
""".strip()


def build_agent(model=None) -> Agent:
    """Build the contest's required Strands agent with an injectable model provider."""
    kwargs = {"system_prompt": SYSTEM_PROMPT, "tools": [triage_contest_event, campaign_attention_metrics]}
    if model is not None:
        kwargs["model"] = model
    return Agent(**kwargs)

