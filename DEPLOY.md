# Deployment

The site is split into static project pages and a shared API backend.

## Static Site

The active static site lives at the repo root:

- `index.html`
- `stock-research/`
- `poker/`
- `craps/`
- `bitcoin-chat/`

Production static hosting should serve those files directly. `vercel.json` rewrites `/api/*` requests to the Railway backend.

## API Backend

Railway builds from the root `Dockerfile`, which installs `backend/requirements.txt` and runs:

```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Health check:

```text
/health
```

## Local

Use:

```bash
./start.sh
```

This runs the API and active static pages together at:

```text
http://127.0.0.1:8000
```

## Archived Code

Legacy frontends and design demos live under `archive/`. They are retained for reference, but are not active deployment targets.
