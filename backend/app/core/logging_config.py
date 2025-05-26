"""
Logging configuration for the cybersecurity intelligence platform
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry)

def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    max_file_size_mb: int = 100,
    backup_count: int = 5,
    enable_console: bool = True,
    enable_json: bool = True
):
    """Setup logging configuration"""
    
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler for general logs
    file_handler = logging.handlers.RotatingFileHandler(
        log_path / "cybersec_intel.log",
        maxBytes=max_file_size_mb * 1024 * 1024,
        backupCount=backup_count
    )
    
    if enable_json:
        file_formatter = JSONFormatter()
    else:
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
    
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Separate handler for errors
    error_handler = logging.handlers.RotatingFileHandler(
        log_path / "errors.log",
        maxBytes=max_file_size_mb * 1024 * 1024,
        backupCount=backup_count
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # Separate handler for scraping activities
    scraping_handler = logging.handlers.RotatingFileHandler(
        log_path / "scraping.log",
        maxBytes=max_file_size_mb * 1024 * 1024,
        backupCount=backup_count
    )
    scraping_formatter = JSONFormatter() if enable_json else file_formatter
    scraping_handler.setFormatter(scraping_formatter)
    
    # Create scraping logger
    scraping_logger = logging.getLogger("scraping")
    scraping_logger.addHandler(scraping_handler)
    scraping_logger.propagate = False
    
    # Separate handler for analysis activities
    analysis_handler = logging.handlers.RotatingFileHandler(
        log_path / "analysis.log",
        maxBytes=max_file_size_mb * 1024 * 1024,
        backupCount=backup_count
    )
    analysis_formatter = JSONFormatter() if enable_json else file_formatter
    analysis_handler.setFormatter(analysis_formatter)
    
    # Create analysis logger
    analysis_logger = logging.getLogger("analysis")
    analysis_logger.addHandler(analysis_handler)
    analysis_logger.propagate = False
    
    # Set specific log levels for external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("crawl4ai").setLevel(logging.INFO)
    
    logging.info("Logging configuration initialized")

class ContextLogger:
    """Logger with context information"""
    
    def __init__(self, name: str, context: Optional[dict] = None):
        self.logger = logging.getLogger(name)
        self.context = context or {}
    
    def _log_with_context(self, level: int, message: str, extra_fields: Optional[dict] = None):
        """Log message with context"""
        combined_extra = {**self.context}
        if extra_fields:
            combined_extra.update(extra_fields)
        
        # Create a custom LogRecord with extra fields
        record = self.logger.makeRecord(
            self.logger.name, level, "", 0, message, (), None
        )
        record.extra_fields = combined_extra
        self.logger.handle(record)
    
    def debug(self, message: str, **kwargs):
        self._log_with_context(logging.DEBUG, message, kwargs)
    
    def info(self, message: str, **kwargs):
        self._log_with_context(logging.INFO, message, kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log_with_context(logging.WARNING, message, kwargs)
    
    def error(self, message: str, **kwargs):
        self._log_with_context(logging.ERROR, message, kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log_with_context(logging.CRITICAL, message, kwargs)

def get_logger(name: str, context: Optional[dict] = None) -> ContextLogger:
    """Get a context-aware logger"""
    return ContextLogger(name, context)