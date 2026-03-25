"""
Auth Middleware Module
FastAPI middleware for JWT verification
"""

import os
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.auth.auth0 import verify_auth0_token, TokenPayload


# Security scheme for HTTP Bearer token
security = HTTPBearer()


async def get_current_user_optional(request: Request) -> Optional[TokenPayload]:
    """
    Optional authentication - validates token if provided but doesn't require it.
    Use this for endpoints that should work with or without authentication.
    """
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    
    # If no credentials provided, return None (optional auth)
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.replace("Bearer ", "")
    
    # If credentials provided, validate them
    try:
        payload = verify_auth0_token(token)
        return payload
    except Exception:
        # Invalid token - return None for optional auth
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenPayload:
    """
    Dependency that REQUIRES authentication.
    Raises 401 if no valid token is provided.
    
    Usage in routes:
        @app.get("/items")
        async def get_items(current_user: TokenPayload = Depends(get_current_user)):
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        # Verify token
        payload = verify_auth0_token(credentials.credentials)
        return payload
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )


def require_user_id(current_user: TokenPayload = Depends(get_current_user)) -> str:
    """
    Extract user_id from authenticated user.
    Use this for endpoints that need the user_id.
    
    Returns:
        user_id string from token
    """
    return current_user.sub


def extract_user_id(payload: TokenPayload) -> str:
    """Extract user ID from token payload"""
    return payload.sub


class AuthMiddleware:
    """Authentication middleware for FastAPI"""
    
    @staticmethod
    async def verify_request(request: Request) -> Optional[TokenPayload]:
        """Verify request authentication"""
        # Skip auth for health checks
        if request.url.path in ["/", "/health"]:
            return None
        
        # Extract token from header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header"
            )
        
        token = auth_header.replace("Bearer ", "")
        return verify_auth0_token(token)