"""
RQ Task Definitions
Background tasks for scan processing
"""
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_scan_task(scan_id: str, scan_request: dict):
    """RQ task to execute scan pipeline"""
    try:
        logger.info(f"[RQ] Starting scan {scan_id}")
        
        # Import here to avoid circular dependencies
        from app import run_scan_pipeline, ScanRequest as ScanRequestModel
        
        # Convert dict to model
        request = ScanRequestModel(**scan_request)
        
        # Run async pipeline in sync context
        asyncio.run(run_scan_pipeline(scan_id, request))
        
        logger.info(f"[RQ] Scan {scan_id} completed successfully")
        
        return {
            'scan_id': scan_id,
            'status': 'completed'
        }
        
    except Exception as exc:
        logger.error(f"[RQ] Scan {scan_id} failed: {exc}")
        
        # Update scan status
        try:
            from db_helpers import update_scan_status
            update_scan_status(scan_id, "failed", error=str(exc))
        except Exception as e:
            logger.error(f"Failed to update status: {e}")
        
        raise