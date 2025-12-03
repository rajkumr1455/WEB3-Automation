"""
Migration Tests
Tests InMemory → PostgreSQL migration
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))

from persistence import InMemoryAdapter, create_persistence_adapter, ScanStatus
from orchestrator.startup import perform_startup_migration


@pytest.fixture
def inmemory_with_data():
    """Create InMemory adapter with sample data"""
    adapter = InMemoryAdapter()
    
    # Add sample scans
    for i in range(3):
        adapter.save_scan({
            "contract_address": f"0x{i:040x}",
            "chain": "ethereum",
            "status": ScanStatus.PENDING.value if i < 2 else ScanStatus.COMPLETED.value
        })
    
    return adapter


def test_inmemory_adapter_creation():
    """Test creating InMemory adapter"""
    adapter = InMemoryAdapter()
    assert adapter is not None
    assert adapter.health_check() == True


def test_migration_preparation(inmemory_with_data):
    """Test migration data preparation"""
    scans = inmemory_with_data.get_all_scans()
    assert len(scans) == 3
    assert all("scan_id" in scan for scan in scans)


def test_migration_with_no_db_url(inmemory_with_data):
    """Test migration attempt with no DATABASE_URL"""
    # Clear DATABASE_URL if present
    old_db_url = os.environ.get("DATABASE_URL")
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]
    
    try:
        result = perform_startup_migration(inmemory_with_data)
        
        # Should return same adapter (no migration)
        assert result is inmemory_with_data
        assert isinstance(result, InMemoryAdapter)
    finally:
        # Restore DATABASE_URL if it existed
        if old_db_url:
            os.environ["DATABASE_URL"] = old_db_url


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="Requires DATABASE_URL for integration test"
)
def test_real_migration(inmemory_with_data):
    """Test real migration to PostgreSQL (requires DATABASE_URL)"""
    db_url = os.getenv("DATABASE_URL")
    
    # Perform migration
    postgres_adapter = perform_startup_migration(inmemory_with_data)
    
    # Verify adapter type changed
    from persistence import PostgresAdapter
    assert isinstance(postgres_adapter, PostgresAdapter)
    
    # Verify data was migrated
    migrated_scans = postgres_adapter.list_scans(limit=10)
    assert len(migrated_scans) == 3
    
    # Cleanup test data
    # (We don't delete here to avoid affecting other tests)


def test_migration_marks_scans(inmemory_with_data):
    """Test that migration marks scans"""
    scans_before = inmemory_with_data.get_all_scans()
    
    # Mark as migrated
    inmemory_with_data.mark_migrated()
    
    # After marking, in-memory should be cleared
    scans_after = inmemory_with_data.get_all_scans()
    assert len(scans_after) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
