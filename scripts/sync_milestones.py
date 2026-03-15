#!/usr/bin/env python3
"""Sync unchecked checklist items in MILESTONES.md into a PyCharm TODO file."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

CHECKBOX_RE = re.compile(r"^(?P<indent>\s*)- \[(?P<state>[ xX])] (?P<text>.+)$")


@dataclass
class MilestoneTodo:
    path: str


def parse_unchecked_items(markdown: str) -> list[MilestoneTodo]:
    items: list[MilestoneTodo] = []
    context_by_level: dict[int, str] = {}

    for raw_line in markdown.splitlines():
        match = CHECKBOX_RE.match(raw_line)
        if not match:
            continue

        indent = len(match.group("indent"))
        level = indent // 2
        text = match.group("text").strip()
        is_checked = match.group("state").lower() == "x"

        context_by_level[level] = text

        # Remove deeper stale context when indentation decreases.
        for stale_level in [k for k in context_by_level if k > level]:
            del context_by_level[stale_level]

        if is_checked:
            continue

        parents = [context_by_level[idx] for idx in sorted(context_by_level) if idx < level]
        path = " > ".join(parents + [text])
        items.append(MilestoneTodo(path=path))

    return items


def build_todo_markdown(items: list[MilestoneTodo], source_file: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    lines = [
        "# MILESTONES TODO",
        "",
        "Auto-generated from unchecked checklist items in `MILESTONES.md`.",
        f"Generated at: `{timestamp}`",
        "",
        "## Open milestone work",
        "",
    ]

    if not items:
        lines.append("No open milestone work.")
    else:
        for item in items:
            lines.append(f"- TODO(milestone): {item.path}")

    lines.extend(
        [
            "",
            "## Notes",
            f"- Source: `{source_file}`",
            "- Update by running: `make milestones-sync`",
            "",
        ]
    )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--milestones-file", default="MILESTONES.md")
    parser.add_argument("--todo-file", default="MILESTONES-TODO.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_path = Path(args.milestones_file)
    todo_path = Path(args.todo_file)

    milestones_text = source_path.read_text(encoding="utf-8")
    items = parse_unchecked_items(milestones_text)
    todo_text = build_todo_markdown(items, source_file=str(source_path))
    todo_path.write_text(todo_text, encoding="utf-8")
    print(f"updated {todo_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

