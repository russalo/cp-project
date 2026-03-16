#!/usr/bin/env python3
"""Auto-roll homework batches when no open batch exists or an open batch is fully answered."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOMEWORK_PATH = ROOT / "HOMEWORK.md"

QUESTION_BANK = [
    "**EWO numbering strategy:** should EWO IDs be sequential globally, per customer, or per job number?",
    "**Job number validation:** what format rules should v1 enforce for job number entry (required prefix/length/characters)?",
    "**Labor unit policy:** should labor be captured in hours only, or support hour + minute precision in v1?",
    "**Equipment quantity model:** should equipment usage be time-based only, quantity-based only, or both with explicit unit types?",
    "**Material pricing entry rule:** should materials default to unit cost x quantity, with optional manual total override?",
    "**Rounding policy detail:** where should rounding occur (line item, category subtotal, final total), and to how many decimals?",
    "**Tax policy boundary:** should tax be excluded from v1, optional per EWO, or required per material line category?",
    "**Overtime modeling:** should overtime be represented as separate labor line types or a multiplier on standard labor lines?",
    "**Approval authority:** which role is allowed to approve/reject EWOs in v1, and is dual-approval needed?",
    "**Post-approval edits:** if an approved EWO must change, should it reopen, clone to revision, or require admin override with audit reason?",
    "**Rejection workflow:** when rejected, should EWO return to draft, move to a rejected terminal state, or require explicit resubmission action?",
    "**Billing handoff format:** what exact export/summary fields must be present for office billing handoff in v1?",
    "**Audit event scope:** which actions must be audited in v1 (create/edit/delete/submit/approve/rate change/login)?",
    "**Soft delete vs hard delete:** should core records use soft deletes for traceability, and who can perform permanent deletes?",
    "**Attachment ownership model (future):** should uploaded documents belong to material lines, EWOs, or both with linkage metadata?",
    "**Search v1 priority:** which 3 filters are mandatory first (job number, date range, status, customer, creator)?",
    "**Pagination default:** what default page size should APIs and UI use, and should users be able to change it?",
    "**Timezone policy:** should all timestamps be stored UTC and displayed in a single company timezone in v1?",
    "**Concurrency handling:** how should conflicting edits be handled (last write wins, optimistic lock, manual merge warning)?",
    "**Error handling standard:** what user-facing error format is required in UI for validation vs system errors?",
    "**Health check definition:** what endpoint(s) define app health for deploy validation (DB connectivity required or app-only)?",
    "**Backup retention baseline:** how many daily/weekly backups should be retained during Milestone 1 baseline?",
    "**Restore RTO target:** what is the acceptable restore time target for the first production baseline?",
    "**Environment promotion rule:** should changes flow strictly dev -> PR -> main -> production, or allow emergency direct hotfix paths?",
    "**Release notes habit:** should each stop-session push include a short changelog line in `DEV-SESSION.md` for traceability?",
    "**Testing minimum for M1:** should PRs require at least one backend smoke test before merge, or defer until M2?",
    "**API versioning start:** should APIs start unversioned in v1 or use `/api/v1/` from day one?",
    "**Idempotency policy:** should EWO create endpoints support idempotency keys in v1 or defer to later hardening?",
    "**Role bootstrap:** who creates the first admin users in production and what is the secure bootstrap process?",
    "**Data correction policy:** when financial data is wrong after billing, should corrections create adjustment EWOs instead of direct edits?",
]


def next_batch_number(text: str) -> int:
    file_numbers: list[int] = []
    for path in ROOT.glob("HOMEWORK-*.md"):
        match = re.match(r"HOMEWORK-(\d{3})\.md", path.name)
        if match:
            file_numbers.append(int(match.group(1)))

    heading_numbers = [int(n) for n in re.findall(r"^## Homework Batch (\d{3})", text, re.MULTILINE)]
    max_number = max(file_numbers + heading_numbers, default=0)
    return max_number + 1


def open_batch_section(text: str) -> tuple[int, int, str] | None:
    match = re.search(r"^## Homework Batch (\d{3}) \(Open\)$", text, re.MULTILINE)
    if not match:
        return None
    start = match.start()
    next_header = re.search(r"^## ", text[match.end() :], re.MULTILINE)
    end = match.end() + (next_header.start() if next_header else len(text[match.end() :]))
    section = text[start:end]
    return start, end, section


def select_questions(text: str, count: int = 10) -> list[str]:
    selected: list[str] = []
    for question in QUESTION_BANK:
        if question in text:
            continue
        selected.append(question)
        if len(selected) == count:
            return selected
    # Fallback if bank is exhausted.
    while len(selected) < count:
        selected.append(f"**Open planning item {len(selected)+1}:** define this item for the next planning pass.")
    return selected


def build_batch(batch_num: int, questions: list[str]) -> str:
    lines = [
        f"## Homework Batch {batch_num:03d} (Open)",
        "",
        f"Created automatically during stop-session rollover on {__import__('datetime').date.today().isoformat()}.",
        "",
    ]
    for i, question in enumerate(questions, start=1):
        lines.append(f"{i}. {question}")
        lines.append("   - Answer: TBD")
    lines.append("")
    return "\n".join(lines)


def ensure_rollover() -> bool:
    text = HOMEWORK_PATH.read_text(encoding="utf-8")
    section_info = open_batch_section(text)

    should_create = False
    if section_info is None:
        should_create = True
    else:
        _, _, section = section_info
        should_create = "Answer: TBD" not in section

    if not should_create:
        print("[homework] Open homework batch already exists; no rollover needed.")
        return False

    batch_num = next_batch_number(text)
    questions = select_questions(text)
    batch_block = build_batch(batch_num, questions)

    marker = "- There is no open homework list at the moment."
    if marker in text:
        text = text.replace(marker, f"- Active homework batch: `{batch_num:03d}` in this file.")

    if not text.endswith("\n"):
        text += "\n"
    text = f"{text}\n{batch_block}".rstrip() + "\n"

    HOMEWORK_PATH.write_text(text, encoding="utf-8")
    print(f"[homework] Added Homework Batch {batch_num:03d} with 10 new items.")
    return True


if __name__ == "__main__":
    ensure_rollover()

