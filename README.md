# Palmer Gill

Personal project site plus shared API backend.

## Active Site Paths

- `/` - project index
- `/stock-research/` - polished stock research app
- `/poker/` - Texas Hold'em poker app
- `/craps/` - craps app
- `/bitcoin-chat/` - Bitcoin chat app

## Active Backend Paths

- `/api/stocks/*` - stock research API
- `/api/poker/*` - poker API
- `/api/bitcoin/*` - Bitcoin chat API
- `/health` - backend health check
- `/docs` - FastAPI docs

## Local Development

```bash
./start.sh
```

Open:

```text
http://127.0.0.1:8000
```

The local server runs FastAPI and, with `LOCAL_SITE_ROOT=true`, also serves the static project folders so the local URL shape matches `palmergill.com`.

To require Basic Auth locally, set:

```bash
APP_AUTH_USERNAME=palmer APP_AUTH_PASSWORD=your-password ./start.sh
```

Logs are written to:

```text
logs/backend.log
```

## Deployment Model

- Static site: hosted from the repo root and project folders.
- API service: Railway/FastAPI from `backend/`.
- Vercel rewrites `/api/*` to the Railway backend in production.
- The root page `/`, `/poker/`, `/craps/`, and `/api/poker/*` stay public. Stock research, Bitcoin chat, and other `/api/*` routes require Basic Auth when `APP_AUTH_PASSWORD` is configured. Set the same `APP_AUTH_USERNAME` and `APP_AUTH_PASSWORD` values in Vercel and Railway.

## Repository Layout

```text
backend/          FastAPI API service
stock-research/   Active stock research frontend
poker/            Active poker frontend and supporting docs/tests
craps/            Active craps frontend
bitcoin-chat/     Active Bitcoin chat frontend
archive/          Legacy frontends, demos, and planning artifacts
```

## Notes

The original site started as only the stock research app. Legacy versions of that UI have been moved into `archive/` so active entrypoints are easier to identify.
