# Backend

FastAPI + SQLite + yfinance stock data API.

## Setup

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

API docs at http://localhost:8000/docs
