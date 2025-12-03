"""
SQLAlchemy Models for Persistence
"""

from sqlalchemy import Column, String, Integer, DateTime, JSON, Boolean, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Scan(Base):
    """Scan record"""
    __tablename__ = "scans"
    
    # Primary key
    scan_id = Column(String(36), primary_key=True, index=True)
    
    # Scan metadata
    target_url = Column(String(512), nullable=True)
    contract_address = Column(String(42), nullable=True, index=True)
    chain = Column(String(32), nullable=False, default="ethereum", index=True)
    
    # Status tracking
    status = Column(String(32), nullable=False, default="pending", index=True)
    progress = Column(Integer, default=0)
    current_stage = Column(String(64), nullable=True)
    
    # Configuration and results
    scan_config = Column(JSON, default={})
    artifacts = Column(JSON, default={})  # All stage results
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Migration flag
    migrated = Column(Boolean, default=False, index=True)
    
    #Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Scan(scan_id={self.scan_id}, status={self.status}, chain={self.chain})>"


class JobQueue(Base):
    """Job queue for RQ tracking"""
    __tablename__ = "job_queue"
    
    # Primary key
    job_id = Column(String(36), primary_key=True, index=True)
    
    # Foreign key to scan
    scan_id = Column(String(36), nullable=False, index=True)
    
    # Job metadata
    job_type = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default="pending", index=True)
    
    # Results
    result_data = Column(JSON, default={})
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<JobQueue(job_id={self.job_id}, type={self.job_type}, status={self.status})>"


class StageResult(Base):
    """Individual stage results"""
    __tablename__ = "stage_results"
    
    # Composite primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(String(36), nullable=False, index=True)
    stage_name = Column(String(64), nullable=False)
    stage_order = Column(Integer, nullable=False)
    
    # Results
    status = Column(String(32), nullable=False, default="completed")
    result_data = Column(JSON, default={})
    
    # Timestamp
    completed_at = Column(DateTime, default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<StageResult(scan_id={self.scan_id}, stage={self.stage_name}, order={self.stage_order})>"


# Migration helper
def create_tables(db_url: str):
    """Create all tables"""
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return engine
