# Windows 11 New Machine Setup (PyCharm + WSL)

Use this runbook to set up a Windows 11 machine for `cp-project` with the same workflow and continuity used on your current machine.

## Goal

Get a new Windows 11 machine into a state where you can:

- clone and run `cp-project`
- use PyCharm with the project venv
- follow the same start/stop session flow
- switch between machines without losing continuity

## Why This Path (Important)

This repo uses:

- `setup.sh` (bash)
- `Makefile` targets
- Linux-style tooling assumptions

Recommended approach: **Windows 11 + WSL2 (Ubuntu)**.

## 0) Prerequisites

- GitHub access to `russalo/cp-project`
- Administrator rights on Windows
- Internet access

---

## 1) Install WSL2 + Ubuntu

**Where:** PowerShell (Run as Administrator)

```powershell
wsl --install -d Ubuntu
```

If prompted, reboot and complete Ubuntu first-run user creation.

Verify WSL install:

**Where:** PowerShell

```powershell
wsl -l -v
```

---

## 2) Install PyCharm on Windows

**Where:** Windows installer or JetBrains Toolbox

- Install PyCharm (Community or Professional)
- Launch once so settings initialize

---

## 3) Install development tools inside Ubuntu (WSL)

**Where:** WSL Terminal (Ubuntu)

```bash
sudo apt update
sudo apt install -y git make curl build-essential python3.12 python3.12-venv postgresql postgresql-contrib
```

Install Node 22 with `nvm`:

```bash
curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm install 22
nvm use 22
```

Install Python 3.12 if not present (repo target), then verify tools:

```bash
git --version
make --version
python3 --version
node --version
npm --version
psql --version
```

---

## 4) Configure git identity on this machine

**Where:** WSL Terminal

```bash
git config --global user.name "Russell Pfister"
git config --global user.email "russellp@cpconst.com"
```

---

## 5) Configure GitHub SSH from WSL

### 5.1 Generate SSH key

**Where:** WSL Terminal

```bash
ssh-keygen -t ed25519 -C "russellp@cpconst.com"
```

At prompts:

- `Enter file in which to save the key ...`: press Enter (default)
- passphrase: optional but recommended

### 5.2 Start ssh-agent and add key

**Where:** WSL Terminal

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

### 5.3 Copy public key

**Where:** WSL Terminal

```bash
cat ~/.ssh/id_ed25519.pub
```

Copy the full output.

### 5.4 Add key to GitHub

**Where:** GitHub site

- Open `https://github.com/settings/keys`
- Click **New SSH key**
- Title: `Win11-WSL` (or similar)
- Paste key
- Save

### 5.5 Test SSH auth

**Where:** WSL Terminal

```bash
ssh -T git@github.com
```

---

## 6) Clone and bootstrap the project

**Where:** WSL Terminal

```bash
mkdir -p ~/Projects
cd ~/Projects
git clone git@github.com:russalo/cp-project.git
cd cp-project
make setup
```

Verify setup:

```bash
make dev-check
make continuity-status
```

---

## 7) Open in PyCharm and set interpreter

**Where:** PyCharm

1. Open project folder (WSL path), for example:
   - `\\wsl$\Ubuntu\home\<your-wsl-user>\Projects\cp-project`
2. Set interpreter to project venv:
   - `.../cp-project/backend/.venv/bin/python`
3. Use integrated terminal at project root for `make` commands

Optional run commands:

**Where:** PyCharm integrated terminal (WSL)

```bash
make backend-run
make frontend-dev
```

---

## 8) Continuity routine (all machines)

### Start session

**Where:** Terminal

```bash
cd ~/Projects/cp-project
make start-session
```

### Stop session

**Where:** PyCharm + Terminal

Before stopping:

- Update `DEV-SESSION.md` (done / next / blockers)
- Update `DECISIONS.md` if a decision changed
- If previous homework batch is fully answered, add 10 new items to `HOMEWORK.md`

Then run:

```bash
cd ~/Projects/cp-project
make stop-session MSG="WIP: <short summary>"
```

---

## 9) Troubleshooting

### `git push` auth fails

**Where:** Terminal

- Confirm SSH remote:

```bash
git remote -v
```

Expect `git@github.com:russalo/cp-project.git`.

- Re-test SSH:

```bash
ssh -T git@github.com
```

### `nvm` not found in a new shell

**Where:** Terminal

```bash
source ~/.bashrc
nvm use 22
```

### Backend env or DB errors (`DB_NAME` missing)

**Where:** Terminal

```bash
cd ~/Projects/cp-project
cp backend/.env.example backend/.env
```

Then fill real values and rerun:

```bash
make setup-backend
make backend-check
```

### PyCharm cannot find interpreter

**Where:** PyCharm

Re-select interpreter path:

- `.../cp-project/backend/.venv/bin/python`

---

## 10) Quick verification checklist

- [ ] `git clone` works via SSH
- [ ] `make setup` completes
- [ ] `make dev-check` passes
- [ ] PyCharm uses `./backend/.venv/bin/python`
- [ ] `make start-session` works
- [ ] `make stop-session` commits/pushes checkpoint

