# Frontend setup (React + Vite)

For full project onboarding, start with the repo root `README.md`.

This file covers the frontend-specific setup and daily commands.

## Runtime target

- Node `22`
- npm `10+`

The repo includes `.nvmrc` for machine-to-machine consistency.

If you use `nvm`:

```bash
cd ~/Projects/cp-project
nvm install
nvm use
```

## Install dependencies

From the repo root:

```bash
make frontend-install
```

Or directly:

```bash
cd ~/Projects/cp-project/frontend
npm ci
```

## Run the frontend in development

From the repo root:

```bash
make frontend-dev
```

## Verify the frontend

From the repo root:

```bash
make frontend-build
```

This runs:

- `npm ci`
- `npm run lint`
- `npm run build`

## Notes

- The frontend is currently JavaScript-based.
- TypeScript migration is planned later and is tracked in `MILESTONES.md` / `DECISIONS.md`.
- `node_modules/` and build artifacts should stay untracked.
