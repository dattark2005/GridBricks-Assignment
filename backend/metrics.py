import math
from typing import List, Optional
from backend.models import MatchedInterval, EvaluationMetrics
from backend.config import DEFAULT_CUTOFF_TIME, DEFAULT_MAPE_THRESHOLD_MW


def calculate_metrics(
    intervals: List[MatchedInterval],
    cutoff_time_str: str = DEFAULT_CUTOFF_TIME,
    mape_threshold_mw: float = DEFAULT_MAPE_THRESHOLD_MW,
) -> EvaluationMetrics:
    """
    Computes rigorous forecast evaluation metrics based on matched pairs.
    
    Error convention:
        error = forecast - actual
        signed_error > 0: Overforecasting (utility procured surplus wind)
        signed_error < 0: Underforecasting (utility faces deficit in wind)
    """
    total_intervals = len(intervals)
    matched_pairs = [
        iv for iv in intervals
        if iv.status == "MATCHED"
        and iv.actual_generation_mw is not None
        and iv.forecast_generation_mw is not None
    ]

    matched_count = len(matched_pairs)
    missing_forecast_count = sum(1 for iv in intervals if iv.status == "MISSING_FORECAST")
    missing_actual_count = sum(1 for iv in intervals if iv.status == "MISSING_ACTUAL")
    coverage_pct = round((matched_count / total_intervals * 100.0), 2) if total_intervals > 0 else 0.0

    if matched_count == 0:
        return EvaluationMetrics(
            total_delivery_intervals=total_intervals,
            matched_intervals_count=0,
            missing_forecast_count=missing_forecast_count,
            missing_actual_count=missing_actual_count,
            coverage_pct=0.0,
            mae_mw=0.0,
            rmse_mw=0.0,
            mape_pct=None,
            mape_valid_intervals_count=0,
            mape_excluded_intervals_count=0,
            mean_signed_error_mw=0.0,
            max_abs_error_mw=None,
            min_abs_error_mw=None,
            actual_peak_mw=None,
            actual_min_mw=None,
            forecast_peak_mw=None,
            forecast_min_mw=None,
            decision_cutoff_time=cutoff_time_str,
            mape_threshold_mw=mape_threshold_mw,
        )

    signed_errors: List[float] = []
    abs_errors: List[float] = []
    squared_errors: List[float] = []
    mape_pcts: List[float] = []

    actual_values: List[float] = []
    forecast_values: List[float] = []

    mape_excluded_count = 0

    for iv in matched_pairs:
        act = iv.actual_generation_mw
        fc = iv.forecast_generation_mw
        err = fc - act
        abs_err = abs(err)

        signed_errors.append(err)
        abs_errors.append(abs_err)
        squared_errors.append(err ** 2)

        actual_values.append(act)
        forecast_values.append(fc)

        # MAPE calculation threshold rule
        if act >= mape_threshold_mw:
            mape_pcts.append((abs_err / act) * 100.0)
        else:
            mape_excluded_count += 1

    mae = round(sum(abs_errors) / matched_count, 2)
    rmse = round(math.sqrt(sum(squared_errors) / matched_count), 2)
    mean_signed_error = round(sum(signed_errors) / matched_count, 2)

    mape_valid_count = len(mape_pcts)
    mape = round(sum(mape_pcts) / mape_valid_count, 2) if mape_valid_count > 0 else None

    max_abs_err = round(max(abs_errors), 2) if abs_errors else None
    min_abs_err = round(min(abs_errors), 2) if abs_errors else None

    actual_peak = round(max(actual_values), 2) if actual_values else None
    actual_min = round(min(actual_values), 2) if actual_values else None
    forecast_peak = round(max(forecast_values), 2) if forecast_values else None
    forecast_min = round(min(forecast_values), 2) if forecast_values else None

    return EvaluationMetrics(
        total_delivery_intervals=total_intervals,
        matched_intervals_count=matched_count,
        missing_forecast_count=missing_forecast_count,
        missing_actual_count=missing_actual_count,
        coverage_pct=coverage_pct,
        mae_mw=mae,
        rmse_mw=rmse,
        mape_pct=mape,
        mape_valid_intervals_count=mape_valid_count,
        mape_excluded_intervals_count=mape_excluded_count,
        mean_signed_error_mw=mean_signed_error,
        max_abs_error_mw=max_abs_err,
        min_abs_error_mw=min_abs_err,
        actual_peak_mw=actual_peak,
        actual_min_mw=actual_min,
        forecast_peak_mw=forecast_peak,
        forecast_min_mw=forecast_min,
        decision_cutoff_time=cutoff_time_str,
        mape_threshold_mw=mape_threshold_mw,
    )
