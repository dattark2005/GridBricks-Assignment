# Codebase Concerns, Optimizations & Security Opportunities

## 1. Performance & Bundle Optimizations
1. **Frontend Chunk Size:**
   - *Current state:* Vite build warns `Some chunks are larger than 500 kB after minification (dist/assets/index-Djb61CdC.js is 635 kB)`.
   - *Optimization:* Configure Vite Rollup manual chunking to split large vendor dependencies (`recharts`, `lucide-react`, `react`, `react-dom`) into separate vendor chunks (`vendor-react`, `vendor-charts`). This reduces initial load times and leverages browser asset caching.
2. **API HTTP Compression:**
   - *Current state:* The `/api/evaluation` response for an entire month contains 744-1488 interval objects (~250 KB JSON).
   - *Optimization:* Add GZip middleware (`fastapi.middleware.gzip.GzipMiddleware`) with minimum size threshold (e.g. 500 bytes) to compress JSON payloads over the wire by ~80%, dramatically speeding up transfer times on slower networks.
3. **HTTP Cache-Control Headers:**
   - *Current state:* Backend responses do not explicitly provide `Cache-Control` headers.
   - *Optimization:* Historical January 2026 data is immutable. Adding `Cache-Control: public, max-age=3600` headers for evaluation endpoints allows edge proxies, browsers, and CDNs to cache historical responses without repeated backend processing.

## 2. Security Hardening & Protocols
1. **Security Headers (OWASP Recommended):**
   - *Current state:* Default FastAPI responses lack standard HTTP security headers.
   - *Hardening:* Add a custom security middleware injecting:
     - `X-Content-Type-Options: nosniff` (prevents MIME-type sniffing attacks)
     - `X-Frame-Options: DENY` (clickjacking protection)
     - `X-XSS-Protection: 1; mode=block` (legacy cross-site scripting filter)
     - `Strict-Transport-Security: max-age=31536000; includeSubDomains` (forces HTTPS in production)
     - `Referrer-Policy: strict-origin-when-cross-origin` (prevents leakage of sensitive query parameters)
     - `Permissions-Policy: geolocation=(), camera=(), microphone=()` (disables unused browser capabilities)
2. **CORS Origin Restriction:**
   - *Current state:* `CORSMiddleware` currently allows wildcard `allow_origins=["*"]`.
   - *Hardening:* Make allowed origins configurable via `CORS_ORIGINS` environment variable, defaulting to explicit trusted development origins (`http://localhost:5173`, `http://localhost:3000`, `http://127.0.0.1:5173`, `http://127.0.0.1:3000`).
3. **API Rate Limiting Protocol:**
   - *Current state:* Public endpoints could be subjected to unbounded request flooding.
   - *Hardening:* Implement an in-memory token-bucket / sliding-window rate limiter middleware for `/api/*` endpoints (e.g., 60 requests/minute per client IP) to protect against DoS attacks without needing an external Redis dependency.
4. **Input Boundary Enforcement & Sanitization:**
   - *Current state:* String dates are parsed with `datetime.strptime`, but query parameters could accept arbitrary length strings.
   - *Hardening:* Restrict `start_date` and `end_date` string lengths with Pydantic `Field(min_length=10, max_length=10, pattern=r"^\d{4}-\d{2}-\d{2}$")`.
5. **Container Security (Least Privilege):**
   - *Current state:* `Dockerfile.backend` runs as default root user inside the container.
   - *Hardening:* Create and switch to a non-privileged system user (`USER appuser`) to follow container security best practices.
