import logging
from datetime import datetime, date, time, timedelta, timezone
from typing import List, Dict, Tuple, Optional
from zoneinfo import ZoneInfo
from dateutil import parser as date_parser

from backend.config import MARKET_TIMEZONE, DEFAULT_CUTOFF_TIME, DEFAULT_MAPE_THRESHOLD_MW
from backend.models import (
    ElexonFuelHHItem,
    ElexonWindforItem,
    MatchedInterval,
    ForecastVintage,
    IntervalVintagesResponse,
)

logger = logging.getLogger("forecast_matcher")


def parse_iso_to_utc(iso_str: str) -> datetime:
    """Parse an ISO 8601 string and ensure it is timezone-aware in UTC."""
    dt = date_parser.isoparse(iso_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


def format_iso_utc(dt: datetime) -> str:
    """Format datetime as canonical ISO8601 UTC string."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def format_iso_london(dt: datetime) -> str:
    """Format datetime in Europe/London timezone with offset."""
    dt_london = dt.astimezone(MARKET_TIMEZONE)
    return dt_london.isoformat()


def compute_day_ahead_cutoff(
    delivery_start_utc: datetime,
    cutoff_time_str: str = DEFAULT_CUTOFF_TIME,
) -> Tuple[datetime, datetime]:
    """
    Computes the applicable day-ahead purchasing decision cutoff timestamp.
    
    Rule:
    1. Determine the delivery interval's start date in UK local market time (Europe/London).
    2. The day-ahead wholesale purchasing decision is made on Day D-1 (the day prior).
    3. The cutoff time (default: 11:00 London time, aligned with EPEX SPOT Day-Ahead wholesale
       auction gate closure) occurs on D-1.
    
    Returns:
        (cutoff_dt_utc, cutoff_dt_london)
    """
    # Convert delivery start time to Europe/London
    delivery_london = delivery_start_utc.astimezone(MARKET_TIMEZONE)
    delivery_date = delivery_london.date()

    # Purchasing decision occurs on Day D-1
    decision_date = delivery_date - timedelta(days=1)

    # Parse cutoff time
    parts = cutoff_time_str.strip().split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0

    # Create cutoff datetime in Europe/London timezone
    cutoff_dt_london = datetime(
        decision_date.year,
        decision_date.month,
        decision_date.day,
        hour,
        minute,
        0,
        tzinfo=MARKET_TIMEZONE,
    )
    cutoff_dt_utc = cutoff_dt_london.astimezone(timezone.utc)
    return cutoff_dt_utc, cutoff_dt_london


class ForecastMatcher:
    """
    Service responsible for deterministic day-ahead forecast selection,
    actuals matching, and error calculations per delivery interval.
    """

    def __init__(
        self,
        cutoff_time_str: str = DEFAULT_CUTOFF_TIME,
        mape_threshold_mw: float = DEFAULT_MAPE_THRESHOLD_MW,
    ):
        self.cutoff_time_str = cutoff_time_str
        self.mape_threshold_mw = mape_threshold_mw

    def match_intervals(
        self,
        actual_records: List[ElexonFuelHHItem],
        forecast_records: List[ElexonWindforItem],
    ) -> List[MatchedInterval]:
        """
        Match each delivery interval's actual wind generation with the most recent
        forecast published prior to the day-ahead purchasing decision cutoff.
        """
        # 1. Index actuals by canonical UTC startTime
        actuals_by_start: Dict[str, ElexonFuelHHItem] = {}
        for r in actual_records:
            if r.fuelType != "WIND":
                continue
            start_utc = format_iso_utc(parse_iso_to_utc(r.startTime))
            # In case of duplicate records, take the last one deterministically
            actuals_by_start[start_utc] = r

        # 2. Group forecasts by canonical UTC startTime
        forecasts_by_start: Dict[str, List[ElexonWindforItem]] = {}
        for f in forecast_records:
            start_utc = format_iso_utc(parse_iso_to_utc(f.startTime))
            if start_utc not in forecasts_by_start:
                forecasts_by_start[start_utc] = []
            forecasts_by_start[start_utc].append(f)

        # 3. Identify all unique delivery interval start times across actuals and forecasts
        all_start_times = sorted(list(set(actuals_by_start.keys()) | set(forecasts_by_start.keys())))

        matched_intervals: List[MatchedInterval] = []

        for start_utc_str in all_start_times:
            start_dt_utc = parse_iso_to_utc(start_utc_str)
            start_london_str = format_iso_london(start_dt_utc)

            # Compute day-ahead cutoff
            cutoff_dt_utc, cutoff_dt_london = compute_day_ahead_cutoff(
                start_dt_utc, self.cutoff_time_str
            )
            cutoff_utc_str = format_iso_utc(cutoff_dt_utc)
            cutoff_london_str = format_iso_london(cutoff_dt_london)

            # Actual generation lookup
            actual_item = actuals_by_start.get(start_utc_str)
            actual_gen = actual_item.generation if actual_item is not None else None
            settlement_date = (
                actual_item.settlementDate
                if actual_item and actual_item.settlementDate
                else start_dt_utc.astimezone(MARKET_TIMEZONE).strftime("%Y-%m-%d")
            )
            settlement_period = actual_item.settlementPeriod if actual_item else None

            # Forecast selection logic
            candidate_forecasts = forecasts_by_start.get(start_utc_str, [])
            total_vintages = len(candidate_forecasts)

            # Filter forecasts published ON OR BEFORE the purchasing decision cutoff
            eligible_forecasts = []
            for fc in candidate_forecasts:
                pub_dt_utc = parse_iso_to_utc(fc.publishTime)
                if pub_dt_utc <= cutoff_dt_utc:
                    eligible_forecasts.append((pub_dt_utc, fc))

            selected_forecast_item: Optional[ElexonWindforItem] = None
            selected_pub_utc: Optional[datetime] = None

            if eligible_forecasts:
                # Deterministic selection:
                # Primary sort key: publish_time_utc (latest)
                # Tie-breaking key: generation (highest) to ensure absolute determinism
                eligible_forecasts.sort(key=lambda x: (x[0], x[1].generation), reverse=True)
                selected_pub_utc, selected_forecast_item = eligible_forecasts[0]

            # Determine interval status
            if selected_forecast_item is None and actual_gen is None:
                status = "MISSING_BOTH"
            elif selected_forecast_item is None:
                status = "MISSING_FORECAST"
            elif actual_gen is None:
                status = "MISSING_ACTUAL"
            else:
                status = "MATCHED"

            forecast_gen = selected_forecast_item.generation if selected_forecast_item else None
            forecast_pub_utc_str = (
                format_iso_utc(selected_pub_utc) if selected_pub_utc else None
            )
            forecast_pub_london_str = (
                format_iso_london(selected_pub_utc) if selected_pub_utc else None
            )

            # Lead time: hours between forecast publish time and delivery start time
            lead_time_hours = None
            if selected_pub_utc:
                lead_time_hours = round(
                    (start_dt_utc - selected_pub_utc).total_seconds() / 3600.0, 2
                )

            # Numerical error calculations
            signed_error_mw = None
            abs_error_mw = None
            abs_error_pct = None

            if actual_gen is not None and forecast_gen is not None:
                # Error convention: forecast - actual
                signed_error_mw = round(forecast_gen - actual_gen, 2)
                abs_error_mw = round(abs(forecast_gen - actual_gen), 2)

                # Percentage error: only valid when actual is above threshold
                if actual_gen >= self.mape_threshold_mw:
                    abs_error_pct = round((abs_error_mw / actual_gen) * 100.0, 2)

            interval = MatchedInterval(
                start_time_utc=start_utc_str,
                start_time_london=start_london_str,
                settlement_date=settlement_date,
                settlement_period=settlement_period,
                actual_generation_mw=actual_gen,
                forecast_generation_mw=forecast_gen,
                forecast_publish_time_utc=forecast_pub_utc_str,
                forecast_publish_time_london=forecast_pub_london_str,
                decision_cutoff_utc=cutoff_utc_str,
                decision_cutoff_london=cutoff_london_str,
                lead_time_hours=lead_time_hours,
                signed_error_mw=signed_error_mw,
                abs_error_mw=abs_error_mw,
                abs_error_pct=abs_error_pct,
                status=status,
                total_vintages_count=total_vintages,
            )
            matched_intervals.append(interval)

        return matched_intervals

    def get_interval_vintages(
        self,
        interval_start_utc_str: str,
        actual_records: List[ElexonFuelHHItem],
        forecast_records: List[ElexonWindforItem],
    ) -> IntervalVintagesResponse:
        """
        Diagnostic feature: Inspect all forecast vintages published for a specific
        delivery interval, clearly indicating which one was selected for the
        day-ahead decision cutoff, earlier eligible vintages, and later vintages.
        """
        target_start_dt_utc = parse_iso_to_utc(interval_start_utc_str)
        target_start_utc = format_iso_utc(target_start_dt_utc)

        cutoff_dt_utc, cutoff_dt_london = compute_day_ahead_cutoff(
            target_start_dt_utc, self.cutoff_time_str
        )

        # Actual generation lookup
        actual_gen = None
        for r in actual_records:
            if r.fuelType == "WIND" and format_iso_utc(parse_iso_to_utc(r.startTime)) == target_start_utc:
                actual_gen = r.generation
                break

        # Filter candidate forecasts for this delivery interval
        all_candidates = [
            f for f in forecast_records
            if format_iso_utc(parse_iso_to_utc(f.startTime)) == target_start_utc
        ]

        # Determine eligible and selected
        eligible_candidates = [
            f for f in all_candidates
            if parse_iso_to_utc(f.publishTime) <= cutoff_dt_utc
        ]
        eligible_candidates.sort(
            key=lambda x: (parse_iso_to_utc(x.publishTime), x.generation),
            reverse=True,
        )
        selected_item = eligible_candidates[0] if eligible_candidates else None

        vintages: List[ForecastVintage] = []
        for fc in sorted(all_candidates, key=lambda x: parse_iso_to_utc(x.publishTime)):
            pub_dt_utc = parse_iso_to_utc(fc.publishTime)
            is_eligible = pub_dt_utc <= cutoff_dt_utc
            is_selected = (
                selected_item is not None
                and fc.publishTime == selected_item.publishTime
                and fc.generation == selected_item.generation
            )
            hours_before_cutoff = round(
                (cutoff_dt_utc - pub_dt_utc).total_seconds() / 3600.0, 2
            )

            vintage = ForecastVintage(
                publish_time_utc=format_iso_utc(pub_dt_utc),
                publish_time_london=format_iso_london(pub_dt_utc),
                generation_mw=fc.generation,
                is_eligible=is_eligible,
                is_selected=is_selected,
                hours_before_cutoff=hours_before_cutoff,
            )
            vintages.append(vintage)

        selected_vintage = next((v for v in vintages if v.is_selected), None)

        return IntervalVintagesResponse(
            delivery_start_time_utc=target_start_utc,
            delivery_start_time_london=format_iso_london(target_start_dt_utc),
            decision_cutoff_utc=format_iso_utc(cutoff_dt_utc),
            decision_cutoff_london=format_iso_london(cutoff_dt_london),
            actual_generation_mw=actual_gen,
            selected_forecast=selected_vintage,
            all_vintages=vintages,
        )
