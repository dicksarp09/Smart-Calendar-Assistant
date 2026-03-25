"""
Auth0 Authentication Module
Handles Auth0 integration and JWT verification
"""

import os
import jwt
from jwt import PyJWKClient
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from pydantic import BaseModel


class Auth0Config:
    """Auth0 configuration"""
    
    DOMAIN = os.getenv("AUTH0_DOMAIN", "")
    AUDIENCE = os.getenv("AUTH0_AUDIENCE", "")
    ALGORITHMS = ["RS256"]
    
    @classmethod
    def get_jwks_url(cls) -> str:
        """Get JWKS URL for token verification"""
        return f"https://{cls.DOMAIN}/.well-known/jwks.json"


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    iss: Optional[str] = None
    aud: Optional[str] = None
    iat: Optional[int] = None
    exp: Optional[int] = None


def verify_auth0_token(token: str) -> TokenPayload:
    """
    Verify Auth0 JWT token and extract payload.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenPayload with user info
        
    Raises:
        HTTPException: If token is invalid
    """
    # For development, allow mock tokens
    if os.getenv("ENVIRONMENT") == "development":
        return _parse_development_token(token)
    
    try:
        # Get JWKS client
        jwks_client = PyJWKClient(Auth0Config.get_jwks_url())
        
        # Verify token
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Decode token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=Auth0Config.ALGORITHMS,
            audience=Auth0Config.AUDIENCE,
            issuer=f"https://{Auth0Config.DOMAIN}/"
        )
        
        return TokenPayload(**payload)
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}"
        )


def _parse_development_token(token: str) -> TokenPayload:
    """Parse mock token for development"""
    # Simple base64 decode for dev tokens
    try:
        import base64
        import json
        
        # Handle "Bearer " prefix
        if token.startswith("Bearer "):
            token = token[7:]
        
        # Add padding if needed
        padding = 4 - len(token) % 4
        if padding != 4:
            token += "=" * padding
        
        # Decode
        payload = json.loads(base64.b64decode(token))
        return TokenPayload(**payload)
        
    except:
        # Default dev user
        return TokenPayload(
            sub="dev|user123",
            email="dev@example.com",
            name="Dev User"
        )


def get_user_from_token(credentials: str = None) -> Dict[str, Any]:
    """
    Extract user info from token.
    
    Args:
        credentials: Bearer token from Authorization header
        
    Returns:
        User dictionary with id, email, name, picture
    """
    if not credentials or not credentials.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = credentials.replace("Bearer ", "")
    payload = verify_auth0_token(token)
    
    return {
        "user_id": payload.sub,
        "email": payload.email,
        "name": payload.name,
        "picture": payload.picture
    }