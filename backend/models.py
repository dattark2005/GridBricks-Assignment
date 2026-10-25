from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ElexonFuelHHItem(BaseModel):
    dataset: str
    publishTime: Optional[str] = None
    startTime: str
    settlementDate: Optional[str] = None
    settlementPeriod: Optional[int] = None
    fuelType: str
    generation: float

class ElexonWindforItem(BaseModel):
    dataset: str
    publishTime: str
    startTime: str
    generation: float

class ForecastVintage(BaseModel):
    publish_time_utc: str
    publish_time_london: str
    generation_mw: float
    is_eligible: bool
    is_selected: bool
    hours_before_cutoff: float

class MatchedInterval(BaseModel):
    start_time_utc: str
    start_time_london: str
    settlement_date: str
    settlement_period: Optional[int] = None
    actual_generation_mw: Optional[float] = None
    forecast_generation_mw: Optional[float] = None
    forecast_publish_time_utc: Optional[str] = None
    forecast_publish_time_london: Optional[str] = None
    decision_cutoff_utc: Optional[str] = None
    decision_cutoff_london: Optional[str] = None
    lead_time_hours: Optional[float] = None
    signed_error_mw: Optional[float] = None  # forecast - actual
    abs_error_mw: Optional[float] = None     # abs(forecast - actual)
    abs_error_pct: Optional[float] = None    # (abs_error / actual) * 100
    status: str                              # "MATCHED", "MISSING_FORECAST", "MISSING_ACTUAL"
    total_vintages_count: int = 0

class IntervalVintagesResponse(BaseModel):
    delivery_start_time_utc: str
    delivery_start_time_london: str
    decision_cutoff_utc: str
    decision_cutoff_london: str
    actual_generation_mw: Optional[float] = None
    selected_forecast: Optional[ForecastVintage] = None
    all_vintages: List[ForecastVintage]

class EvaluationMetrics(BaseModel):
    total_delivery_intervals: int
    matched_intervals_count: int
    missing_forecast_count: int
    missing_actual_count: int
    coverage_pct: float
    mae_mw: float
    rmse_mw: float
    mape_pct: Optional[float] = None
    mape_valid_intervals_count: int
    mape_excluded_intervals_count: int
    mean_signed_error_mw: float  # Bias
    max_abs_error_mw: Optional[float] = None
    min_abs_error_mw: Optional[float] = None
    actual_peak_mw: Optional[float] = None
    actual_min_mw: Optional[float] = None
    forecast_peak_mw: Optional[float] = None
    forecast_min_mw: Optional[float] = None
    decision_cutoff_time: str
    mape_threshold_mw: float
    error_convention: str = "forecast - actual (positive = overforecast, negative = underforecast)"

class EvaluationResponse(BaseModel):
    period_start: str
    period_end: str
    decision_cutoff_time: str
    metrics: EvaluationMetrics
    intervals: List[MatchedInterval]
    data_source: str
    cache_status: str

class SystemStatusResponse(BaseModel):
    status: str
    backend_version: str
    timezone: str
    default_cutoff_time: str
    default_mape_threshold_mw: float
    cached_datasets: Dict[str, Any]
