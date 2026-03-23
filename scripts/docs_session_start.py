#!/usr/bin/env python3
"""Print documentation review feedback for make start-session."""

from __future__ import annotations

from docs_common import PRIORITY_REVIEW_DOCS, ROOT, branch_changed_markdown, read_text, relpath, working_tree_changed_markdown
from knowledge_pipeline_check import run_check as pipeline_check


def has_unprocessed_inbox() -> bool:
    path = ROOT / "INBOX.md"
    if not path.exists():
        return False
    text = read_text(path)
    marker = "## Unprocessed Items"
    if marker not in text:
        return False
    return bool(text.split(marker, 1)[1].strip())


def has_pending_items(path) -> bool:
    if not path.exists():
        return False
    text = read_text(path)
    return "- [ ]" in text or "* **DEC-" in text or "### Target:" in text


def main() -> int:
    branch_changed = branch_changed_markdown()
    working_changed = working_tree_changed_markdown()
    warnings, _ = pipeline_check()

    print("[docs] Review queue")
    reasons: dict[str, list[str]] = {}

    def add_reason(path: str, reason: str) -> None:
        reasons.setdefault(path, [])
        if reason not in reasons[path]:
            reasons[path].append(reason)

    if has_unprocessed_inbox():
        add_reason("INBOX.md", "unprocessed content present")
    if has_pending_items(ROOT / "DECISIONS_INBOX.md"):
        add_reason("DECISIONS_INBOX.md", "pending decision drafts present")
    if has_pending_items(ROOT / "MILESTONES_INBOX.md"):
        add_reason("MILESTONES_INBOX.md", "draft milestone sequencing present")

    for path in PRIORITY_REVIEW_DOCS:
        rel = relpath(path)
        if rel in working_changed:
            add_reason(rel, "locally modified")
        elif rel in branch_changed:
            add_reason(rel, "changed on current branch")

    for rel in [
        "CHARTER.md",
        "DECISIONS.md",
        "MILESTONES.md",
        "README.md",
        "WORKFLOW.md",
        "AGENTS.md",
        "CLAUDE.md",
        "GEMINI.md",
        ".github/copilot-instructions.md",
        "KNOWLEDGE-PIPELINE.md",
    ]:
        if rel in working_changed:
            add_reason(rel, "locally modified")
        elif rel in branch_changed:
            add_reason(rel, "changed on current branch")

    if warnings:
        add_reason("KNOWLEDGE-PIPELINE.md", "pipeline guide may be stale")

    if reasons:
        for path, items in reasons.items():
            print(f"[docs] - {path}: {', '.join(items)}")
    else:
        print("[docs] No priority documentation review items detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
