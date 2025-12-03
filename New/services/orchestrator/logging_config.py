"""
Structured JSON logging configuration for Web3 Hunter
Provides consistent, parseable logs for production monitoring
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Add service information
        log_record['service'] = 'orchestrator'
        log_record['environment'] = 'production'
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add logger name
        log_record['logger'] = record.name
        
        # Add source location
        log_record['source'] = {
            'file': record.pathname,
            'line': record.lineno,
            'function': record.funcName
        }


def setup_json_logging(log_level: str = "INFO"):
    """
    Configure structured JSON logging for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Create console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    
    # JSON format string
    format_str = '%(timestamp)s %(level)s %(service)s %(logger)s %(message)s'
    formatter = CustomJsonFormatter(format_str)
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Log startup
    root_logger.info("Structured JSON logging initialized", extra={
        'log_level': log_level,
        'formatter': 'json'
    })
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance with JSON formatting
    """
    return logging.getLogger(name)


# Logging helper functions
def log_scan_started(scan_id: str, target: str, chain: str):
    """Log scan start event"""
    logger = get_logger(__name__)
    logger.info("Scan started", extra={
        'event': 'scan_started',
        'scan_id': scan_id,
        'target': target,
        'chain': chain
    })


def log_scan_completed(scan_id: str, duration: float, status: str):
    """Log scan completion event"""
    logger = get_logger(__name__)
    logger.info("Scan completed", extra={
        'event': 'scan_completed',
        'scan_id': scan_id,
        'duration_seconds': duration,
        'status': status
    })


def log_scan_failed(scan_id: str, error: str, stage: str = None):
    """Log scan failure event"""
    logger = get_logger(__name__)
    logger.error("Scan failed", extra={
        'event': 'scan_failed',
        'scan_id': scan_id,
        'error': error,
        'stage': stage
    })


def log_agent_call(agent_name: str, endpoint: str, duration: float, status_code: int):
    """Log agent API call"""
    logger = get_logger(__name__)
    logger.info("Agent call completed", extra={
        'event': 'agent_call',
        'agent': agent_name,
        'endpoint': endpoint,
        'duration_ms': duration * 1000,
        'status_code': status_code
    })


def log_database_operation(operation: str, table: str, duration: float, success: bool):
    """Log database operation"""
    logger = get_logger(__name__)
    level = logging.INFO if success else logging.ERROR
    logger.log(level, "Database operation", extra={
        'event': 'database_operation',
        'operation': operation,
        'table': table,
        'duration_ms': duration * 1000,
        'success': success
    })
