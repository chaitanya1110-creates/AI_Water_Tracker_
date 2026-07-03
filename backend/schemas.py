"""
Pydantic schemas (request/response models) for the water intake API.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class IntakeCreate(BaseModel):
    """Request body for POST /api/intake — the frontend sends this."""

    user_name: str = Field(..., min_length=1, max_length=100, description="User's name")
    water_intake_ml: int = Field(..., gt=0, description="Water intake in millilitres")


class IntakeResponse(BaseModel):
    """Response for a single intake entry (returned after logging)."""

    id: int
    user_name: str
    water_intake_ml: int
    date_time: datetime


class IntakeSummaryResponse(BaseModel):
    """Aggregated summary of today's intake for a user."""

    user_name: str
    date: str  # ISO date string (YYYY-MM-DD)
    total_intake_ml: int
    entries: list[IntakeResponse]
    goal_ml: int
    remaining_ml: int  # negative if goal exceeded


class InsightResponse(BaseModel):
    """AI-generated insight returned to the frontend."""

    user_name: str
    date: str
    total_intake_ml: int
    goal_ml: int
    remaining_ml: int
    ai_summary: str


class ChatRequest(BaseModel):
    """Request body for POST /api/chat — optional for free-form Q&A."""

    user_name: str = Field(..., description="User's name (to fetch their data)")
    message: str = Field(..., min_length=1, description="User's question to the AI")


class ChatResponse(BaseModel):
    """Response from the AI chat endpoint."""

    user_name: str
    answer: str
    total_intake_ml: int
    goal_ml: int
    remaining_ml: int
