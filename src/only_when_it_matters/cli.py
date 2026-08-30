from __future__ import annotations

import argparse
import json
from pathlib import Path

from .policy import Event
from .store import EventStore


def run_scenario(path: Path, database: Path | str = ":memory:") -> dict[str, object]:
    store = EventStore(database)
    outcomes = []
    for raw in json.loads(path.read_text()):
        classification, duplicate = store.process(Event(**raw))
        outcomes.append(
            {
                "event_id": raw["event_id"],
                "contest": raw["contest"],
                **classification.to_dict(),
                "duplicate": duplicate,
            }
        )
    return {"outcomes": outcomes, "metrics": store.metrics()}


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay the judge-visible attention boundary.")
    parser.add_argument("scenario", type=Path)
    parser.add_argument("--database", type=Path, default=Path(":memory:"))
    args = parser.parse_args()
    print(json.dumps(run_scenario(args.scenario, args.database), indent=2))


if __name__ == "__main__":
    main()

