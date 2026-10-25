import React from "react";
import type { EvaluationMetrics } from "../types";
import { AlertCircle, ArrowDownRight, ArrowUpRight, CheckCircle2, TrendingUp, Zap } from "lucide-react";

interface MetricCardsProps {
  metrics: EvaluationMetrics;
}

export const MetricCards: React.FC<MetricCardsProps> = ({ metrics }) => {
  const isOverforecast = metrics.mean_signed_error_mw > 0;
  const isUnderforecast = metrics.mean_signed_error_mw < 0;

  return (
    <div className="metrics-grid">
      {/* MAE */}
      <div className="metric-card">
        <div className="metric-header">
          <span className="metric-title">Mean Absolute Error (MAE)</span>
          <TrendingUp size={16} color="#38bdf8" />
        </div>
        <div className="metric-value-box">
          <span className="metric-value tabular">
            {metrics.mae_mw.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
          </span>
          <span className="metric-unit">MW</span>
        </div>
        <div className="metric-subtext">
          <span>Average unsigned volume deviation</span>
        </div>
      </div>

      {/* RMSE */}
      <div className="metric-card">
        <div className="metric-header">
          <span className="metric-title">Root Mean Squared Error (RMSE)</span>
          <Zap size={16} color="#818cf8" />
        </div>
        <div className="metric-value-box">
          <span className="metric-value tabular">
            {metrics.rmse_mw.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
          </span>
          <span className="metric-unit">MW</span>
        </div>
        <div className="metric-subtext">
          <span>Heavily penalizes extreme forecast spikes</span>
        </div>
      </div>

      {/* MAPE */}
      <div className="metric-card">
        <div className="metric-header">
          <span className="metric-title">Mean Abs % Error (MAPE)</span>
          <CheckCircle2 size={16} color="#10b981" />
        </div>
        <div className="metric-value-box">
          <span className="metric-value tabular">
            {metrics.mape_pct !== null && metrics.mape_pct !== undefined
              ? `${metrics.mape_pct.toFixed(1)}%`
              : "N/A"}
          </span>
        </div>
        <div className="metric-subtext">
          <span>
            Computed on {metrics.mape_valid_intervals_count} intervals ({metrics.mape_excluded_intervals_count} &lt; {metrics.mape_threshold_mw}MW excluded)
          </span>
        </div>
      </div>

      {/* Mean Signed Error / Bias */}
      <div className="metric-card">
        <div className="metric-header">
          <span className="metric-title">Mean Signed Bias</span>
          {isOverforecast ? (
            <ArrowUpRight size={16} color="#f59e0b" />
          ) : isUnderforecast ? (
            <ArrowDownRight size={16} color="#ec4899" />
          ) : (
            <TrendingUp size={16} color="#94a3b8" />
          )}
        </div>
        <div className="metric-value-box">
          <span
            className="metric-value tabular"
            style={{ color: isOverforecast ? "#f59e0b" : isUnderforecast ? "#ec4899" : "#fff" }}
          >
            {metrics.mean_signed_error_mw > 0 ? "+" : ""}
            {metrics.mean_signed_error_mw.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
          </span>
          <span className="metric-unit">MW</span>
        </div>
        <div className="metric-subtext">
          <span>
            {isOverforecast
              ? "Overforecasting (Surplus procured into market)"
              : isUnderforecast
              ? "Underforecasting (Deficit unhedged)"
              : "Neutral bias"}
          </span>
        </div>
      </div>

      {/* Coverage */}
      <div className="metric-card">
        <div className="metric-header">
          <span className="metric-title">Matched Coverage</span>
          <AlertCircle size={16} color="#38bdf8" />
        </div>
        <div className="metric-value-box">
          <span className="metric-value tabular">
            {metrics.matched_intervals_count}
          </span>
          <span className="metric-unit">/ {metrics.total_delivery_intervals} ({metrics.coverage_pct}%)</span>
        </div>
        <div className="metric-subtext">
          <span>Hourly WINDFOR resolution matched to FUELHH</span>
        </div>
      </div>

      {/* Peak Generation */}
      <div className="metric-card">
        <div className="metric-header">
          <span className="metric-title">Actual vs Forecast Peak</span>
          <Zap size={16} color="#10b981" />
        </div>
        <div className="metric-value-box">
          <span className="metric-value tabular" style={{ fontSize: "20px" }}>
            {metrics.actual_peak_mw?.toLocaleString() || "0"}
          </span>
          <span className="metric-unit">/ {metrics.forecast_peak_mw?.toLocaleString() || "0"} MW</span>
        </div>
        <div className="metric-subtext">
          <span>Max outturn vs Max Day-Ahead estimate</span>
        </div>
      </div>
    </div>
  );
};
