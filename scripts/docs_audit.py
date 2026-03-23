#!/usr/bin/env python3
"""Run a combined documentation audit for the repo."""

from __future__ import annotations

import argparse
from collections import defaultdict

from assistant_doc_diff import run_check as assistant_check
from docs_common import ROOT, decision_ids, format_section, markdown_files, read_text, relpath, report_path
from knowledge_pipeline_check import run_check as pipeline_check

STALE_PATTERNS = [
    "HOMEWORK-001.md",
    "HOMEWORK-002.md",
    "SESSION_SUMMARY.md",
]


def duplicate_decision_ids() -> list[str]:
    locations: dict[str, list[str]] = defaultdict(list)
    for path in [ROOT / "DECISIONS.md", ROOT / "DECISIONS_INBOX.md"]:
        if not path.exists():
            continue
        for decision_id in sorted(set(decision_ids(read_text(path)))):
            locations[decision_id].append(relpath(path))
    return [
        f"{decision_id} appears in {', '.join(paths)}"
        for decision_id, paths in sorted(locations.items())
        if len(paths) > 1 and decision_id not in {"DEC-004", "DEC-005"}
    ]


def stale_references() -> list[str]:
    warnings: list[str] = []
    for path in markdown_files():
        rel = relpath(path)
        if rel.startswith("docs/archive/"):
            continue
        text = read_text(path)
        for pattern in STALE_PATTERNS:
            if pattern in text and f"docs/archive/" not in text:
                warnings.append(f"`{rel}` still references `{pattern}`.")
    return warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    duplicate_ids = duplicate_decision_ids()
    stale_refs = stale_references()
    pipeline_warnings, _ = pipeline_check()
    assistant_warnings, _ = assistant_check()

    lines = ["# Documentation Audit", ""]
    lines.append(format_section("Duplicate Decision IDs", duplicate_ids))
    lines.append(format_section("Stale References", stale_refs))
    lines.append(format_section("Knowledge Pipeline Warnings", pipeline_warnings))
    lines.append(format_section("AI Guidance Warnings", assistant_warnings))
    report = "\n".join(lines).rstrip() + "\n"
    print(report.rstrip())
    if args.write_report:
        path = report_path("docs-audit.md")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
        print(f"\nWrote report to {relpath(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
