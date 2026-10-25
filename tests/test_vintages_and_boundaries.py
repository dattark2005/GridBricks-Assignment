import pytest
from backend.models import ElexonFuelHHItem, ElexonWindforItem
from backend.forecast_matcher import ForecastMatcher, parse_iso_to_utc


def test_hourly_vs_half_hourly_coverage():
    matcher = ForecastMatcher(cutoff_time_str="11:00")
    
    # 2 settlement periods in one hour: 00:00 and 00:30
    actuals = [
        ElexonFuelHHItem(dataset="FUELHH", startTime="2026-01-02T00:00:00Z", fuelType="WIND", generation=12000.0, settlementPeriod=1),
        ElexonFuelHHItem(dataset="FUELHH", startTime="2026-01-02T00:30:00Z", fuelType="WIND", generation=12200.0, settlementPeriod=2),
    ]
    # WINDFOR publishes at hourly granularity (00:00)
    forecasts = [
        ElexonWindforItem(dataset="WINDFOR", publishTime="2026-01-01T09:30:00Z", startTime="2026-01-02T00:00:00Z", generation=11800.0),
    ]

    intervals = matcher.match_intervals(actual_records=actuals, forecast_records=forecasts)
    assert len(intervals) == 2
    
    # 00:00 is MATCHED
    iv0 = next(iv for iv in intervals if iv.start_time_utc == "2026-01-02T00:00:00Z")
    assert iv0.status == "MATCHED"
    assert iv0.actual_generation_mw == 12000.0
    assert iv0.forecast_generation_mw == 11800.0
    assert iv0.signed_error_mw == -200.0  # 11800 - 12000

    # 00:30 is correctly labeled MISSING_FORECAST
    iv1 = next(iv for iv in intervals if iv.start_time_utc == "2026-01-02T00:30:00Z")
    assert iv1.status == "MISSING_FORECAST"
    assert iv1.actual_generation_mw == 12200.0
    assert iv1.forecast_generation_mw is None


def test_month_boundary_cutoff():
    """
    For delivery interval on January 1, 2026 (first day of January),
    the purchasing decision was made on December 31, 2025 at 11:00 London time.
    """
    matcher = ForecastMatcher(cutoff_time_str="11:00")
    delivery_time = "2026-01-01T00:00:00Z"
    
    actuals = [
        ElexonFuelHHItem(dataset="FUELHH", startTime=delivery_time, fuelType="WIND", generation=14000.0),
    ]
    forecasts = [
        # Published on Dec 31 09:30 (Eligible)
        ElexonWindforItem(dataset="WINDFOR", publishTime="2025-12-31T09:30:00Z", startTime=delivery_time, generation=14200.0),
        # Published on Dec 31 15:30 (Ineligible - after cutoff)
        ElexonWindforItem(dataset="WINDFOR", publishTime="2025-12-31T15:30:00Z", startTime=delivery_time, generation=14900.0),
    ]

    intervals = matcher.match_intervals(actual_records=actuals, forecast_records=forecasts)
    assert len(intervals) == 1
    iv = intervals[0]
    assert iv.status == "MATCHED"
    assert iv.decision_cutoff_utc == "2025-12-31T11:00:00Z"
    assert iv.forecast_publish_time_utc == "2025-12-31T09:30:00Z"
    assert iv.forecast_generation_mw == 14200.0


def test_interval_vintages_diagnostic():
    matcher = ForecastMatcher(cutoff_time_str="11:00")
    delivery_time = "2026-01-02T12:00:00Z"

    actuals = [
        ElexonFuelHHItem(dataset="FUELHH", startTime=delivery_time, fuelType="WIND", generation=10000.0),
    ]
    forecasts = [
        ElexonWindforItem(dataset="WINDFOR", publishTime="2026-01-01T02:30:00Z", startTime=delivery_time, generation=9000.0),
        ElexonWindforItem(dataset="WINDFOR", publishTime="2026-01-01T09:30:00Z", startTime=delivery_time, generation=9400.0),
        ElexonWindforItem(dataset="WINDFOR", publishTime="2026-01-01T15:30:00Z", startTime=delivery_time, generation=9700.0),
    ]

    vintages_resp = matcher.get_interval_vintages(
        interval_start_utc_str=delivery_time,
        actual_records=actuals,
        forecast_records=forecasts,
    )

    assert vintages_resp.actual_generation_mw == 10000.0
    assert len(vintages_resp.all_vintages) == 3
    assert vintages_resp.selected_forecast is not None
    assert vintages_resp.selected_forecast.generation_mw == 9400.0
    assert vintages_resp.selected_forecast.is_selected is True

    # Check eligibility flags
    v0 = next(v for v in vintages_resp.all_vintages if "02:30:00" in v.publish_time_utc)
    assert v0.is_eligible is True
    assert v0.is_selected is False

    v_after = next(v for v in vintages_resp.all_vintages if "15:30:00" in v.publish_time_utc)
    assert v_after.is_eligible is False
    assert v_after.is_selected is False
