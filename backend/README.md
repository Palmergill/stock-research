# Backend

FastAPI service for the Palmer Gill project site.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run API Only

```bash
uvicorn app.main:app --reload
```

This mode exposes API endpoints and returns service metadata at `/`.

## Run Local Site + API

From the repo root:

```bash
./start.sh
```

That sets `LOCAL_SITE_ROOT=true`, which serves the root portfolio page and active project folders from the same FastAPI process.

## Useful URLs

- `http://127.0.0.1:8000/` - local site root when `LOCAL_SITE_ROOT=true`
- `http://127.0.0.1:8000/stock-research/` - stock app
- `http://127.0.0.1:8000/health` - health check
- `http://127.0.0.1:8000/docs` - FastAPI docs
