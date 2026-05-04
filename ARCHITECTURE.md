# Architecture

## Overview

```text
Browser
  |
  | static HTML/CSS/JS
  v
Static host / local FastAPI static mode
  |
  | /api/*
  v
FastAPI backend
  |
  +-- stock data clients and SQLite/Postgres cache
  +-- poker game APIs
  +-- Bitcoin chat APIs
```

## Frontend Entry Points

The active public site is static:

- `/` - portfolio/project launcher from `index.html`
- `/stock-research/` - stock research app
- `/poker/` - poker app
- `/craps/` - craps app
- `/bitcoin-chat/` - Bitcoin chat app

Earlier stock-app frontends are retained under `archive/` and are not served by default.

## Backend

The backend is a FastAPI service in `backend/app`.

Important routes:

- `/api/stocks/*`
- `/api/poker/*`
- `/api/bitcoin/*`
- `/health`
- `/docs`

In production, `/` returns API metadata. In local development, `./start.sh` sets `LOCAL_SITE_ROOT=true`, which makes FastAPI serve the static project folders as well.

## Local Development

```bash
./start.sh
```

Open:

```text
http://127.0.0.1:8000
```

Logs:

```text
logs/backend.log
```

## Deployment

- Static site hosting serves the root static files and project directories.
- Vercel rewrites `/api/*` to the Railway API.
- Railway runs the Dockerized FastAPI backend from `backend/`.
