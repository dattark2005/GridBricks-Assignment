import logging
import os
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fastapi.middleware.gzip import GZipMiddleware
from backend.config import (
    DEFAULT_CUTOFF_TIME,
    DEFAULT_MAPE_THRESHOLD_MW,
    MARKET_TIMEZONE_NAME,
    CACHE_DIR,
    CORS_ORIGINS,
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
)
from backend.models import (
    EvaluationResponse,
    IntervalVintagesResponse,
    SystemStatusResponse,
)
from backend.elexon_client import ElexonClient
from backend.forecast_matcher import ForecastMatcher, parse_iso_to_utc, format_iso_utc
from backend.metrics import calculate_metrics
from backend.security import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    HttpCacheControlMiddleware,
)

logger = logging.getLogger("gridbricks_api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

app = FastAPI(
    title="GridBricks UK Wind Forecast Evaluation API",
    description=(
        "Production-grade decision-support API evaluating Day-Ahead wind generation forecast accuracy "
        "against actual generation using official Elexon BMRS data (FUELHH and WINDFOR)."
    ),
    version="1.0.0",
)

# 1. OWASP Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# 2. Rate Limiting Protection (120 req/min default per client IP)
app.add_middleware(
    RateLimitMiddleware,
    max_requests=RATE_LIMIT_MAX_REQUESTS,
    window_seconds=RATE_LIMIT_WINDOW_SECONDS,
)

# 3. HTTP Cache-Control for evaluation datasets
app.add_middleware(HttpCacheControlMiddleware)

# 4. GZip Compression for payloads > 500 bytes
app.add_middleware(GZipMiddleware, minimum_size=500)

# 5. Configurable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if "*" not in CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

elexon_client = ElexonClient()


@app.get("/", tags=["General"])
def root():
    return {
        "service": "GridBricks UK Wind Forecast Evaluation API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "market": "UK Day-Ahead Electricity Market (Elexon BMRS)",
        "default_evaluation_period": "January 2026",
    }


@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "service": "gridbricks-backend",
        "version": "1.0.0",
    }


@app.get("/api/status", response_model=SystemStatusResponse, tags=["Status"])
def get_status():
    cache_files = list(CACHE_DIR.glob("*.json"))
    cache_info = {
        "cache_files_count": len(cache_files),
        "files": [f.name for f in cache_files],
    }

    return SystemStatusResponse(
        status="operational",
        backend_version="1.0.0",
        timezone=MARKET_TIMEZONE_NAME,
        default_cutoff_time=DEFAULT_CUTOFF_TIME,
        default_mape_threshold_mw=DEFAULT_MAPE_THRESHOLD_MW,
        cached_datasets=cache_info,
    )


@app.get("/api/evaluation", response_model=EvaluationResponse, tags=["Evaluation"])
def evaluate_forecasts(
    start_date: str = Query("2026-01-01", pattern=r"^\d{4}-\d{2}-\d{2}$", description="Delivery start date (YYYY-MM-DD)"),
    end_date: str = Query("2026-01-31", pattern=r"^\d{4}-\d{2}-\d{2}$", description="Delivery end date (YYYY-MM-DD)"),
    cutoff_time: str = Query(
        DEFAULT_CUTOFF_TIME,
        pattern=r"^\d{1,2}:\d{2}$",
        description="Day-ahead purchasing decision cutoff time on D-1 in Europe/London (HH:MM). Default is 11:00.",
    ),
    mape_threshold_mw: float = Query(
        DEFAULT_MAPE_THRESHOLD_MW,
        ge=0.0,
        le=1000.0,
        description="Threshold (MW) below which actual generation is excluded from MAPE to avoid division by near-zero.",
    ),
    force_refresh: bool = Query(False, description="Bypass cache and re-fetch from Elexon BMRS API"),
):
    """
    Main evaluation endpoint:
    1. Fetches official actual wind generation (FUELHH) and wind forecasts (WINDFOR).
    2. Applies the Day-Ahead decision cutoff logic (default 11:00 London time on D-1).
    3. Selects the latest eligible forecast vintage for each delivery interval.
    4. Computes MAE, RMSE, MAPE, Bias, and generates interval error time-series.
    """
    try:
        # Validate date inputs
        s_dt = datetime.strptime(start_date, "%Y-%m-%d")
        e_dt = datetime.strptime(end_date, "%Y-%m-%d")
        if s_dt > e_dt:
            raise HTTPException(status_code=400, detail="start_date must be before or equal to end_date")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Expected YYYY-MM-DD.")

    # Validate cutoff format
    try:
        parts = cutoff_time.split(":")
        h, m = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cutoff_time format. Expected HH:MM (24-hour).")

    try:
        # 1. Fetch actuals
        actual_records = elexon_client.get_actual_generation(
            start_date=start_date, end_date=end_date, force_refresh=force_refresh
        )

        # 2. Fetch forecasts
        forecast_records = elexon_client.get_forecast_generation(
            delivery_start_date=start_date, delivery_end_date=end_date, force_refresh=force_refresh
        )

        # 3. Match intervals using ForecastMatcher
        matcher = ForecastMatcher(cutoff_time_str=cutoff_time, mape_threshold_mw=mape_threshold_mw)
        matched_intervals = matcher.match_intervals(
            actual_records=actual_records, forecast_records=forecast_records
        )

        # Filter intervals strictly within requested delivery range (inclusive)
        # Using settlementDate or start_time_london date
        filtered_intervals = [
            iv for iv in matched_intervals
            if start_date <= iv.settlement_date <= end_date
        ]

        # 4. Compute metrics
        metrics = calculate_metrics(
            intervals=filtered_intervals,
            cutoff_time_str=cutoff_time,
            mape_threshold_mw=mape_threshold_mw,
        )

        return EvaluationResponse(
            period_start=start_date,
            period_end=end_date,
            decision_cutoff_time=cutoff_time,
            metrics=metrics,
            intervals=filtered_intervals,
            data_source="Elexon BMRS API (FUELHH & WINDFOR)",
            cache_status="Cached/Live Elexon stream",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error evaluating forecasts")
        raise HTTPException(status_code=500, detail=f"Failed to evaluate forecasts: {str(e)}")


@app.get("/api/interval/vintages", response_model=IntervalVintagesResponse, tags=["Diagnostic"])
def get_interval_vintages(
    interval_time: str = Query(..., description="Target delivery interval start time (ISO 8601 UTC)"),
    cutoff_time: str = Query(
        DEFAULT_CUTOFF_TIME,
        description="Day-ahead purchasing decision cutoff time on D-1 in Europe/London (HH:MM)",
    ),
):
    """
    Diagnostic endpoint allowing exploration of all forecast revisions published
    for a specific delivery interval.
    Shows the forecast progression leading up to and after the day-ahead cutoff.
    """
    try:
        target_utc = parse_iso_to_utc(interval_time)
        target_date_str = target_utc.strftime("%Y-%m-%d")

        # Fetch data around target date
        actual_records = elexon_client.get_actual_generation(
            start_date=target_date_str, end_date=target_date_str
        )
        forecast_records = elexon_client.get_forecast_generation(
            delivery_start_date=target_date_str, delivery_end_date=target_date_str
        )

        matcher = ForecastMatcher(cutoff_time_str=cutoff_time)
        return matcher.get_interval_vintages(
            interval_start_utc_str=interval_time,
            actual_records=actual_records,
            forecast_records=forecast_records,
        )
    except Exception as e:
        logger.exception("Error fetching interval vintages")
        raise HTTPException(status_code=500, detail=f"Failed to fetch interval vintages: {str(e)}")
