"""
Configuration Module for Orchestrator
Centralized configuration for timeouts, limits, and constants
"""
import os

# ============================================================================
# AGENT TIMEOUTS (seconds)
# ============================================================================

# Per-agent timeout configuration
AGENT_TIMEOUTS = {
    "recon": int(os.getenv("RECON_TIMEOUT", "120")),  # 2 minutes
    "static": int(os.getenv("STATIC_TIMEOUT", "300")),  # 5 minutes
    "fuzzing": int(os.getenv("FUZZING_TIMEOUT", "600")),  # 10 minutes
    "monitoring": int(os.getenv("MONITORING_TIMEOUT", "180")),  # 3 minutes
    "triage": int(os.getenv("TRIAGE_TIMEOUT", "180")),  # 3 minutes
    "reporting": int(os.getenv("REPORTING_TIMEOUT", "120")),  # 2 minutes
    "address_scanner": int(os.getenv("ADDRESS_SCANNER_TIMEOUT", "90")),  # 1.5 minutes
}

# Default timeout for agents not in the map
DEFAULT_AGENT_TIMEOUT = int(os.getenv("DEFAULT_AGENT_TIMEOUT", "300"))  # 5 minutes

# Maximum total scan duration (timeout budget)
SCAN_TIMEOUT_BUDGET = int(os.getenv("SCAN_TIMEOUT_BUDGET", "1800"))  # 30 minutes


def get_agent_timeout(agent_name: str) -> int:
    """
    Get timeout for a specific agent
    
    Args:
        agent_name: Agent name (recon, static, etc.)
        
    Returns:
        Timeout in seconds
    """
    return AGENT_TIMEOUTS.get(agent_name, DEFAULT_AGENT_TIMEOUT)


# ============================================================================
# RATE LIMITING CONFIGURATION
# ============================================================================

RATE_LIMIT_GLOBAL = os.getenv("RATE_LIMIT_GLOBAL", "60/minute")
RATE_LIMIT_SCAN = os.getenv("RATE_LIMIT_SCAN", "10/minute")
RATE_LIMIT_STATUS = os.getenv("RATE_LIMIT_STATUS", "60/minute")


# ============================================================================
# CIRCUIT BREAKER CONFIGURATION
# ============================================================================

CIRCUIT_BREAKER_FAIL_MAX = int(os.getenv("CIRCUIT_BREAKER_FAIL_MAX", "5"))
CIRCUIT_BREAKER_TIMEOUT = int(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60"))


# ============================================================================
# DEDUPLICATION CONFIGURATION
# ============================================================================

# Deduplication cache TTL (how long to remember a scan)
DEDUP_TTL_SECONDS = int(os.getenv("DEDUP_TTL_SECONDS", "300"))  # 5 minutes

# Enable/disable deduplication
ENABLE_DEDUPLICATION = os.getenv("ENABLE_DEDUPLICATION", "true").lower() == "true"


# ============================================================================
# GRACEFUL SHUTDOWN CONFIGURATION
# ============================================================================

# Maximum wait time for active scans during shutdown
SHUTDOWN_WAIT_SECONDS = int(os.getenv("SHUTDOWN_WAIT_SECONDS", "30"))


# ============================================================================
# REDIS CONFIGURATION
# ============================================================================

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
