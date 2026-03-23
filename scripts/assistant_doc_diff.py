#!/usr/bin/env python3
"""Check whether AI guidance mirrors still agree on core documentation rules."""

from __future__ import annotations

import argparse

from docs_common import AI_GUIDE_FILES, ROOT, format_section, read_text, relpath, report_path

REQUIRED_TERMS = [
    "INBOX.md",
    "VISION.md",
    "DECISIONS_INBOX.md",
    "MILESTONES_INBOX.md",
    "CHARTER.md",
    "DECISIONS.md",
    "MILESTONES.md",
    "KNOWLEDGE-PIPELINE.md",
]


def run_check() -> tuple[list[str], str]:
    warnings: list[str] = []
    for path in AI_GUIDE_FILES:
        if not path.exists():
            warnings.append(f"Missing AI guidance file: `{relpath(path)}`.")
            continue
        text = read_text(path)
        for term in REQUIRED_TERMS:
            if term not in text:
                warnings.append(f"`{relpath(path)}` is missing `{term}`.")

    report = ["# Assistant Guidance Check", "", format_section("Warnings", warnings)]
    if not warnings:
        report.append("AI guidance mirrors all contain the expected documentation pipeline terms.\n")
    return warnings, "\n".join(report).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    warnings, report = run_check()
    print(report.rstrip())
    if args.write_report:
        path = report_path("assistant-doc-check.md")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
        print(f"\nWrote report to {relpath(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
