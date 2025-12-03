"""
RQ (Redis Queue) Worker Configuration
Simple background job processing
"""
import os
from redis import Redis
from rq import Queue
import logging

logger = logging.getLogger(__name__)

# Redis connection for RQ
redis_conn = Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0))
)

# Create job queue
job_queue = Queue('scans', connection=redis_conn)


def queue_scan_job(scan_id: str, scan_request: dict) -> str:
    """
    Queue a scan job using RQ
    
    Args:
        scan_id: Scan ID
        scan_request: Scan request dictionary
        
    Returns:
        Job ID
    """
    from rq_tasks import run_scan_task
    
    try:
        job = job_queue.enqueue(
            run_scan_task,
            scan_id,
            scan_request,
            job_timeout='30m',  # 30 minute timeout
            result_ttl=3600,  # Keep result for 1 hour
            failure_ttl=86400  # Keep failed job for 24 hours
        )
        
        logger.info(f"Queued scan {scan_id} to RQ (job: {job.id})")
        return job.id
        
    except Exception as e:
        logger.error(f"Failed to queue scan: {e}")
        raise


def get_job_status(job_id: str) -> dict:
    """Get status of an RQ job"""
    from rq.job import Job
    
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        return {
            'job_id': job.id,
            'status': job.get_status(),
            'result': job.result if job.is_finished else None,
            'exc_info': job.exc_info if job.is_failed else None
        }
    except Exception as e:
        return {'job_id': job_id, 'status': 'unknown', 'error': str(e)}
