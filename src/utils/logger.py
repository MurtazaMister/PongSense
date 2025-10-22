"""
Logging system for PongSense with thread-safe operations.
"""

import logging
import threading
from typing import Optional
from pathlib import Path


class ThreadSafeLogger:
    """Thread-safe logger for PongSense."""
    
    _instance: Optional['ThreadSafeLogger'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'ThreadSafeLogger':
        """Singleton pattern for logger."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize logger if not already done."""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._logger = logging.getLogger('pongsense')
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Setup logger configuration."""
        # Clear any existing handlers
        self._logger.handlers.clear()
        
        # Set level
        self._logger.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)
        
        # File handler
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(log_dir / 'pongsense.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        self._logger.propagate = False
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        self._logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log info message."""
        self._logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        self._logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message."""
        self._logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log critical message."""
        self._logger.critical(message)
    
    def set_level(self, level: str) -> None:
        """Set logging level.
        
        Args:
            level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        if level.upper() in level_map:
            self._logger.setLevel(level_map[level.upper()])
            for handler in self._logger.handlers:
                handler.setLevel(level_map[level.upper()])


# Global logger instance
logger = ThreadSafeLogger()
