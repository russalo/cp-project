#!/usr/bin/env python3
"""Sync DECISIONS.md index into a PyCharm TODO file and optional GitHub Issues."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

INDEX_HEADER = "## Decision Index"
DECISION_ID_RE = re.compile(r"DEC-\d+")
STATUS_ACTIONABLE = {"proposed", "deferred"}


@dataclass
class Decision:
    id: str
    milestone: str
    topic: str
    status: str
    owner: str
    target_date: str


def _split_markdown_row(row: str) -> list[str]:
    return [cell.strip() for cell in row.strip().strip("|").split("|")]


def parse_decision_index(decisions_text: str) -> list[Decision]:
    lines = decisions_text.splitlines()
    try:
        start = lines.index(INDEX_HEADER)
    except ValueError as exc:
        raise RuntimeError(f"{INDEX_HEADER} not found") from exc

    table_lines: list[str] = []
    for line in lines[start + 1 :]:
        if line.strip().startswith("|"):
            table_lines.append(line)
            continue
        if table_lines and not line.strip():
            break

    if len(table_lines) < 3:
        raise RuntimeError("Decision index table is missing or malformed")

    headers = _split_markdown_row(table_lines[0])
    decisions: list[Decision] = []

    for row in table_lines[2:]:
        cells = _split_markdown_row(row)
        if len(cells) != len(headers):
            continue
        mapped = dict(zip(headers, cells))
        decision_id = mapped.get("ID", "")
        if not DECISION_ID_RE.fullmatch(decision_id):
            continue
        decisions.append(
            Decision(
                id=decision_id,
                milestone=mapped.get("Milestone", "TBD"),
                topic=mapped.get("Topic", ""),
                status=mapped.get("Status", "proposed").lower(),
                owner=mapped.get("Owner", "TBD"),
                target_date=mapped.get("Target Date", "TBD"),
            )
        )

    return decisions


def build_todo_markdown(decisions: list[Decision], source_file: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    actionable = [d for d in decisions if d.status in STATUS_ACTIONABLE]

    lines = [
        "# DECISIONS TODO",
        "",
        "Auto-generated from `DECISIONS.md` decision index.",
        f"Generated at: `{timestamp}`",
        "",
        "## Open decision work",
    ]

    if not actionable:
        lines.extend(["", "No open decision work."])
        return "\n".join(lines) + "\n"

    lines.append("")
    for decision in actionable:
        lines.append(
            f"- TODO(decision): [{decision.id}] ({decision.milestone}) {decision.topic}"
            f" | status={decision.status} | owner={decision.owner} | target={decision.target_date}"
        )

    lines.extend(
        [
            "",
            "## Notes",
            f"- Source: `{source_file}`",
            "- Update by running: `make decisions-sync`",
        ]
    )
    return "\n".join(lines) + "\n"


class GitHubIssuesClient:
    def __init__(self, repo: str, token: str):
        if "/" not in repo:
            raise ValueError("repo must be in owner/name format")
        self.repo = repo
        self.api_base = f"https://api.github.com/repos/{repo}"
        self.token = token

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        url = f"{self.api_base}{path}"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "cp-project-decisions-sync",
        }
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = Request(url, data=data, method=method, headers=headers)
        try:
            with urlopen(req) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else None
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API {exc.code}: {detail}") from exc

    def list_decision_issues(self) -> dict[str, dict[str, Any]]:
        query = urlencode({"state": "all", "per_page": 100})
        issues = self._request("GET", f"/issues?{query}")
        by_id: dict[str, dict[str, Any]] = {}
        for issue in issues:
            if "pull_request" in issue:
                continue
            match = re.search(r"Decision-ID:\s*(DEC-\d+)", issue.get("body", ""))
            if match:
                by_id[match.group(1)] = issue
        return by_id

    def create_issue(self, decision: Decision) -> None:
        payload = {
            "title": f"[{decision.id}] {decision.topic}",
            "body": issue_body(decision),
        }
        self._request("POST", "/issues", payload)

    def update_issue(self, issue_number: int, decision: Decision, state: str) -> None:
        payload = {
            "title": f"[{decision.id}] {decision.topic}",
            "body": issue_body(decision),
            "state": state,
        }
        self._request("PATCH", f"/issues/{issue_number}", payload)


def issue_body(decision: Decision) -> str:
    return "\n".join(
        [
            "This issue is synchronized from `DECISIONS.md`.",
            "",
            f"- Decision-ID: {decision.id}",
            f"- Milestone: {decision.milestone}",
            f"- Topic: {decision.topic}",
            f"- Status: {decision.status}",
            f"- Owner: {decision.owner}",
            f"- Target Date: {decision.target_date}",
            "",
            "Update source record in `DECISIONS.md` (Decision Index).",
        ]
    )


def sync_github_issues(decisions: list[Decision], repo: str, token: str) -> None:
    client = GitHubIssuesClient(repo=repo, token=token)
    existing = client.list_decision_issues()

    for decision in decisions:
        issue = existing.get(decision.id)
        should_be_open = decision.status in STATUS_ACTIONABLE

        if issue is None:
            if should_be_open:
                client.create_issue(decision)
                print(f"created issue for {decision.id}")
            continue

        issue_number = int(issue["number"])
        current_state = issue.get("state", "open")
        target_state = "open" if should_be_open else "closed"

        if current_state != target_state or issue.get("title") != f"[{decision.id}] {decision.topic}":
            client.update_issue(issue_number, decision, state=target_state)
            print(f"updated issue #{issue_number} for {decision.id} -> {target_state}")
        else:
            # Keep issue body in sync even if state/title already match.
            client.update_issue(issue_number, decision, state=target_state)
            print(f"refreshed issue #{issue_number} for {decision.id}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decisions-file", default="DECISIONS.md")
    parser.add_argument("--todo-file", default="DECISIONS-TODO.md")
    parser.add_argument("--sync-github", action="store_true")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    decisions_path = Path(args.decisions_file)
    todo_path = Path(args.todo_file)

    decisions = parse_decision_index(decisions_path.read_text(encoding="utf-8"))
    todo_markdown = build_todo_markdown(decisions, source_file=str(decisions_path))
    todo_path.write_text(todo_markdown, encoding="utf-8")
    print(f"updated {todo_path}")

    if args.sync_github:
        if not args.repo or not args.token:
            raise RuntimeError("--sync-github requires --repo and --token (or env vars)")
        sync_github_issues(decisions, repo=args.repo, token=args.token)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI failure path
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)

