#!/usr/bin/env python3
"""Print documentation change feedback for make stop-session."""

from __future__ import annotations

from pathlib import Path

from docs_common import ROOT, extract_headings, relpath, working_tree_changed_markdown

PIPELINE_RELATED = {
    "INBOX.md",
    "VISION.md",
    "DECISIONS_INBOX.md",
    "MILESTONES_INBOX.md",
    "CHARTER.md",
    "DECISIONS.md",
    "MILESTONES.md",
    "README.md",
    "WORKFLOW.md",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".github/copilot-instructions.md",
    "docs/reference/ai-guidance.md",
}


def diff_numstat(path: str) -> str:
    import subprocess

    result = subprocess.run(
        ["git", "diff", "--numstat", "--", path],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    line = result.stdout.strip().splitlines()
    if line:
        parts = line[0].split("\t")
        if len(parts) >= 2:
            return f"+{parts[0]} / -{parts[1]}"
    if not (ROOT / path).exists():
        return "deleted"
    return "new or staged"


def main() -> int:
    changed = sorted(working_tree_changed_markdown())
    print("[docs] Documentation changes")
    if not changed:
        print("[docs] No documentation changes detected.")
        return 0

    for rel in changed:
        path = ROOT / rel
        headings = []
        if path.exists():
            headings = extract_headings(path.read_text(encoding="utf-8"), limit=2)
        heading_text = f" | headings: {', '.join(headings)}" if headings else ""
        print(f"[docs] - {rel}: {diff_numstat(rel)}{heading_text}")

    if any(rel in PIPELINE_RELATED for rel in changed) and "KNOWLEDGE-PIPELINE.md" not in changed:
        print("[docs] WARNING: pipeline-related docs changed without updating KNOWLEDGE-PIPELINE.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
