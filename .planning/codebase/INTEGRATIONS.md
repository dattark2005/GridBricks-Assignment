# External Integrations

## 1. Elexon BMRS REST API
- **Base URL:** `https://data.elexon.co.uk/bmrs/api/v1`
- **Authentication:** Publicly accessible endpoints for BMRS stream datasets (no API key required).
- **Rate Limits & Resilience:**
  - Client implements retry loops with backoff (`backend/elexon_client.py`).
  - Response payload caching to disk prevents redundant network requests.

### Endpoints Consumed
1. **`datasets/FUELHH/stream`**
   - Query Parameters: `settlementDateFrom`, `settlementDateTo`, `fuelType=WIND`.
   - Ingestion Filter: Strict client-side verification of `fuelType == "WIND"`.
   - Granularity: Half-hourly settlement periods (48 intervals/day).
2. **`datasets/WINDFOR/stream`**
   - Query Parameters: `publishDateTimeFrom`, `publishDateTimeTo`.
   - Publish Horizon: Fetches from $D-2$ to $D+1$ relative to delivery dates to capture all historical day-ahead candidates.
   - Granularity: Hourly intervals (24 intervals/day).

## 2. Reverse Proxy & Service Networking
- **Docker Network:** `gridbricks-network` connects `gridbricks-frontend` (Nginx) to `gridbricks-backend` (FastAPI).
- **Nginx Reverse Proxy:** Proxies `/api/` to `http://backend:8000/api/` ensuring single-origin requests with zero CORS friction in production.
