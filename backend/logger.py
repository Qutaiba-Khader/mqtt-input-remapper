"""
Logging Module
Provides centralized logging configuration with rotating file handler
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

LOG_DIR = os.path.expanduser("~/.local/share/mqtt-remapper/logs")
LOG_FILE = "mqtt-remapper.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5


class LogManager:
    """Manages application logging"""
    
    def __init__(self, log_dir: Optional[str] = None, log_level: str = "INFO"):
        """Initialize log manager"""
        self.log_dir = log_dir or LOG_DIR
        self.log_file = os.path.join(self.log_dir, LOG_FILE)
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.logs_buffer = []
        self.max_buffer_size = 1000
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging configuration"""
        # Ensure log directory exists
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Create rotating file handler
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(self.log_level)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(self.log_level)
        
        # Create buffer handler for UI
        buffer_handler = BufferHandler(self.logs_buffer, self.max_buffer_size)
        buffer_handler.setFormatter(formatter)
        buffer_handler.setLevel(logging.DEBUG)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(buffer_handler)
        
        logging.info(f"Logging initialized - log file: {self.log_file}")
    
    def set_log_level(self, level: str):
        """Change log level dynamically"""
        self.log_level = getattr(logging, level.upper(), logging.INFO)
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            if not isinstance(handler, BufferHandler):
                handler.setLevel(self.log_level)
        logging.info(f"Log level changed to {level}")
    
    def get_logs(self, level: Optional[str] = None, limit: int = 100) -> list:
        """Get recent logs from buffer"""
        logs = self.logs_buffer[-limit:]
        if level:
            level_upper = level.upper()
            logs = [log for log in logs if level_upper in log]
        return logs
    
    def clear_logs(self):
        """Clear log buffer"""
        self.logs_buffer.clear()
        logging.info("Log buffer cleared")
    
    def get_log_file_path(self) -> str:
        """Get path to log file"""
        return self.log_file


class BufferHandler(logging.Handler):
    """Custom handler that stores logs in memory buffer"""
    
    def __init__(self, buffer: list, max_size: int):
        super().__init__()
        self.buffer = buffer
        self.max_size = max_size
    
    def emit(self, record):
        """Add log record to buffer"""
        try:
            msg = self.format(record)
            self.buffer.append(msg)
            
            # Keep buffer size limited
            if len(self.buffer) > self.max_size:
                self.buffer.pop(0)
        except Exception:
            self.handleError(record)


# Global log manager instance
log_manager = LogManager()
