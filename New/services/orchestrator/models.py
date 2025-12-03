"""
Database models for Web3 Hunter platform
SQLAlchemy models for scans, results, and job tracking
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Enum as SQLEnum, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class ScanStatus(str, enum.Enum):
    """Scan status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Scan(Base):
    """Main scan record"""
    __tablename__ = "scans"
    
    # Primary key
    scan_id = Column(String(36), primary_key=True)  # UUID
    
    # Request details
    target_url = Column(String(512), nullable=True)
    contract_address = Column(String(42), nullable=True, index=True)
    chain = Column(String(32), nullable=True, index=True)
    scan_config = Column(JSON, nullable=True)
    
    # Status tracking
    status = Column(SQLEnum(ScanStatus), nullable=False, default=ScanStatus.PENDING, index=True)
    current_stage = Column(String(64), nullable=True)
    progress = Column(Integer, default=0)  # 0-100
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Results summary
    total_findings = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    # Relationships
    stage_results = relationship("StageResult", back_populates="scan", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            "scan_id": self.scan_id,
            "target_url": self.target_url,
            "contract_address": self.contract_address,
            "chain": self.chain,
            "status": self.status.value,
            "current_stage": self.current_stage,
            "progress": self.progress,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "error": self.error_message,
        }


class StageResult(Base):
    """Individual stage results for a scan"""
    __tablename__ = "stage_results"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key
    scan_id = Column(String(36), ForeignKey("scans.scan_id"), nullable=False, index=True)
    
    # Stage identification
    stage_name = Column(String(64), nullable=False, index=True)  # e.g., "address_scan", "static", "triage"
    stage_order = Column(Integer, nullable=False)  # Execution order
    
    # Stage status
    status = Column(String(32), nullable=False)  # completed, skipped, failed
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Results data (JSON)
    result_data = Column(JSON, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    # Relationships
    scan = relationship("Scan", back_populates="stage_results")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "stage_name": self.stage_name,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "result_data": self.result_data,
            "error": self.error_message,
        }


class JobQueue(Base):
    """Background job tracking"""
    __tablename__ = "job_queue"
    
    # Primary key
    job_id = Column(String(36), primary_key=True)  # UUID
    
    # Job details
    job_type = Column(String(64), nullable=False, index=True)  # e.g., "scan_pipeline"
    scan_id = Column(String(36), ForeignKey("scans.scan_id"), nullable=True, index=True)
    
    # Job status
    status = Column(String(32), nullable=False, index=True)  # pending, running, completed, failed
    priority = Column(Integer, default=0, index=True)  # Higher = more important
    
    # Retry tracking
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Job data
    job_data = Column(JSON, nullable=True)
    result_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "scan_id": self.scan_id,
            "status": self.status,
            "priority": self.priority,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class AuditLog(Base):
    """Audit trail for important events"""
    __tablename__ = "audit_logs"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Event details
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    event_type = Column(String(64), nullable=False, index=True)  # e.g., "scan_started", "scan_completed"
    scan_id = Column(String(36), nullable=True, index=True)
    
    # Actor information
    user_id = Column(String(64), nullable=True, index=True)
    api_key = Column(String(64), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Event data
    event_data = Column(JSON, nullable=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "scan_id": self.scan_id,
            "user_id": self.user_id,
            "event_data": self.event_data,
        }
