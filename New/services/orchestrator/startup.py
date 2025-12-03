"""
Startup Migration Logic
Handles seamless InMemory → PostgreSQL migration on orchestrator startup
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def perform_startup_migration(persistence_adapter):
    """
    Perform startup migration if PostgreSQL is available
    and InMemory adapter has data
    
    Args:
        persistence_adapter: Current persistence adapter
    
    Returns:
        PersistenceAdapter: Possibly migrated adapter
    """
    from persistence import create_persistence_adapter, InMemoryAdapter, PostgresAdapter
    
    db_url = os.getenv("DATABASE_URL")
    
    # If no DATABASE_URL, continue with current adapter
    if not db_url:
        logger.info("📦 Using InMemoryAdapter (no DATABASE_URL configured)")
        return persistence_adapter
    
    # If already using PostgresAdapter, no migration needed
    if isinstance(persistence_adapter, PostgresAdapter):
        logger.info("✅ Already using PostgresAdapter")
        return persistence_adapter
    
    # If InMemoryAdapter and DATABASE_URL present, attempt migration
    if isinstance(persistence_adapter, InMemoryAdapter):
        try:
            logger.info("🔄 DATABASE_URL detected, attempting migration...")
            
            # Create PostgreSQL adapter
            postgres_adapter = create_persistence_adapter(db_url)
            
            if not isinstance(postgres_adapter, PostgresAdapter):
                logger.warning("⚠️ PostgreSQL unavailable, continuing with InMemory")
                return persistence_adapter
            
            # Check if PostgreSQL is healthy
            if not postgres_adapter.health_check():
                logger.warning("⚠️ PostgreSQL unhealthy, continuing with InMemory")
                return persistence_adapter
            
            # Migrate data from InMemory to PostgreSQL
            in_memory_scans = persistence_adapter.get_all_scans()
            
            if in_memory_scans:
                logger.info(f"📊 Migrating {len(in_memory_scans)} scans to PostgreSQL...")
                
                migrated_count = 0
                for scan in in_memory_scans:
                    try:
                        scan["migrated"] = True
                        postgres_adapter.save_scan(scan)
                        migrated_count += 1
                    except Exception as e:
                        logger.error(f"❌ Failed to migrate scan {scan.get('scan_id')}: {e}")
                
                logger.info(f"✅ Migrated {migrated_count}/{len(in_memory_scans)} scans")
                
                # Mark InMemory as migrated and clear
                persistence_adapter.mark_migrated()
            else:
                logger.info("ℹ️ No scans to migrate")
            
            logger.info("✅ Migration complete, switching to PostgresAdapter")
            return postgres_adapter
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}, continuing with InMemory")
            return persistence_adapter
    
    return persistence_adapter


def initialize_persistence(force_inmemory: bool = False) -> 'PersistenceAdapter':
    """
    Initialize persistence adapter with migration support
    
    Args:
        force_inmemory: Force use of InMemoryAdapter (for testing)
    
    Returns:
        PersistenceAdapter instance
    """
    from persistence import create_persistence_adapter
    
    if force_inmemory:
        logger.info("🔧 Forcing InMemoryAdapter (testing mode)")
        adapter = create_persistence_adapter(None)
    else:
        db_url = os.getenv("DATABASE_URL")
        adapter = create_persistence_adapter(db_url)
    
    # Log adapter type
    adapter_type = type(adapter).__name__
    logger.info(f"📦 Persistence: {adapter_type}")
    
    return adapter


def get_persistence_status(adapter) -> dict:
    """
    Get persistence adapter status
    
    Returns:
        dict with adapter type and health
    """
    from persistence import InMemoryAdapter, PostgresAdapter
    
    is_healthy = adapter.health_check()
    adapter_type = type(adapter).__name__
    
    status = {
        "adapter": adapter_type,
        "healthy": is_healthy,
        "database_url_configured": bool(os.getenv("DATABASE_URL"))
    }
    
    if isinstance(adapter, PostgresAdapter):
        status["connection_pool"] = "active"
    elif isinstance(adapter, InMemoryAdapter):
        try:
            status["scan_count"] = len(adapter.get_all_scans())
        except:
            status["scan_count"] = 0
    
    return status
