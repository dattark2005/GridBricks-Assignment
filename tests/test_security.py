import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.security import InMemoryRateLimiter

client = TestClient(app)


def test_security_headers_present():
    response = client.get("/api/health")
    assert response.status_code == 200
    headers = response.headers

    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("x-xss-protection") == "1; mode=block"
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "geolocation=()" in headers.get("permissions-policy", "")
    assert "max-age=31536000" in headers.get("strict-transport-security", "")


def test_rate_limiter_logic():
    limiter = InMemoryRateLimiter(max_requests=3, window_seconds=60)
    test_ip = "192.168.1.100"

    # First 3 requests allowed
    assert limiter.is_allowed(test_ip)[0] is True
    assert limiter.is_allowed(test_ip)[0] is True
    assert limiter.is_allowed(test_ip)[0] is True

    # 4th request blocked
    allowed, retry_after = limiter.is_allowed(test_ip)
    assert allowed is False
    assert retry_after > 0


def test_rate_limiter_middleware_blocks_flooding():
    # Create isolated client with low rate limit
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route
    from backend.security import RateLimitMiddleware

    async def sample_endpoint(request):
        return PlainTextResponse("OK")

    test_app = Starlette(routes=[Route("/api/test", sample_endpoint)])
    test_app.add_middleware(RateLimitMiddleware, max_requests=2, window_seconds=60)

    sub_client = TestClient(test_app)
    r1 = sub_client.get("/api/test")
    assert r1.status_code == 200

    r2 = sub_client.get("/api/test")
    assert r2.status_code == 200

    r3 = sub_client.get("/api/test")
    assert r3.status_code == 429
    assert "retry_after_seconds" in r3.json()
    assert "Retry-After" in r3.headers


def test_query_parameter_regex_validation():
    # Invalid date pattern (e.g. sql injection attempt or malformed text)
    r1 = client.get("/api/evaluation?start_date=2026-01-01;DROP+TABLE")
    assert r1.status_code == 422  # Unprocessable Entity via Pydantic pattern validation

    r2 = client.get("/api/evaluation?cutoff_time=invalid_time")
    assert r2.status_code == 422


def test_cache_control_headers_on_evaluation():
    response = client.get("/api/evaluation?start_date=2026-01-01&end_date=2026-01-02")
    assert response.status_code == 200
    cache_header = response.headers.get("cache-control")
    assert cache_header is not None
    assert "public" in cache_header
    assert "max-age=3600" in cache_header
