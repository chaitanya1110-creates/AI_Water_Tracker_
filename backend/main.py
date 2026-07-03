"""
FastAPI application — Water Tracker backend.

Endpoints
---------
POST   /api/intake      Log a water intake entry (user_name + water_intake_ml).
GET    /api/intake      Get the user's logged entries for today (with totals).
GET    /api/insight     AI summary: today's intake, remaining, and recommendation.
POST   /api/chat        Free-form Q&A with the AI about the user's progress.

Database
--------
SQLite via SQLAlchemy. The DB file lives at backend/data/water_tracker_db.db
(the name 'water_tracker_db' comes from DATABASE_URL in .env).
"""

from datetime import datetime, date
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import init_db, get_db, WaterIntake
from schemas import (
    IntakeCreate,
    IntakeResponse,
    IntakeSummaryResponse,
    InsightResponse,
    ChatRequest,
    ChatResponse,
)
from agent import generate_insight, generate_chat_answer
from dotenv import load_dotenv
import os

load_dotenv()

DEFAULT_DAILY_GOAL_ML = int(os.getenv("DEFAULT_DAILY_GOAL_ML", "2500"))

app = FastAPI(title="AI Water Tracker API", version="1.0.0")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Create the SQLite database and tables when the server starts."""
    init_db()


@app.get("/")
def root():
    return {"message": "AI Water Tracker API is running.", "docs": "/docs"}


# ---------------------------------------------------------------------------
# POST /api/intake  — log a water intake entry
# ---------------------------------------------------------------------------
@app.post("/api/intake", response_model=IntakeResponse)
def log_intake(payload: IntakeCreate, db: Session = Depends(get_db)):
    """Receive the user's name + water intake (ml) from the frontend and store it."""
    entry = WaterIntake(
        user_name=payload.user_name,
        water_intake_ml=payload.water_intake_ml,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry  # FastAPI serializes it via IntakeResponse (includes id + date_time)


# ---------------------------------------------------------------------------
# GET /api/intake  — get today's entries for a user (with totals)
# ---------------------------------------------------------------------------
@app.get("/api/intake", response_model=IntakeSummaryResponse)
def get_today_intake(user_name: str, db: Session = Depends(get_db)):
    """Return all of the user's intake entries logged today, plus daily totals."""
    today = date.today()
    entries = (
        db.query(WaterIntake)
        .filter(WaterIntake.user_name == user_name)
        .filter(WaterIntake.date_time >= datetime.combine(today, datetime.min.time()))
        .order_by(WaterIntake.date_time.asc())
        .all()
    )
    total = sum(e.water_intake_ml for e in entries)
    remaining = DEFAULT_DAILY_GOAL_ML - total
    return IntakeSummaryResponse(
        user_name=user_name,
        date=today.isoformat(),
        total_intake_ml=total,
        entries=[IntakeResponse.model_validate(e.as_dict()) for e in entries],
        goal_ml=DEFAULT_DAILY_GOAL_ML,
        remaining_ml=remaining,
    )


# ---------------------------------------------------------------------------
# GET /api/insight  — AI summary of today's intake + recommendation
# ---------------------------------------------------------------------------
@app.get("/api/insight", response_model=InsightResponse)
def get_insight(user_name: str, db: Session = Depends(get_db)):
    """
    Generate an AI-powered summary of the user's progress today:
    total water drunk, how much more they should drink, and a tip.
    """
    today = date.today()
    entries = (
        db.query(WaterIntake)
        .filter(WaterIntake.user_name == user_name)
        .filter(WaterIntake.date_time >= datetime.combine(today, datetime.min.time()))
        .order_by(WaterIntake.date_time.asc())
        .all()
    )
    total = sum(e.water_intake_ml for e in entries)
    remaining = DEFAULT_DAILY_GOAL_ML - total

    # Build a human-readable summary of log entries for the AI
    if entries:
        entries_summary = "\n".join(
            f"- {e.date_time.strftime('%H:%M')}: {e.water_intake_ml} ml"
            for e in entries
        )
    else:
        entries_summary = "- No water logged yet today."

    try:
        ai_summary = generate_insight(
            user_name=user_name,
            total_intake_ml=total,
            goal_ml=DEFAULT_DAILY_GOAL_ML,
            remaining_ml=remaining,
            entries_summary=entries_summary,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return InsightResponse(
        user_name=user_name,
        date=today.isoformat(),
        total_intake_ml=total,
        goal_ml=DEFAULT_DAILY_GOAL_ML,
        remaining_ml=remaining,
        ai_summary=ai_summary,
    )


# ---------------------------------------------------------------------------
# POST /api/chat  — free-form Q&A with the AI about the user's progress
# ---------------------------------------------------------------------------
@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    """Answer the user's question, grounded in today's intake data."""
    today = date.today()
    entries = (
        db.query(WaterIntake)
        .filter(WaterIntake.user_name == payload.user_name)
        .filter(WaterIntake.date_time >= datetime.combine(today, datetime.min.time()))
        .all()
    )
    total = sum(e.water_intake_ml for e in entries)
    remaining = DEFAULT_DAILY_GOAL_ML - total

    try:
        answer = generate_chat_answer(
            user_name=payload.user_name,
            message=payload.message,
            total_intake_ml=total,
            goal_ml=DEFAULT_DAILY_GOAL_ML,
            remaining_ml=remaining,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return ChatResponse(
        user_name=payload.user_name,
        answer=answer,
        total_intake_ml=total,
        goal_ml=DEFAULT_DAILY_GOAL_ML,
        remaining_ml=remaining,
    )
