#!/usr/bin/env python3
"""Suggest documentation files that likely belong in docs/archive/."""

from __future__ import annotations

import argparse

from docs_common import ROOT, markdown_files, relpath, report_path


CANDIDATES = {
    "SESSION_SUMMARY.md",
    "HOMEWORK-001.md",
    "HOMEWORK-002.md",
    "LABOR_PLAN.md",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    present = [
        relpath(path)
        for path in markdown_files()
        if path.relative_to(ROOT).as_posix() in CANDIDATES
    ]

    lines = ["# Archive Candidates", ""]
    if present:
        lines.append("These files still appear active-side and likely belong in `docs/archive/`:")
        lines.append("")
        lines.extend(f"- {item}" for item in present)
    else:
        lines.append("No known archive candidates remain in the active documentation paths.")
    report = "\n".join(lines).rstrip() + "\n"
    print(report.rstrip())
    if args.write_report:
        path = report_path("archive-audit.md")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
        print(f"\nWrote report to {relpath(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
