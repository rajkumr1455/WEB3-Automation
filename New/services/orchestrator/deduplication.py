"""
Request Deduplication Module
Prevents duplicate scans using Redis cache
"""
import hashlib
import redis
import json
import logging
from typing import Optional, Dict, Any
from config import REDIS_HOST, REDIS_PORT, REDIS_DB, DEDUP_TTL_SECONDS, ENABLE_DEDUPLICATION

logger = logging.getLogger(__name__)

# Redis client for deduplication
redis_client = None


def init_redis():
    """Initialize Redis connection for deduplication"""
    global redis_client
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )
        redis_client.ping()
        logger.info("Deduplication Redis initialized", extra={
            'event': 'redis_init',
            'host': REDIS_HOST,
            'port': REDIS_PORT
        })
    except Exception as e:
        logger.error(f"Failed to initialize deduplication Redis: {e}", extra={
            'event': 'redis_init_failed',
            'error': str(e)
        })
        redis_client = None


def get_scan_hash(scan_request: Dict[str, Any]) -> str:
    """
    Generate unique hash for a scan request
    
    Args:
        scan_request: Scan request dict
        
    Returns:
        SHA256 hash string
    """
    # Create unique identifier from critical fields
    contract = scan_request.get('contract_address', '')
    target = scan_request.get('target_url', '')
    chain = scan_request.get('chain', 'ethereum')
    
    # Combine to create unique key
    unique_str = f"{contract}:{target}:{chain}".lower()
    
    # Hash it
    return hashlib.sha256(unique_str.encode()).hexdigest()


def check_duplicate_scan(scan_request: Dict[str, Any]) -> Optional[str]:
    """
    Check if scan request is a duplicate
    
    Args:
        scan_request: Scan request dict
        
    Returns:
        Existing scan_id if duplicate, None otherwise
    """
    if not ENABLE_DEDUPLICATION or redis_client is None:
        return None
    
    try:
        scan_hash = get_scan_hash(scan_request)
        key = f"scan_dedup:{scan_hash}"
        
        # Check if exists in Redis
        existing_scan_id = redis_client.get(key)
        
        if existing_scan_id:
            logger.info("Duplicate scan detected", extra={
                'event': 'duplicate_scan',
                'scan_hash': scan_hash[:16],
                'existing_scan_id': existing_scan_id
            })
            return existing_scan_id
        
        return None
        
    except Exception as e:
        logger.error(f"Deduplication check failed: {e}", extra={
            'event': 'dedup_check_failed',
            'error': str(e)
        })
        # Fail open - allow scan if Redis fails
        return None


def register_scan(scan_request: Dict[str, Any], scan_id: str):
    """
    Register a new scan in deduplication cache
    
    Args:
        scan_request: Scan request dict
        scan_id: New scan ID
    """
    if not ENABLE_DEDUPLICATION or redis_client is None:
        return
    
    try:
        scan_hash = get_scan_hash(scan_request)
        key = f"scan_dedup:{scan_hash}"
        
        # Store with TTL
        redis_client.setex(key, DEDUP_TTL_SECONDS, scan_id)
        
        logger.info("Scan registered in dedup cache", extra={
            'event': 'scan_registered',
            'scan_id': scan_id,
            'ttl_seconds': DEDUP_TTL_SECONDS
        })
        
    except Exception as e:
        logger.error(f"Failed to register scan in dedup cache: {e}", extra={
            'event': 'dedup_register_failed',
            'error': str(e)
        })


def clear_dedup_cache():
    """Clear all deduplication entries (for testing)"""
    if redis_client is None:
        return
    
    try:
        # Find all dedup keys
        keys = redis_client.keys("scan_dedup:*")
        if keys:
            redis_client.delete(*keys)
            logger.info(f"Cleared {len(keys)} dedup entries", extra={
                'event': 'dedup_cache_cleared',
                'count': len(keys)
            })
    except Exception as e:
        logger.error(f"Failed to clear dedup cache: {e}")
