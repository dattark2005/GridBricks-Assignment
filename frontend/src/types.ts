export interface ForecastVintage {
  publish_time_utc: string;
  publish_time_london: string;
  generation_mw: number;
  is_eligible: boolean;
  is_selected: boolean;
  hours_before_cutoff: number;
}

export interface MatchedInterval {
  start_time_utc: string;
  start_time_london: string;
  settlement_date: string;
  settlement_period?: number | null;
  actual_generation_mw?: number | null;
  forecast_generation_mw?: number | null;
  forecast_publish_time_utc?: string | null;
  forecast_publish_time_london?: string | null;
  decision_cutoff_utc?: string | null;
  decision_cutoff_london?: string | null;
  lead_time_hours?: number | null;
  signed_error_mw?: number | null;
  abs_error_mw?: number | null;
  abs_error_pct?: number | null;
  status: "MATCHED" | "MISSING_FORECAST" | "MISSING_ACTUAL" | "MISSING_BOTH";
  total_vintages_count: number;
}

export interface EvaluationMetrics {
  total_delivery_intervals: number;
  matched_intervals_count: number;
  missing_forecast_count: number;
  missing_actual_count: number;
  coverage_pct: number;
  mae_mw: number;
  rmse_mw: number;
  mape_pct?: number | null;
  mape_valid_intervals_count: number;
  mape_excluded_intervals_count: number;
  mean_signed_error_mw: number;
  max_abs_error_mw?: number | null;
  min_abs_error_mw?: number | null;
  actual_peak_mw?: number | null;
  actual_min_mw?: number | null;
  forecast_peak_mw?: number | null;
  forecast_min_mw?: number | null;
  decision_cutoff_time: string;
  mape_threshold_mw: number;
  error_convention: string;
}

export interface EvaluationResponse {
  period_start: string;
  period_end: string;
  decision_cutoff_time: string;
  metrics: EvaluationMetrics;
  intervals: MatchedInterval[];
  data_source: string;
  cache_status: string;
}

export interface IntervalVintagesResponse {
  delivery_start_time_utc: string;
  delivery_start_time_london: string;
  decision_cutoff_utc: string;
  decision_cutoff_london: string;
  actual_generation_mw?: number | null;
  selected_forecast?: ForecastVintage | null;
  all_vintages: ForecastVintage[];
}

export interface SystemStatusResponse {
  status: string;
  backend_version: string;
  timezone: string;
  default_cutoff_time: string;
  default_mape_threshold_mw: number;
  cached_datasets: {
    cache_files_count: number;
    files: string[];
  };
}
