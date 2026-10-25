import pytest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from backend.models import ElexonFuelHHItem, ElexonWindforItem
from backend.forecast_matcher import (
    ForecastMatcher,
    compute_day_ahead_cutoff,
    parse_iso_to_utc,
    format_iso_utc,
    format_iso_london,
)

LONDON_TZ = ZoneInfo("Europe/London")


def test_parse_iso_and_timezone_conversion():
    # Test UTC with Z
    dt_utc = parse_iso_to_utc("2026-01-02T12:00:00Z")
    assert dt_utc.tzinfo == timezone.utc
    assert dt_utc.year == 2026
    assert dt_utc.month == 1
    assert dt_utc.day == 2
    assert dt_utc.hour == 12

    # Test London representation (in January, London is UTC+0 GMT)
    london_str = format_iso_london(dt_utc)
    assert "2026-01-02T12:00:00" in london_str

    # Test summer time DST conversion (BST, UTC+1)
    dt_summer = parse_iso_to_utc("2026-07-01T12:00:00Z")
    london_summer_str = format_iso_london(dt_summer)
    assert "2026-07-01T13:00:00+01:00" == london_summer_str


def test_compute_day_ahead_cutoff():
    # Delivery on 2026-01-02 at 14:00 UTC
    delivery_start = parse_iso_to_utc("2026-01-02T14:00:00Z")
    
    # Default cutoff 11:00 London time on D-1
    cutoff_utc, cutoff_london = compute_day_ahead_cutoff(delivery_start, cutoff_time_str="11:00")
    
    # D-1 is 2026-01-01
    assert cutoff_london.year == 2026
    assert cutoff_london.month == 1
    assert cutoff_london.day == 1
    assert cutoff_london.hour == 11
    assert cutoff_london.minute == 0

    # Custom cutoff 17:30
    cutoff_utc_custom, cutoff_london_custom = compute_day_ahead_cutoff(delivery_start, cutoff_time_str="17:30")
    assert cutoff_london_custom.hour == 17
    assert cutoff_london_custom.minute == 30


def test_latest_eligible_forecast_selected():
    """
    Given multiple forecasts for delivery at 2026-01-02 12:00:
    - F1 published 2026-01-01 06:00 (Eligible)
    - F2 published 2026-01-01 09:30 (Eligible, latest before 11:00 cutoff)
    - F3 published 2026-01-01 11:30 (Ineligible, published after 11:00 cutoff)
    - F4 published 2026-01-02 08:00 (Ineligible, intraday)
    
    The matcher must select F2.
    """
    delivery_time = "2026-01-02T12:00:00Z"
    matcher = ForecastMatcher(cutoff_time_str="11:00")

    forecasts = [
        ElexonWindforItem(dataset="WINDFOR", publishTime="2026-01-01T06:00:00Z", startTime=delivery_time, generation=8500),
        ElexonWindforItem(dataset="WINDFOR", publishTime="2026-01-01T09:30:00Z", startTime=delivery_time, generation=9200),
        ElexonWindforItem(dataset="WINDFOR", publishTime="2026-01-01T11:30:00Z", startTime=delivery_time, generation=9800),
        ElexonWindforItem(dataset="WINDFOR", publishTime="2026-01-02T08:00:00Z", startTime=delivery_time, generation=9400),
    ]

    actuals = [
        ElexonFuelHHItem(dataset="FUELHH", startTime=delivery_time, fuelType="WIND", generation=9000),
    ]

    intervals = matcher.match_intervals(actual_records=actuals, forecast_records=forecasts)
    assert len(intervals) == 1
    iv = intervals[0]
    assert iv.status == "MATCHED"
    assert iv.forecast_publish_time_utc == "2026-01-01T09:30:00Z"
    assert iv.forecast_generation_mw == 9200.0
    assert iv.actual_generation_mw == 9000.0
    assert iv.signed_error_mw == 200.0   # 9200 - 9000
    assert iv.abs_error_mw == 200.0
    assert iv.abs_error_pct == round((200.0 / 9000.0) * 100, 2)
    assert iv.total_vintages_count == 4


def test_forecast_exactly_at_cutoff_is_eligible():
    """Forecasts published exactly at the cutoff (e.g. 11:00:00) must be included."""
    delivery_time = "2026-01-02T12:00:00Z"
    matcher = ForecastMatcher(cutoff_time_str="11:00")

    forecasts = [
        ElexonWindforItem(dataset="WINDFOR", publishTime="2026-01-01T11:00:00Z", startTime=delivery_time, generation=8800),
    ]
    actuals = [
        ElexonFuelHHItem(dataset="FUELHH", startTime=delivery_time, fuelType="WIND", generation=8800),
    ]

    intervals = matcher.match_intervals(actual_records=actuals, forecast_records=forecasts)
    assert len(intervals) == 1
    assert intervals[0].status == "MATCHED"
    assert intervals[0].forecast_generation_mw == 8800.0


def test_missing_forecast_and_missing_actual():
    matcher = ForecastMatcher(cutoff_time_str="11:00")
    
    # Case 1: Actual exists, but no eligible forecast exists (only after cutoff)
    t1 = "2026-01-02T10:00:00Z"
    forecasts = [
        ElexonWindforItem(dataset="WINDFOR", publishTime="2026-01-01T15:00:00Z", startTime=t1, generation=5000),
    ]
    actuals = [
        ElexonFuelHHItem(dataset="FUELHH", startTime=t1, fuelType="WIND", generation=5200),
    ]
    intervals = matcher.match_intervals(actual_records=actuals, forecast_records=forecasts)
    assert len(intervals) == 1
    assert intervals[0].status == "MISSING_FORECAST"
    assert intervals[0].actual_generation_mw == 5200.0
    assert intervals[0].forecast_generation_mw is None

    # Case 2: Forecast exists, but missing actual
    t2 = "2026-01-02T10:30:00Z"
    forecasts_2 = [
        ElexonWindforItem(dataset="WINDFOR", publishTime="2026-01-01T08:00:00Z", startTime=t2, generation=7000),
    ]
    intervals_2 = matcher.match_intervals(actual_records=[], forecast_records=forecasts_2)
    assert len(intervals_2) == 1
    assert intervals_2[0].status == "MISSING_ACTUAL"
    assert intervals_2[0].forecast_generation_mw == 7000.0
    assert intervals_2[0].actual_generation_mw is None


def test_fuelhh_non_wind_records_are_ignored():
    delivery_time = "2026-01-02T12:00:00Z"
    matcher = ForecastMatcher(cutoff_time_str="11:00")

    actuals = [
        ElexonFuelHHItem(dataset="FUELHH", startTime=delivery_time, fuelType="BIOMASS", generation=1200),
        ElexonFuelHHItem(dataset="FUELHH", startTime=delivery_time, fuelType="SOLAR", generation=400),
        ElexonFuelHHItem(dataset="FUELHH", startTime=delivery_time, fuelType="WIND", generation=8500),
    ]
    forecasts = [
        ElexonWindforItem(dataset="WINDFOR", publishTime="2026-01-01T09:00:00Z", startTime=delivery_time, generation=8200),
    ]

    intervals = matcher.match_intervals(actual_records=actuals, forecast_records=forecasts)
    assert len(intervals) == 1
    assert intervals[0].actual_generation_mw == 8500.0


def test_deterministic_tie_breaker():
    """
    If two forecasts have the identical publishTime, the matcher must select
    deterministically (e.g., higher generation).
    """
    delivery_time = "2026-01-02T12:00:00Z"
    matcher = ForecastMatcher(cutoff_time_str="11:00")

    forecasts = [
        ElexonWindforItem(dataset="WINDFOR", publishTime="2026-01-01T09:00:00Z", startTime=delivery_time, generation=6000),
        ElexonWindforItem(dataset="WINDFOR", publishTime="2026-01-01T09:00:00Z", startTime=delivery_time, generation=6500),
    ]
    actuals = [
        ElexonFuelHHItem(dataset="FUELHH", startTime=delivery_time, fuelType="WIND", generation=6200),
    ]

    intervals = matcher.match_intervals(actual_records=actuals, forecast_records=forecasts)
    assert len(intervals) == 1
    assert intervals[0].forecast_generation_mw == 6500.0
