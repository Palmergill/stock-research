# Deployment

The site is split into static project pages and a shared API backend.

## Static Site

The active static site lives at the repo root:

- `index.html`
- `docs/`
- `stock-research/`
- `poker/`
- `craps/`
- `blackjack/`
- `bitcoin-chat/`
- `admin/`

Production static hosting should serve those files directly. `vercel.json` rewrites `/api/*` requests to the Railway backend.

Vercel middleware keeps `/` public and requires Basic Auth for:

- `/stock-research/*`
- `/bitcoin-chat/*`
- `/admin/*`
- `/api/*`, except `/api/poker/*`

`/poker/*`, `/craps/*`, `/blackjack/*`, and `/api/poker/*` are public.

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

The backend mirrors the same Basic Auth check for protected `/api/*` routes and locally served app folders. Poker, craps, and `/api/poker/*` remain public in the backend; blackjack is served by static hosting in the current deployment. Stock research, Bitcoin chat, admin, and other `/api/*` routes are protected. Protected routes return `503` if `APP_AUTH_PASSWORD` is missing, so set the same `APP_AUTH_USERNAME` and `APP_AUTH_PASSWORD` values in Railway to keep direct backend access usable and protected.

The root Railway deployment uses the root `Dockerfile`, which copies only `backend/`. The standalone service under `poker/backend/` is not active in this deployment path.

Stock Research uses Polygon in production. Configure:

```text
USE_REAL_DATA=true
POLYGON_API_KEY=<secret Polygon key>
```

`USE_REAL_DATA` defaults to `true` in the app and Docker image; set it to `false` only for local development with synthetic stock data.

## Local

Use:

```bash
./start.sh
```

This runs the API and active static pages together at:

```text
http://127.0.0.1:8000
```

`LOCAL_SITE_ROOT=true` currently mounts `shared/`, `stock-research/`, `poker/`, `craps/`, `bitcoin-chat/`, and `admin/` through FastAPI. The `blackjack/` app is a static site folder served by production static hosting; use a static file server or add a local FastAPI mount if you need that exact route locally.

## Archived Code

Legacy frontends and design demos live under `archive/`. They are retained for reference, but are not active deployment targets.
