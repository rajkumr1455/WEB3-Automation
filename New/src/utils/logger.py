"""
Structured logging configuration
"""

import logging
import sys
from datetime import datetime
import json


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "scan_id"):
            log_data["scan_id"] = record.scan_id
        
        if hasattr(record, "agent"):
            log_data["agent"] = record.agent
        
        return json.dumps(log_data)


def setup_logging(service_name: str, log_level: str = "INFO"):
    """Setup structured logging for a service"""
    
    # Create logger
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


# Example usage:
# logger = setup_logging("recon-agent")
# logger.info("Starting reconnaissance", extra={"scan_id": "123"})
