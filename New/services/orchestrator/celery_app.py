"""
Celery app - ABSOLUTE MINIMUM
"""
from celery import Celery
import os

# Create app
celery_app = Celery('web3hunter')
celery_app.conf.broker_url = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
celery_app.conf.result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/1')

# Minimal config
celery_app.conf.task_serializer = 'json'
celery_app.conf.result_serializer = 'json'
celery_app.conf.accept_content = ['json']

# Task definition
@celery_app.task(name='run_scan')
def run_scan_task(scan_id, scan_request):
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Processing scan {scan_id}")
        from app import run_scan_pipeline_sync
        from models import ScanRequest
        run_scan_pipeline_sync(scan_id, ScanRequest(**scan_request))
        return {"status": "completed", "scan_id": scan_id}
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        raise
