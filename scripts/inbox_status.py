#!/usr/bin/env python3
"""Report unprocessed content in INBOX.md."""

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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    items = inbox_items()
    lines = ["# Inbox Status", ""]
    if items:
        lines.append(f"Unprocessed inbox lines: {len(items)}")
        lines.append("")
        for item in items[:20]:
            lines.append(f"- {item}")
    else:
        lines.append("INBOX is currently empty or has no unprocessed items.")
    report = "\n".join(lines).rstrip() + "\n"
    print(report.rstrip())
    if args.write_report:
        path = report_path("inbox-status.md")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
        print(f"\nWrote report to {relpath(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
