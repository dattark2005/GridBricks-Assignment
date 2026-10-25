import json
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
import httpx

from backend.config import (
    ELEXON_BASE_URL,
    ELEXON_REQUEST_TIMEOUT_SECONDS,
    ELEXON_MAX_RETRIES,
    CACHE_DIR,
    CACHE_ENABLED,
    CACHE_TTL_SECONDS,
)
from backend.models import ElexonFuelHHItem, ElexonWindforItem

logger = logging.getLogger("elexon_client")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class ElexonClient:
    """
    Official Elexon BMRS API Client for FUELHH (actuals) and WINDFOR (forecasts).
    Includes intelligent disk caching, robust retries, and strict schema validation.
    """

    def __init__(
        self,
        base_url: str = ELEXON_BASE_URL,
        timeout: float = ELEXON_REQUEST_TIMEOUT_SECONDS,
        max_retries: int = ELEXON_MAX_RETRIES,
        cache_dir: Path = CACHE_DIR,
        cache_enabled: bool = CACHE_ENABLED,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_dir = cache_dir
        self.cache_enabled = cache_enabled
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, dataset: str, key: str) -> Path:
        safe_key = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in key)
        return self.cache_dir / f"{dataset.lower()}_{safe_key}.json"

    def _read_cache(self, path: Path) -> Optional[List[Dict[str, Any]]]:
        if not self.cache_enabled or not path.exists():
            return None
        try:
            stat = path.stat()
            # If cache file exists and has content
            if stat.st_size == 0:
                return None
            age = time.time() - stat.st_mtime
            if age > CACHE_TTL_SECONDS:
                logger.info(f"Cache expired for {path.name} (age: {age:.0f}s > {CACHE_TTL_SECONDS}s)")
                return None
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} records from cache: {path.name}")
                return data
        except Exception as e:
            logger.warning(f"Error reading cache file {path}: {e}")
            return None

    def _write_cache(self, path: Path, data: List[Dict[str, Any]]) -> None:
        if not self.cache_enabled:
            return
        try:
            temp_path = path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            temp_path.replace(path)
            logger.info(f"Cached {len(data)} records to {path.name}")
        except Exception as e:
            logger.warning(f"Error writing cache file {path}: {e}")

    def _fetch_stream(self, endpoint_path: str, params: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Execute an HTTP GET request to Elexon stream endpoint with retries and timeout.
        """
        url = f"{self.base_url}/{endpoint_path.lstrip('/')}"
        headers = {
            "Accept": "application/json",
            "User-Agent": "GridBricks-Forecast-Evaluation/1.0",
        }

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Fetching Elexon [{endpoint_path}] (Attempt {attempt}/{self.max_retries}) with params {params}")
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(url, params=params, headers=headers)
                    resp.raise_for_status()
                    payload = resp.json()

                    if isinstance(payload, list):
                        records = payload
                    elif isinstance(payload, dict) and "data" in payload:
                        records = payload["data"]
                    else:
                        raise ValueError(f"Unexpected response structure from Elexon: {type(payload)}")

                    logger.info(f"Successfully received {len(records)} records from {endpoint_path}")
                    return records
            except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
                last_error = e
                logger.warning(f"Attempt {attempt} failed for {url}: {e}")
                if attempt < self.max_retries:
                    time.sleep(1.0 * attempt)

        raise RuntimeError(f"Failed to fetch data from Elexon after {self.max_retries} attempts: {last_error}")

    def get_actual_generation(
        self,
        start_date: str,
        end_date: str,
        force_refresh: bool = False,
    ) -> List[ElexonFuelHHItem]:
        """
        Fetch actual wind generation from FUELHH dataset for the given date range.
        Filters specifically for fuelType == 'WIND'.
        """
        cache_key = f"{start_date}_{end_date}"
        cache_path = self._get_cache_path("fuelhh_wind", cache_key)

        cached_data = None if force_refresh else self._read_cache(cache_path)
        if cached_data is not None:
            raw_records = cached_data
        else:
            # Query by settlementDate to cover exact delivery periods
            params = {
                "settlementDateFrom": start_date,
                "settlementDateTo": end_date,
                "fuelType": "WIND",
            }
            raw_records = self._fetch_stream("datasets/FUELHH/stream", params)
            self._write_cache(cache_path, raw_records)

        # Normalization and strict fuelType filtering
        wind_records: List[ElexonFuelHHItem] = []
        for r in raw_records:
            if not isinstance(r, dict):
                continue
            fuel_type = str(r.get("fuelType", "")).strip().upper()
            if fuel_type != "WIND":
                continue
            start_time = r.get("startTime")
            generation = r.get("generation")
            if start_time is None or generation is None:
                continue

            try:
                item = ElexonFuelHHItem(
                    dataset=r.get("dataset", "FUELHH"),
                    publishTime=r.get("publishTime"),
                    startTime=str(start_time),
                    settlementDate=r.get("settlementDate"),
                    settlementPeriod=r.get("settlementPeriod"),
                    fuelType="WIND",
                    generation=float(generation),
                )
                wind_records.append(item)
            except Exception as e:
                logger.debug(f"Skipping malformed FUELHH record {r}: {e}")

        logger.info(f"Processed {len(wind_records)} valid WIND records from FUELHH for {start_date} to {end_date}")
        return wind_records

    def get_forecast_generation(
        self,
        delivery_start_date: str,
        delivery_end_date: str,
        force_refresh: bool = False,
    ) -> List[ElexonWindforItem]:
        """
        Fetch wind forecasts from WINDFOR dataset.
        Crucial: Day-ahead forecasts for delivery on date D are published on D-1 or earlier.
        Therefore, we fetch forecasts published from (delivery_start_date - 2 days) to (delivery_end_date + 1 day).
        """
        # Calculate publish time bounds to capture all candidate day-ahead forecasts
        start_dt = datetime.strptime(delivery_start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(delivery_end_date, "%Y-%m-%d")

        publish_from_dt = start_dt - timedelta(days=2)
        publish_to_dt = end_dt + timedelta(days=1, hours=23, minutes=59, seconds=59)

        pub_from_str = publish_from_dt.strftime("%Y-%m-%dT00:00:00Z")
        pub_to_str = publish_to_dt.strftime("%Y-%m-%dT23:59:59Z")

        cache_key = f"{delivery_start_date}_{delivery_end_date}"
        cache_path = self._get_cache_path("windfor", cache_key)

        cached_data = None if force_refresh else self._read_cache(cache_path)
        if cached_data is not None:
            raw_records = cached_data
        else:
            params = {
                "publishDateTimeFrom": pub_from_str,
                "publishDateTimeTo": pub_to_str,
            }
            raw_records = self._fetch_stream("datasets/WINDFOR/stream", params)
            self._write_cache(cache_path, raw_records)

        # Normalization and validation
        forecast_records: List[ElexonWindforItem] = []
        for r in raw_records:
            if not isinstance(r, dict):
                continue
            start_time = r.get("startTime")
            publish_time = r.get("publishTime")
            generation = r.get("generation")
            if not start_time or not publish_time or generation is None:
                continue

            try:
                item = ElexonWindforItem(
                    dataset=r.get("dataset", "WINDFOR"),
                    publishTime=str(publish_time),
                    startTime=str(start_time),
                    generation=float(generation),
                )
                forecast_records.append(item)
            except Exception as e:
                logger.debug(f"Skipping malformed WINDFOR record {r}: {e}")

        logger.info(
            f"Processed {len(forecast_records)} valid WINDFOR records covering delivery {delivery_start_date} to {delivery_end_date}"
        )
        return forecast_records
