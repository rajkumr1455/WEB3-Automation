"""
Phase 2 Pipeline Tests - InMemory Mode
Tests full scan pipeline using InMemoryAdapter (no DB required)
"""

import pytest
import sys
import os

# Add services to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))

from persistence import create_persistence_adapter, ScanStatus


@pytest.fixture
def inmemory_persistence():
    """Create InMemory persistence adapter"""
    adapter = create_persistence_adapter(None)  # Force InMemory
    return adapter


def test_save_and_retrieve_scan(inmemory_persistence):
    """Test saving and retrieving a scan"""
    scan_data = {
        "target_url": "https://github.com/test/repo",
        "contract_address": "0xDEADBEEF",
        "chain": "ethereum",
        "status": ScanStatus.PENDING.value
    }
    
    # Save scan
    scan_id = inmemory_persistence.save_scan(scan_data)
    assert scan_id is not None
    
    # Retrieve scan
    retrieved = inmemory_persistence.get_scan(scan_id)
    assert retrieved is not None
    assert retrieved["scan_id"] == scan_id
    assert retrieved["chain"] == "ethereum"
    assert retrieved["status"] == ScanStatus.PENDING.value


def test_update_scan_status(inmemory_persistence):
    """Test updating scan status"""
    scan_data = {
        "contract_address": "0x123",
        "chain": "ethereum"
    }
    
    scan_id = inmemory_persistence.save_scan(scan_data)
    
    # Update status
    success = inmemory_persistence.update_scan(scan_id, {
        "status": ScanStatus.RUNNING.value,
        "progress": 50
    })
    
    assert success == True
    
    # Verify update
    updated = inmemory_persistence.get_scan(scan_id)
    assert updated["status"] == ScanStatus.RUNNING.value
    assert updated["progress"] == 50


def test_list_scans(inmemory_persistence):
    """Test listing scans"""
    # Create multiple scans
    for i in range(5):
        inmemory_persistence.save_scan({
            "contract_address": f"0x{i}",
            "chain": "ethereum",
            "status": ScanStatus.PENDING.value if i < 3 else ScanStatus.COMPLETED.value
        })
    
    # List all
    all_scans = inmemory_persistence.list_scans(limit=10)
    assert len(all_scans) == 5
    
    # List pending only
    pending = inmemory_persistence.list_scans(limit=10, status=ScanStatus.PENDING.value)
    assert len(pending) == 3


def test_list_pending_scans(inmemory_persistence):
    """Test listing pending scans specifically"""
    # Create scans with different statuses
    inmemory_persistence.save_scan({"status": ScanStatus.PENDING.value})
    inmemory_persistence.save_scan({"status": ScanStatus.RUNNING.value})
    inmemory_persistence.save_scan({"status": ScanStatus.PENDING.value})
    inmemory_persistence.save_scan({"status": ScanStatus.COMPLETED.value})
    
    pending = inmemory_persistence.list_pending_scans()
    assert len(pending) == 2


def test_health_check(inmemory_persistence):
    """Test health check"""
    assert inmemory_persistence.health_check() == True


def test_idempotent_updates(inmemory_persistence):
    """Test that updates are idempotent"""
    scan_data = {"contract_address": "0xABC"}
    scan_id = inmemory_persistence.save_scan(scan_data)
    
    # Update multiple times with same data
    for _ in range(3):
        inmemory_persistence.update_scan(scan_id, {
            "status": ScanStatus.COMPLETED.value,
            "progress": 100
        })
    
    # Should still have correct final state
    scan = inmemory_persistence.get_scan(scan_id)
    assert scan["status"] == ScanStatus.COMPLETED.value
    assert scan["progress"] == 100


def test_nonexistent_scan_update(inmemory_persistence):
    """Test updating non-existent scan"""
    success = inmemory_persistence.update_scan("fake-id", {"status": "running"})
    assert success == False


def test_nonexistent_scan_retrieval(inmemory_persistence):
    """Test retrieving non-existent scan"""
    scan = inmemory_persistence.get_scan("fake-id")
    assert scan is None


@pytest.mark.asyncio
async def test_simulated_pipeline(inmemory_persistence):
    """Simulate full pipeline using inmemory adapter"""
    # Stage 0: Submit scan
    scan_data = {
        "contract_address": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
        "chain": "ethereum",
        "status": ScanStatus.PENDING.value,
        "artifacts": {}
    }
    scan_id = inmemory_persistence.save_scan(scan_data)
    
    # Stage 1: Address scanning (running)
    inmemory_persistence.update_scan(scan_id, {
        "status": ScanStatus.RUNNING.value,
        "current_stage": "address_scan",
        "progress": 10
    })
    
    # Stage 2: Reconnaissance
    inmemory_persistence.update_scan(scan_id, {
        "current_stage": "recon",
        "progress": 30,
        "artifacts": {"address_scan": {"source_found": True}}
    })
    
    # Stage 3: Static analysis
    inmemory_persistence.update_scan(scan_id, {
        "current_stage": "static",
        "progress": 50,
        "artifacts": {
            "address_scan": {"source_found": True},
            "recon": {"contracts": ["Contract1"]}
        }
    })
    
    # Stage 4: Fuzzing
    inmemory_persistence.update_scan(scan_id, {
        "current_stage": "fuzzing",
        "progress": 70
    })
    
    # Stage 5: Complete
    inmemory_persistence.update_scan(scan_id, {
        "status": ScanStatus.COMPLETED.value,
        "current_stage": "completed",
        "progress": 100
    })
    
    # Verify final state
    final_scan = inmemory_persistence.get_scan(scan_id)
    assert final_scan["status"] == ScanStatus.COMPLETED.value
    assert final_scan["progress"] == 100
    assert "address_scan" in final_scan["artifacts"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
