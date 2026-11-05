import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database.base import Base


# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./documind.db"
)


# SQLite-specific configuration
connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}


# Create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)


# Create database session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Initialize database tables
def init_db():
    Base.metadata.create_all(bind=engine)


# Database dependency for FastAPI
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()