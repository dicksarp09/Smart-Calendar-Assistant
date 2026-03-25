"""
Central Logging Module
Provides structured logging for the application
"""

import logging
import sys
from datetime import datetime
from typing import Optional
import json


class AppLogger:
    """Centralized logging for the application"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup_logger()
        return cls._instance
    
    def _setup_logger(self):
        """Set up logger configuration"""
        self.logger = logging.getLogger("calendar_agent")
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log("DEBUG", message, kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log("INFO", message, kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log("WARNING", message, kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self._log("ERROR", message, kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self._log("CRITICAL", message, kwargs)
    
    def _log(self, level: str, message: str, extra: dict):
        """Internal log method"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **extra
        }
        
        getattr(self.logger, level.lower())(json.dumps(log_data))


# Singleton logger
logger = AppLogger()


def log_request(method: str, path: str, user_id: str = None, 
                status_code: int = None, duration_ms: float = None):
    """Log HTTP request"""
    logger.info(
        f"{method} {path}",
        method=method,
        path=path,
        user_id=user_id,
        status_code=status_code,
        duration_ms=duration_ms
    )


def log_event_action(action: str, event_id: str, user_id: str, 
                    details: dict = None):
    """Log calendar event action"""
    logger.info(
        f"Event {action}: {event_id}",
        action=action,
        event_id=event_id,
        user_id=user_id,
        details=details or {}
    )


def log_agent_action(user_id: str, message: str, response: str = None,
                    action_taken: str = None):
    """Log agent interaction"""
    logger.info(
        f"Agent: {message[:50]}...",
        user_id=user_id,
        message=message,
        response=response,
        action_taken=action_taken
    )