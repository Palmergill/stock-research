from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database_migration import init_db_with_migration
from app.routers import bitcoin, stocks, poker
import os

app = FastAPI(title="Palmer Gill API", version="0.2.0-p5")

# CORS - allow frontend to call backend
# Allow all origins for development (restrict in production)
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "https://palmergill.com")
if allowed_origins_str == "*":
    # Allow all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # Must be False when using "*"
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.on_event("startup")
async def startup():
    init_db_with_migration()

app.include_router(stocks.router)
app.include_router(poker.router)
app.include_router(bitcoin.router)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.2.1"}

# Static site serving is only enabled for local development. Production should
# treat this FastAPI app as the API service; the public site is hosted separately.
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
repo_root = os.path.abspath(os.path.join(backend_dir, ".."))
local_site_root_enabled = os.getenv("LOCAL_SITE_ROOT", "").lower() in {"1", "true", "yes"}

if local_site_root_enabled:
    for route, folder in {
        "/stock-research": "stock-research",
        "/poker": "poker",
        "/craps": "craps",
        "/bitcoin-chat": "bitcoin-chat",
    }.items():
        directory = os.path.join(repo_root, folder)
        if os.path.exists(directory):
            app.mount(route, StaticFiles(directory=directory, html=True), name=folder)

@app.get("/")
async def root():
    if local_site_root_enabled:
        return FileResponse(os.path.join(repo_root, "index.html"))
    return {
        "service": "Palmer Gill API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
        "local_site": "Set LOCAL_SITE_ROOT=true to serve local static pages from this process.",
    }
