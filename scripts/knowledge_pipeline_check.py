#!/usr/bin/env python3
"""Check whether KNOWLEDGE-PIPELINE.md still matches the repo's documentation structure."""

from __future__ import annotations

import argparse
import re

from docs_common import (
    AI_GUIDE_FILES,
    PIPELINE_DOCS,
    ROOT,
    changed_markdown_union,
    format_section,
    read_text,
    relpath,
    report_path,
)

EXPECTED_FILES = [
    *PIPELINE_DOCS,
    "docs/reference/ai-guidance.md",
    "docs/archive/",
    "docs/archive/homework/",
]
EXPECTED_MAKE_TARGETS = {
    "docs-audit",
    "knowledge-pipeline-check",
    "inbox-status",
    "inbox-route-draft",
    "archive-audit",
    "assistant-doc-check",
}


def run_check() -> tuple[list[str], str]:
    warnings: list[str] = []
    kp_path = ROOT / "KNOWLEDGE-PIPELINE.md"
    if not kp_path.exists():
        warnings.append("`KNOWLEDGE-PIPELINE.md` is missing.")
        return warnings, format_section("Warnings", warnings)

    text = read_text(kp_path)

    for rel in EXPECTED_FILES:
        target = ROOT / rel
        if not target.exists():
            warnings.append(f"Expected pipeline path missing: `{rel}`.")
        elif rel not in text:
            warnings.append(f"`KNOWLEDGE-PIPELINE.md` does not mention `{rel}`.")

    documented_targets = set(re.findall(r"`make ([a-z0-9-]+)`", text))
    for target in EXPECTED_MAKE_TARGETS:
        if target not in documented_targets:
            warnings.append(f"`KNOWLEDGE-PIPELINE.md` does not document `make {target}`.")

    changed = changed_markdown_union()
    pipeline_related = {
        name
        for name in changed
        if name in PIPELINE_DOCS
        or name.startswith("docs/reference/")
        or name.startswith(".github/copilot")
        or name in {"AGENTS.md", "CLAUDE.md", "GEMINI.md"}
    }
    if pipeline_related and "KNOWLEDGE-PIPELINE.md" not in changed:
        warnings.append(
            "Pipeline-related docs changed without updating `KNOWLEDGE-PIPELINE.md`."
        )

    for path in AI_GUIDE_FILES:
        if not path.exists():
            warnings.append(f"AI guidance mirror missing: `{relpath(path)}`.")

    report = []
    report.append("# Knowledge Pipeline Check")
    report.append("")
    report.append(format_section("Warnings", warnings))
    if not warnings:
        report.append("Pipeline guide is aligned with the current repository structure.\n")
    return warnings, "\n".join(report).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    warnings, report = run_check()
    print(report.rstrip())
    if args.write_report:
        report_file = report_path("knowledge-pipeline-check.md")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(report, encoding="utf-8")
        print(f"\nWrote report to {relpath(report_file)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
