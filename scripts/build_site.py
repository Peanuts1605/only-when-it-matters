from __future__ import annotations

import json
from pathlib import Path

from only_when_it_matters.cli import run_scenario

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    report = run_scenario(ROOT / "tests" / "fixtures.json")
    destination = ROOT / "site" / "report.json"
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Built {destination.relative_to(ROOT)} from the Strands tool policy.")


if __name__ == "__main__":
    main()

