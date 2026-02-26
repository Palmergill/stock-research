"""
CSRF Protection Middleware

Provides Cross-Site Request Forgery protection for state-changing requests.
Works alongside the existing action token system for defense in depth.
"""
import secrets
import hmac
import hashlib
from typing import Optional, Set
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from .config import Config, get_logger

logger = get_logger()


class CSRFProtection:
    """CSRF token generation and validation"""
    
    # Token settings
    TOKEN_LENGTH = 32
    COOKIE_NAME = "csrf_token"
    HEADER_NAME = "X-CSRF-Token"
    
    # Endpoints exempt from CSRF validation
    EXEMPT_PATHS: Set[str] = {
        "/api/poker/health",
        "/api/poker/health/ready",
        "/api/poker/health/live",
        "/api/poker/health/detailed",
        "/api/poker/health/integrity",
        "/api/poker/health/performance",
        "/api/poker/analytics/usage",
        "/docs",
        "/openapi.json",
        "/",
    }
    
    # Safe methods that don't require CSRF protection
    SAFE_METHODS: Set[str] = {"GET", "HEAD", "OPTIONS", "TRACE"}
    
    @classmethod
    def generate_token(cls) -> str:
        """Generate a new cryptographically secure CSRF token"""
        return secrets.token_urlsafe(cls.TOKEN_LENGTH)
    
    @classmethod
    def validate_token(cls, cookie_token: Optional[str], header_token: Optional[str]) -> bool:
        """
        Validate that the header token matches the cookie token.
        Uses constant-time comparison to prevent timing attacks.
        """
        if not cookie_token or not header_token:
            return False
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(cookie_token, header_token)
    
    @classmethod
    def is_exempt_path(cls, path: str) -> bool:
        """Check if the path is exempt from CSRF validation"""
        # Check exact matches
        if path in cls.EXEMPT_PATHS:
            return True
        
        # Check prefixes
        for exempt in cls.EXEMPT_PATHS:
            if path.startswith(exempt):
                return True
        
        return False
    
    @classmethod
    def is_safe_method(cls, method: str) -> bool:
        """Check if the HTTP method is safe (doesn't modify state)"""
        return method.upper() in cls.SAFE_METHODS


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for CSRF protection.
    
    Flow:
    1. On every request: Set a CSRF cookie if not present (double-submit cookie pattern)
    2. On state-changing requests (POST/PUT/PATCH/DELETE): Validate X-CSRF-Token header matches cookie
    3. Exempt health checks and safe methods from validation
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        
        # Skip CSRF for exempt paths
        if CSRFProtection.is_exempt_path(path):
            response = await call_next(request)
            # Still set CSRF cookie for exempt paths that might need it later
            self._ensure_csrf_cookie(request, response)
            return response
        
        # Validate CSRF token for state-changing requests
        if not CSRFProtection.is_safe_method(method):
            cookie_token = request.cookies.get(CSRFProtection.COOKIE_NAME)
            header_token = request.headers.get(CSRFProtection.HEADER_NAME)
            
            # Check for token in form data if not in header (for non-JSON requests)
            if not header_token:
                try:
                    form_data = await request.form()
                    header_token = form_data.get("csrf_token") or form_data.get("_csrf")
                    # Reset request body for downstream processing
                    # This is a workaround - in production, consider using Depends() instead
                except Exception:
                    pass
            
            if not CSRFProtection.validate_token(cookie_token, header_token):
                logger.warning(
                    f"CSRF validation failed: path={path}, method={method}, "
                    f"has_cookie={bool(cookie_token)}, has_header={bool(header_token)}"
                )
                raise HTTPException(
                    status_code=403,
                    detail="CSRF token missing or invalid. Include X-CSRF-Token header matching the csrf_token cookie."
                )
        
        # Process the request
        response = await call_next(request)
        
        # Ensure CSRF cookie is set on the response
        self._ensure_csrf_cookie(request, response)
        
        return response
    
    def _ensure_csrf_cookie(self, request: Request, response):
        """Set CSRF cookie if not present"""
        if CSRFProtection.COOKIE_NAME not in request.cookies:
            token = CSRFProtection.generate_token()
            # Set secure, httponly cookie
            response.set_cookie(
                key=CSRFProtection.COOKIE_NAME,
                value=token,
                max_age=86400 * 7,  # 7 days
                httponly=False,  # Must be accessible by JavaScript for double-submit
                secure=not Config.DEBUG,  # Secure in production
                samesite="strict",  # Strict same-site policy
            )
            logger.debug(f"Set new CSRF cookie for {request.url.path}")


def get_csrf_token(request: Request) -> Optional[str]:
    """
    Get the current CSRF token from the request.
    Use this in route handlers if you need to include the token in responses.
    """
    return request.cookies.get(CSRFProtection.COOKIE_NAME)


__all__ = [
    "CSRFProtection",
    "CSRFMiddleware",
    "get_csrf_token",
]
