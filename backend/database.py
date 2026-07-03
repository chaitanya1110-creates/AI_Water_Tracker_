"""
SQLAlchemy database setup and ORM model for water intake logs.

Table: water_intake
  - id          : Integer, primary key, autoincrement
  - user_name   : String, the user's name
  - water_intake_ml : Integer, water intake in millilitres
  - date_time   : DateTime, when the entry was logged (defaults to now)
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Read the DATABASE_URL from the environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/water_tracker_db.db")

# SQLite needs check_same_thread=False so FastAPI's async request handlers
# can share the connection across threads.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# Create the engine
engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)

# Session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Base class for ORM models
Base = declarative_base()


class WaterIntake(Base):
    """ORM model representing a single water intake log entry."""

    __tablename__ = "water_intake"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(100), nullable=False)
    water_intake_ml = Column(Integer, nullable=False)
    date_time = Column(DateTime, default=datetime.now, nullable=False)

    def as_dict(self):
        """Helper to serialize the row to a plain dict (used in API responses)."""
        return {
            "id": self.id,
            "user_name": self.user_name,
            "water_intake_ml": self.water_intake_ml,
            # Use ISO format string so JSON serialization is clean.
            "date_time": self.date_time.isoformat() if self.date_time else None,
        }


def init_db():
    """Create the database file (if missing) and all tables."""
    # Make sure the ./data directory exists for SQLite file-based DB.
    if DATABASE_URL.startswith("sqlite") and "///./data/" in DATABASE_URL:
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(data_dir, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency that yields a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
