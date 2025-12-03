"""
Orchestrator Service - Database Helper Functions
Helper functions for database operations
"""

from models import Scan, StageResult, ScanStatus as DBScanStatus
from database import get_db
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


def create_scan_in_db(scan_id: str, target_url: str, contract_address: str, chain: str, scan_config: dict) -> Scan:
    """Create a new scan in the database"""
    with get_db() as db:
        scan = Scan(
            scan_id=scan_id,
            target_url=target_url or None,
            contract_address=contract_address or None,
            chain=chain,
            scan_config=scan_config,
            status=DBScanStatus.PENDING,
            progress=0
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        return scan


def update_scan_status(scan_id: str, status: str, progress: int = None, current_stage: str = None, error: str = None, completed_at: Any = None, duration_seconds: float = None):
    """Update scan status and progress"""
    from datetime import datetime
    with get_db() as db:
        scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
        if scan:
            scan.status = DBScanStatus(status)
            if progress is not None:
                scan.progress = progress
            if current_stage:
                scan.current_stage = current_stage
            if error:
                scan.error_message = error
            if completed_at:
                scan.completed_at = completed_at if isinstance(completed_at, datetime) else datetime.fromisoformat(str(completed_at)) if isinstance(completed_at, str) else datetime.utcnow()
            if duration_seconds is not None:
                scan.duration_seconds = duration_seconds
            db.commit()


def get_scan_from_db(scan_id: str) -> Optional[Scan]:
    """Get scan by ID"""
    with get_db() as db:
        return db.query(Scan).filter(Scan.scan_id == scan_id).first()


def save_stage_result(scan_id: str, stage_name: str, stage_order: int, result_data: dict, status: str = "completed"):
    """Save stage result to database"""
    with get_db() as db:
        from datetime import datetime
        stage_result = StageResult(
            scan_id=scan_id,
            stage_name=stage_name,
            stage_order=stage_order,
            status=status,
            result_data=result_data,
            completed_at=datetime.utcnow()
        )
        db.add(stage_result)
        db.commit()


def get_all_stage_results(scan_id: str) -> Dict[str, Any]:
    """Get all stage results for a scan"""
    with get_db() as db:
        results = db.query(StageResult).filter(StageResult.scan_id == scan_id).order_by(StageResult.stage_order).all()
        return {result.stage_name: result.result_data for result in results}


def list_scans(limit: int = 50, status: str = None) -> list:
    """List recent scans"""
    with get_db() as db:
        query = db.query(Scan).order_by(Scan.created_at.desc())
        if status:
            query = query.filter(Scan.status == DBScanStatus(status))
        return query.limit(limit).all()


def create_job_record(job_id: str, scan_id: str, job_type: str):
    """Create job queue record for Celery task tracking"""
    from datetime import datetime
    with get_db() as db:
        from models import JobQueue
        job = JobQueue(
            job_id=job_id,
            scan_id=scan_id,
            job_type=job_type,
            status="pending",
            created_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()


def update_job_status(job_id: str, status: str, result_data: dict = None, error: str = None):
    """Update Celery job status in database"""
    from datetime import datetime
    with get_db() as db:
        from models import JobQueue
        job = db.query(JobQueue).filter(JobQueue.job_id == job_id).first()
        if job:
            job.status = status
            if result_data:
                job.result_data = result_data
            if error:
                job.error_message = error
            if status in ["completed", "failed"]:
                job.completed_at = datetime.utcnow()
            db.commit()
