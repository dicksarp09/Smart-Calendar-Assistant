"""
Security Enhancements Module
Rate limiting, encryption, and audit logging
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import defaultdict
import hashlib

from fastapi import HTTPException, status, Request


class RateLimiter:
    """In-memory rate limiter for API endpoints"""
    
    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
    
    def check_rate_limit(self, user_id: str, endpoint: str) -> bool:
        """
        Check if user has exceeded rate limit for endpoint.
        
        Returns True if allowed, raises 429 if exceeded.
        """
        key = f"{user_id}:{endpoint}"
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        self.requests[key] = [t for t in self.requests[key] if t > minute_ago]
        
        if len(self.requests[key]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        self.requests[key].append(now)
        return True
    
    def get_remaining(self, user_id: str, endpoint: str) -> int:
        """Get remaining requests for user/endpoint"""
        key = f"{user_id}:{endpoint}"
        now = time.time()
        minute_ago = now - 60
        
        current_requests = [t for t in self.requests[key] if t > minute_ago]
        return max(0, self.requests_per_minute - len(current_requests))


class AuditLogger:
    """Audit logging for security and compliance"""
    
    @staticmethod
    def log_action(user_id: str, action: str, resource: str, 
                   details: Dict = None, success: bool = True):
        """
        Log critical actions for audit trail.
        
        Args:
            user_id: Who performed the action
            action: What action (create/update/delete/schedule/query)
            resource: Resource type (event, user, agent)
            details: Additional details
            success: Whether action succeeded
        """
        from backend.app.utils.logger import logger
        
        log_data = {
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "details": details or {},
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if success:
            logger.info(f"AUDIT: {action} on {resource} by {user_id}", **log_data)
        else:
            logger.error(f"AUDIT FAILED: {action} on {resource} by {user_id}", **log_data)
    
    @staticmethod
    def log_auth_event(user_id: str, event: str, success: bool):
        """Log authentication events"""
        from backend.app.utils.logger import logger
        
        logger.info(
            f"AUTH: {event} for {user_id}",
            user_id=user_id,
            event=event,
            success=success,
            timestamp=datetime.utcnow().isoformat()
        )


class DataEncryptor:
    """Encryption for sensitive data at rest"""
    
    def __init__(self):
        self._key = None
        self._setup_key()
    
    def _setup_key(self):
        """Setup encryption key from environment"""
        import os
        key = os.getenv("ENCRYPTION_KEY", "")
        
        if key:
            import base64
            # Decode key or generate from hash
            try:
                self._key = base64.urlsafe_b64decode(key)
            except:
                # Generate key from string
                self._key = hashlib.sha256(key.encode()).digest()
        else:
            self._key = None
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        if not self._key:
            return data
        
        from cryptography.fernet import Fernet
        f = Fernet(self._key)
        return f.encrypt(data.encode()).decode()
    
    def decrypt(self, data: str) -> str:
        """Decrypt string data"""
        if not self._key:
            return data
        
        from cryptography.fernet import Fernet
        f = Fernet(self._key)
        return f.decrypt(data.encode()).decode()
    
    def encrypt_dict(self, data: dict) -> dict:
        """Encrypt sensitive fields in dict"""
        sensitive_fields = ["preferences", "scheduling_rules", "api_keys"]
        result = data.copy()
        
        for field in sensitive_fields:
            if field in result and result[field]:
                if isinstance(result[field], str):
                    result[field] = self.encrypt(result[field])
                elif isinstance(result[field], dict):
                    result[field] = self.encrypt(str(result[field]))
        
        return result
    
    def decrypt_dict(self, data: dict) -> dict:
        """Decrypt sensitive fields in dict"""
        return data  # Implement based on needs


# Singleton instances
rate_limiter = RateLimiter()
audit_logger = AuditLogger()
encryptor = DataEncryptor()