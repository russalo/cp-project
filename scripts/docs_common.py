#!/usr/bin/env python3
"""Shared helpers for documentation maintenance scripts."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PIPELINE_DOCS = [
    "INBOX.md",
    "VISION.md",
    "DECISIONS_INBOX.md",
    "MILESTONES_INBOX.md",
    "CHARTER.md",
    "DECISIONS.md",
    "MILESTONES.md",
    "KNOWLEDGE-PIPELINE.md",
]

PIPELINE_DOC_PATHS = [ROOT / name for name in PIPELINE_DOCS]
PRIORITY_REVIEW_DOCS = [
    ROOT / "INBOX.md",
    ROOT / "DECISIONS_INBOX.md",
    ROOT / "MILESTONES_INBOX.md",
    ROOT / "DEV-SESSION.md",
]
AI_GUIDE_FILES = [
    ROOT / "AGENTS.md",
    ROOT / "CLAUDE.md",
    ROOT / "GEMINI.md",
    ROOT / ".github" / "copilot-instructions.md",
]

SKIP_PARTS = {"node_modules", ".venv", ".pytest_cache", "__pycache__", ".git"}
DECISION_ID_PATTERN = re.compile(r"\bDEC-(\d{3})\b")
MAKE_TARGET_PATTERN = re.compile(r"`make ([a-z0-9-]+)`")


def relpath(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def markdown_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*.md"):
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def git_lines(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def merge_base_main() -> str | None:
    lines = git_lines("merge-base", "main", "HEAD")
    return lines[0] if lines else None


def branch_changed_markdown() -> set[str]:
    base = merge_base_main()
    if not base:
        return set()
    return set(git_lines("diff", "--name-only", f"{base}..HEAD", "--", "*.md", "*.MD"))


def working_tree_changed_markdown() -> set[str]:
    changed: set[str] = set()
    for line in git_lines("status", "--porcelain", "--", "*.md", "*.MD"):
        if len(line) > 3:
            changed.add(line[3:].strip())
    return changed


def changed_markdown_union() -> set[str]:
    return branch_changed_markdown() | working_tree_changed_markdown()


def decision_ids(text: str) -> list[str]:
    return [f"DEC-{match}" for match in DECISION_ID_PATTERN.findall(text)]


def extract_headings(text: str, limit: int = 5) -> list[str]:
    headings = [line.strip("# ").strip() for line in text.splitlines() if line.startswith("#")]
    return headings[:limit]


def report_path(name: str) -> Path:
    return ROOT / "docs" / "reports" / name


def format_section(title: str, items: list[str]) -> str:
    lines = [f"## {title}", ""]
    if not items:
        lines.append("- None")
    else:
        lines.extend(f"- {item}" for item in items)
    lines.append("")
    return "\n".join(lines)

