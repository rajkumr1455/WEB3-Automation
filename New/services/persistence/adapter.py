"""
Persistence Adapter Pattern
Provides seamless InMemory ↔ PostgreSQL migration
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid


class ScanStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PersistenceAdapter(ABC):
    """Abstract base class for persistence backends"""
    
    @abstractmethod
    def save_scan(self, scan: Dict[str, Any]) -> str:
        """Save a new scan, return scan_id"""
        pass
    
    @abstractmethod
    def update_scan(self, scan_id: str, updates: Dict[str, Any]) -> bool:
        """Update scan fields, return success"""
        pass
    
    @abstractmethod
    def get_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get scan by ID"""
        pass
    
    @abstractmethod
    def list_scans(self, limit: int = 50, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List scans with optional status filter"""
        pass
    
    @abstractmethod
    def list_pending_scans(self) -> List[Dict[str, Any]]:
        """List all pending scans (for recovery)"""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if backend is healthy"""
        pass


class InMemoryAdapter(PersistenceAdapter):
    """In-memory persistence (current default)"""
    
    def __init__(self):
        self._scans: Dict[str, Dict[str, Any]] = {}
        self._migrated = False
    
    def save_scan(self, scan: Dict[str, Any]) -> str:
        scan_id = scan.get("scan_id") or str(uuid.uuid4())
        scan["scan_id"] = scan_id
        scan.setdefault("created_at", datetime.now().isoformat())
        scan.setdefault("updated_at", datetime.now().isoformat())
        scan.setdefault("status", ScanStatus.PENDING.value)
        self._scans[scan_id] = scan
        return scan_id
    
    def update_scan(self, scan_id: str, updates: Dict[str, Any]) -> bool:
        if scan_id not in self._scans:
            return False
        self._scans[scan_id].update(updates)
        self._scans[scan_id]["updated_at"] = datetime.now().isoformat()
        return True
    
    def get_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        return self._scans.get(scan_id)
    
    def list_scans(self, limit: int = 50, status: Optional[str] = None) -> List[Dict[str, Any]]:
        scans = list(self._scans.values())
        if status:
            scans = [s for s in scans if s.get("status") == status]
        # Sort by created_at descending
        scans.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return scans[:limit]
    
    def list_pending_scans(self) -> List[Dict[str, Any]]:
        return [s for s in self._scans.values() if s.get("status") == ScanStatus.PENDING.value]
    
    def health_check(self) -> bool:
        return True
    
    def get_all_scans(self) -> List[Dict[str, Any]]:
        """Get all scans (for migration)"""
        return list(self._scans.values())
    
    def mark_migrated(self):
        """Mark as migrated"""
        self._migrated = True
        self._scans.clear()  # Clear in-memory after migration


class PostgresAdapter(PersistenceAdapter):
    """PostgreSQL persistence"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self._engine = None
        self._Session = None
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize SQLAlchemy engine and session"""
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from .models import Base
            
            self._engine = create_engine(
                self.db_url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
            
            # Create tables if they don't exist
            Base.metadata.create_all(self._engine)
            
            self._Session = sessionmaker(bind=self._engine)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize PostgreSQL: {e}")
    
    def _get_session(self):
        """Get database session"""
        return self._Session()
    
    def save_scan(self, scan: Dict[str, Any]) -> str:
        """Save scan to PostgreSQL"""
        from .models import Scan
        
        scan_id = scan.get("scan_id") or str(uuid.uuid4())
        
        with self._get_session() as session:
            db_scan = Scan(
                scan_id=scan_id,
                target_url=scan.get("target_url", ""),
                contract_address=scan.get("contract_address", ""),
                chain=scan.get("chain", "ethereum"),
                status=scan.get("status", ScanStatus.PENDING.value),
                scan_config=scan.get("scan_config", {}),
                artifacts=scan.get("artifacts", {}),
                error_message=scan.get("error"),
                progress=scan.get("progress", 0),
                current_stage=scan.get("current_stage", "pending")
            )
            session.add(db_scan)
            session.commit()
        
        return scan_id
    
    def update_scan(self, scan_id: str, updates: Dict[str, Any]) -> bool:
        """Update scan in PostgreSQL"""
        from .models import Scan
        
        with self._get_session() as session:
            scan = session.query(Scan).filter(Scan.scan_id == scan_id).first()
            if not scan:
                return False
            
            for key, value in updates.items():
                if hasattr(scan, key):
                    setattr(scan, key, value)
            
            scan.updated_at = datetime.utcnow()
            session.commit()
            return True
    
    def get_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get scan from PostgreSQL"""
        from .models import Scan
        
        with self._get_session() as session:
            scan = session.query(Scan).filter(Scan.scan_id == scan_id).first()
            if not scan:
                return None
            
            return {
                "scan_id": scan.scan_id,
                "target_url": scan.target_url,
                "contract_address": scan.contract_address,
                "chain": scan.chain,
                "status": scan.status,
                "scan_config": scan.scan_config,
                "artifacts": scan.artifacts,
                "error": scan.error_message,
                "progress": scan.progress,
                "current_stage": scan.current_stage,
                "created_at": scan.created_at.isoformat() if scan.created_at else None,
                "updated_at": scan.updated_at.isoformat() if scan.updated_at else None,
                "completed_at": scan.completed_at.isoformat() if scan.completed_at else None
            }
    
    def list_scans(self, limit: int = 50, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List scans from PostgreSQL"""
        from .models import Scan
        
        with self._get_session() as session:
            query = session.query(Scan).order_by(Scan.created_at.desc())
            
            if status:
                query = query.filter(Scan.status == status)
            
            scans = query.limit(limit).all()
            
            return [
                {
                    "scan_id": s.scan_id,
                    "target_url": s.target_url,
                    "contract_address": s.contract_address,
                    "chain": s.chain,
                    "status": s.status,
                    "progress": s.progress,
                    "current_stage": s.current_stage,
                    "created_at": s.created_at.isoformat() if s.created_at else None
                }
                for s in scans
            ]
    
    def list_pending_scans(self) -> List[Dict[str, Any]]:
        """List pending scans from PostgreSQL"""
        return self.list_scans(limit=1000, status=ScanStatus.PENDING.value)
    
    def health_check(self) -> bool:
        """Check PostgreSQL health"""
        try:
            with self._get_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception:
            return False


def create_persistence_adapter(db_url: Optional[str] = None) -> PersistenceAdapter:
    """
    Factory function to create appropriate persistence adapter
    
    Args:
        db_url: PostgreSQL connection string. If None, uses InMemoryAdapter
    
    Returns:
        PersistenceAdapter instance
    """
    if db_url:
        try:
            adapter = PostgresAdapter(db_url)
            if adapter.health_check():
                return adapter
            else:
                print("⚠️ PostgreSQL unreachable, falling back to InMemory")
                return InMemoryAdapter()
        except Exception as e:
            print(f"⚠️ PostgreSQL initialization failed: {e}, falling back to InMemory")
            return InMemoryAdapter()
    else:
        return InMemoryAdapter()
