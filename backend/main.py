"""AI-Enhanced CRM & Ticket Management System - FastAPI entry point."""
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import init_db
from routers import ai, auth, customers, dashboard, integrations, notifications, reports, tickets, users

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI CRM & Ticket Management", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(customers.router, prefix=API_PREFIX)
app.include_router(tickets.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)
app.include_router(ai.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(notifications.router, prefix=API_PREFIX)
app.include_router(reports.router, prefix=API_PREFIX)
app.include_router(integrations.router, prefix=API_PREFIX)


@app.on_event("startup")
def startup():
    init_db()


@app.get(f"{API_PREFIX}/health")
def health():
    return {"status": "ok"}


# Serve frontend static files (must be after API routes)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
