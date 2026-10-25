import time
import logging
from collections import defaultdict
from typing import Dict, List, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger("security")


class InMemoryRateLimiter:
    """
    In-memory sliding-window rate limiter per client IP.
    Default: 120 requests per 60 seconds window.
    """

    def __init__(self, max_requests: int = 120, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> Tuple[bool, int]:
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old timestamps
        timestamps = [ts for ts in self.requests[client_ip] if ts > window_start]
        self.requests[client_ip] = timestamps

        if len(timestamps) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - timestamps[0])) + 1
            return False, max(1, retry_after)

        self.requests[client_ip].append(now)
        return True, 0


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies OWASP-recommended HTTP security headers to all responses.
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Applies sliding-window rate limiting to /api/* routes.
    """

    def __init__(self, app, max_requests: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.limiter = InMemoryRateLimiter(max_requests=max_requests, window_seconds=window_seconds)

    async def dispatch(self, request: Request, call_next):
        # Exclude docs and health checks from aggressive rate limiting
        if request.url.path in ("/api/health", "/docs", "/openapi.json", "/"):
            return await call_next(request)

        # Extract client IP
        forwarded_for = request.headers.get("x-forwarded-for")
        client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "unknown")

        allowed, retry_after = self.limiter.is_allowed(client_ip)
        if not allowed:
            logger.warning(f"Rate limit exceeded for IP {client_ip} on {request.url.path}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please slow down and try again.",
                    "retry_after_seconds": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)


class HttpCacheControlMiddleware(BaseHTTPMiddleware):
    """
    Applies HTTP Cache-Control headers to historical evaluation endpoints.
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        if request.method == "GET" and request.url.path.startswith("/api/evaluation"):
            if response.status_code == 200:
                response.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=86400"
        return response
