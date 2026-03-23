# CONTINUITY CHECKLIST (Multi-Machine Start/Stop)

Use this runbook whenever you switch machines so work stays synchronized and easy to resume.

## Start Session / Stop Session (Quick Card)

Use this one-screen card for day-to-day continuity.

> Maintenance rule: keep this quick card and the matching section in `README.md` identical. Update both in the same commit.

### Start Session (new work branch)

```bash
cd ~/Projects/cp-project
git switch main
git pull --rebase
make start-session
git switch -c feature/<short-name>
```

### Start Session (continue existing branch)

```bash
cd ~/Projects/cp-project
git switch <existing-branch>
git pull --rebase
make continuity-status
```

### Stop Session

Before running the command, update `DEV-SESSION.md` and the relevant decision docs (`DECISIONS.md`
or `DECISIONS_INBOX.md`) if planning changed.

```bash
cd ~/Projects/cp-project
make stop-session MSG="WIP: <short summary>"
```

### After PR Merge

```bash
cd ~/Projects/cp-project
git switch main
git pull --rebase
git branch -d <merged-branch>
```

---

## Quick Session Commands

Use these when you want a one-command start/stop flow.

**Where:** Terminal

Start a session:

```bash
cd ~/Projects/cp-project
make start-session
```

Stop a session:

```bash
cd ~/Projects/cp-project
make stop-session
```

Custom stop commit message:

```bash
cd ~/Projects/cp-project
make stop-session MSG="WIP: <short summary>"
```

## Start Of Session

### 1) Sync and verify

**Where:** Terminal

```bash
cd ~/Projects/cp-project
git pull --rebase
make continuity-status
make local-check
```

### 2) Open project

**Where:** PyCharm

- Open `cp-project`
- Confirm interpreter is `./backend/.venv/bin/python`
- Use integrated terminal at repo root for `make` commands
- Check `gh auth status` if you want session commands to use GitHub CLI sync/auth automatically

### 3) Pick work branch

**Where:** Terminal

```bash
cd ~/Projects/cp-project
git switch main
git pull --rebase
git switch -c feature/<short-name>
```

If branch already exists:

```bash
cd ~/Projects/cp-project
git switch <existing-branch>
git pull --rebase
```

### 4) Regain context

**Where:** PyCharm or editor

- Read `DEV-SESSION.md` for recent progress and next actions
- Check `DECISIONS.md` for accepted constraints before coding
- Check `INBOX.md`, `DECISIONS_INBOX.md`, and `MILESTONES_INBOX.md` if documentation review is pending

## Stop Of Session

### 1) Save context before commit

**Where:** PyCharm or editor

Update `DEV-SESSION.md` with:

- What you changed today
- What should be done next
- Any blockers/questions

If a planning/architecture choice was made, update `DECISIONS.md` or `DECISIONS_INBOX.md`.

Homework rollover rule:

- If the current homework batch is fully answered, add 10 new homework items to `HOMEWORK.md` before ending the session.
- `make stop-session` now checks this automatically and appends a new 10-item open batch when needed.

### 2) Commit and push checkpoint

**Where:** Terminal

```bash
cd ~/Projects/cp-project
git status
git add -A
git commit -m "WIP: <short summary>"
git push -u origin HEAD
```

### 3) If ready for review

**Where:** GitHub site

- Open or update PR from your branch
- Add short notes on status, risks, and next step

## Minimum Handoff Criteria

Before switching machines, all should be true:

- Latest work is committed and pushed
- `DEV-SESSION.md` reflects where to resume
- Any new decision is captured in `DECISIONS.md` or `DECISIONS_INBOX.md`
- If previous homework is complete, the next 10 homework items are added to `HOMEWORK.md`
- No secrets were committed (`backend/.env` stays local)

## New Machine Bootstrap (First Time Only)

**Where:** Terminal

```bash
cd ~/Projects
git clone git@github.com:russalo/cp-project.git
cd cp-project
make setup-online
make local-check
make continuity-status
```

Then open `cp-project` in PyCharm and set interpreter to `backend/.venv/bin/python`.
