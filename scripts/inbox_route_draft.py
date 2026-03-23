#!/usr/bin/env python3
"""Generate a routing draft for INBOX.md items."""

from __future__ import annotations

import argparse

from docs_common import ROOT, read_text, relpath, report_path


def inbox_items() -> list[str]:
    path = ROOT / "INBOX.md"
    if not path.exists():
        return []
    text = read_text(path)
    marker = "## Unprocessed Items"
    if marker not in text:
        return []
    section = text.split(marker, 1)[1]
    return [line.strip() for line in section.splitlines() if line.strip()]


def destination(item: str) -> str:
    lower = item.lower()
    if any(word in lower for word in ["dec-", "decision", "proposed", "choose", "api", "idempotency"]):
        return "DECISIONS_INBOX.md"
    if any(word in lower for word in ["milestone", "phase", "sequence", "roadmap", "target:"]):
        return "MILESTONES_INBOX.md"
    if any(word in lower for word in ["vision", "future", "later", "long-term", "field ui", "dashboard"]):
        return "VISION.md"
    if any(word in lower for word in ["rule", "constraint", "must", "scope", "active"]):
        return "CHARTER.md"
    return "Needs manual review"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    items = inbox_items()
    lines = ["# Inbox Routing Draft", ""]
    if not items:
        lines.append("No unprocessed inbox items found.")
    else:
        for item in items:
            lines.append(f"- `{destination(item)}`: {item}")
    report = "\n".join(lines).rstrip() + "\n"
    print(report.rstrip())
    if args.write_report:
        path = report_path("inbox-route-draft.md")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
        print(f"\nWrote report to {relpath(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
