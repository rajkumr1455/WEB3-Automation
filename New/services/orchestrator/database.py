"""
Database connection and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
import os
from contextlib import contextmanager
import logging

from models import Base

logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://web3hunter:hunter_password@postgres:5432/web3hunter"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    echo=False,  # Set to True for SQL logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Thread-safe session
ScopedSession = scoped_session(SessionLocal)


def init_db():
    """Initialize database - create all tables"""
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


def drop_db():
    """Drop all tables - USE WITH CAUTION"""
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.warning("All tables dropped")


@contextmanager
def get_db():
    """
    Database session context manager
    
    Usage:
        with get_db() as db:
            scan = db.query(Scan).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()


def get_db_session():
    """
    Get database session for dependency injection
    
    Usage with FastAPI:
        @app.get("/scans")
        def get_scans(db: Session = Depends(get_db_session)):
            return db.query(Scan).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
