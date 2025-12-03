"""
Persistence Layer
Provides seamless InMemory ↔ PostgreSQL abstraction
"""

from .adapter import (
    PersistenceAdapter,
    InMemoryAdapter,
    PostgresAdapter,
    create_persistence_adapter,
    ScanStatus
)

from .models import Scan, JobQueue, StageResult, Base

__all__ = [
    "PersistenceAdapter",
    "InMemoryAdapter",
    "PostgresAdapter",
    "create_persistence_adapter",
    "ScanStatus",
    "Scan",
    "JobQueue",
    "StageResult",
    "Base"
]
