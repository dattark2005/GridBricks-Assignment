import pytest
from backend.models import MatchedInterval
from backend.metrics import calculate_metrics


def create_interval(actual: float, forecast: float, status: str = "MATCHED") -> MatchedInterval:
    signed_err = forecast - actual if actual is not None and forecast is not None else None
    abs_err = abs(signed_err) if signed_err is not None else None
    pct = round((abs_err / actual) * 100, 2) if actual and actual >= 50.0 and abs_err is not None else None
    return MatchedInterval(
        start_time_utc="2026-01-02T00:00:00Z",
        start_time_london="2026-01-02T00:00:00+00:00",
        settlement_date="2026-01-02",
        actual_generation_mw=actual,
        forecast_generation_mw=forecast,
        signed_error_mw=signed_err,
        abs_error_mw=abs_err,
        abs_error_pct=pct,
        status=status,
    )


def test_metrics_calculation_standard():
    # 3 intervals:
    # 1: act=1000, fc=1100 -> err = +100 (overforecast), abs=100, % = 10%
    # 2: act=2000, fc=1800 -> err = -200 (underforecast), abs=200, % = 10%
    # 3: act=1500, fc=1500 -> err = 0, abs=0, % = 0%
    intervals = [
        create_interval(1000.0, 1100.0),
        create_interval(2000.0, 1800.0),
        create_interval(1500.0, 1500.0),
    ]

    metrics = calculate_metrics(intervals, cutoff_time_str="11:00", mape_threshold_mw=50.0)

    assert metrics.total_delivery_intervals == 3
    assert metrics.matched_intervals_count == 3
    assert metrics.coverage_pct == 100.0

    # MAE = (100 + 200 + 0) / 3 = 100.0
    assert metrics.mae_mw == 100.0

    # RMSE = sqrt((100^2 + (-200)^2 + 0^2) / 3) = sqrt((10000 + 40000) / 3) = sqrt(16666.67) = 129.10
    assert metrics.rmse_mw == 129.10

    # Mean signed error (Bias) = (100 - 200 + 0) / 3 = -33.33
    assert metrics.mean_signed_error_mw == -33.33

    # MAPE = (10% + 10% + 0%) / 3 = 6.67%
    assert metrics.mape_pct == 6.67
    assert metrics.mape_valid_intervals_count == 3
    assert metrics.mape_excluded_intervals_count == 0

    assert metrics.max_abs_error_mw == 200.0
    assert metrics.min_abs_error_mw == 0.0
    assert metrics.actual_peak_mw == 2000.0
    assert metrics.actual_min_mw == 1000.0
    assert metrics.forecast_peak_mw == 1800.0
    assert metrics.forecast_min_mw == 1100.0


def test_mape_zero_and_near_zero_handling():
    """
    Ensure zero or near-zero actual generation is safely excluded from MAPE
    and does not cause ZeroDivisionError or wildly skewed percentages.
    """
    intervals = [
        create_interval(actual=0.0, forecast=150.0),     # Below threshold (0 < 50) -> excluded
        create_interval(actual=30.0, forecast=80.0),      # Below threshold (30 < 50) -> excluded
        create_interval(actual=100.0, forecast=120.0),   # 120 - 100 = 20 -> 20%
        create_interval(actual=200.0, forecast=180.0),   # 180 - 200 = -20 -> 10%
    ]

    metrics = calculate_metrics(intervals, cutoff_time_str="11:00", mape_threshold_mw=50.0)

    # All 4 are matched for MAE/RMSE
    assert metrics.matched_intervals_count == 4
    # But only 2 valid for MAPE
    assert metrics.mape_valid_intervals_count == 2
    assert metrics.mape_excluded_intervals_count == 2
    # MAPE = (20% + 10%) / 2 = 15.0%
    assert metrics.mape_pct == 15.0


def test_empty_dataset_handling():
    metrics = calculate_metrics([], cutoff_time_str="11:00", mape_threshold_mw=50.0)
    assert metrics.total_delivery_intervals == 0
    assert metrics.matched_intervals_count == 0
    assert metrics.coverage_pct == 0.0
    assert metrics.mae_mw == 0.0
    assert metrics.rmse_mw == 0.0
    assert metrics.mape_pct is None
