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

Vercel middleware keeps `/` public and requires Basic Auth for:

- `/stock-research/*`
- `/bitcoin-chat/*`
- `/api/*`, except `/api/poker/*`

`/poker/*`, `/craps/*`, and `/api/poker/*` are public.

Configure these environment variables in Vercel:

```text
APP_AUTH_USERNAME=palmer
APP_AUTH_PASSWORD=<secret password>
```

If `APP_AUTH_PASSWORD` is missing in Vercel, protected routes return `503` so the apps do not accidentally publish without auth.

## API Backend

Railway builds from the root `Dockerfile`, which installs `backend/requirements.txt` and runs:

```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Health check:

```text
/health
```

The backend mirrors the same Basic Auth check for protected `/api/*` routes and locally served app folders when `APP_AUTH_PASSWORD` is configured. Poker, craps, and `/api/poker/*` remain public. Set the same `APP_AUTH_USERNAME` and `APP_AUTH_PASSWORD` values in Railway to protect direct backend access.

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
