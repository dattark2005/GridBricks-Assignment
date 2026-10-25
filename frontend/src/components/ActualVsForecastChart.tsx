import React from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from "recharts";
import type { MatchedInterval } from "../types";

interface ChartProps {
  intervals: MatchedInterval[];
  onSelectInterval: (interval: MatchedInterval) => void;
}

export const ActualVsForecastChart: React.FC<ChartProps> = ({ intervals, onSelectInterval }) => {
  // Format chart data
  const chartData = intervals
    .filter((iv) => iv.actual_generation_mw !== null || iv.forecast_generation_mw !== null)
    .map((iv) => {
      // Short label: DD/MM HH:mm
      const dt = new Date(iv.start_time_utc);
      const day = dt.getUTCDate().toString().padStart(2, "0");
      const month = (dt.getUTCMonth() + 1).toString().padStart(2, "0");
      const hours = dt.getUTCHours().toString().padStart(2, "0");
      const mins = dt.getUTCMinutes().toString().padStart(2, "0");
      const label = `${day}/${month} ${hours}:${mins}`;

      const signedErr = iv.signed_error_mw ?? 0;

      return {
        ...iv,
        label,
        actual: iv.actual_generation_mw,
        forecast: iv.forecast_generation_mw,
        error: iv.signed_error_mw,
        posError: signedErr > 0 ? signedErr : 0,
        negError: signedErr < 0 ? signedErr : 0,
      };
    });

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;
    const data = payload[0].payload;

    return (
      <div className="chart-tooltip">
        <div className="tooltip-title">
          <span>{data.label} UTC</span> (SP {data.settlement_period || "—"})
        </div>
        <div className="tooltip-row">
          <span className="tooltip-label">Actual Generation:</span>
          <span className="tooltip-val" style={{ color: "#10b981" }}>
            {data.actual !== null && data.actual !== undefined
              ? `${data.actual.toLocaleString()} MW`
              : "Missing"}
          </span>
        </div>
        <div className="tooltip-row">
          <span className="tooltip-label">Day-Ahead Forecast:</span>
          <span className="tooltip-val" style={{ color: "#38bdf8" }}>
            {data.forecast !== null && data.forecast !== undefined
              ? `${data.forecast.toLocaleString()} MW`
              : "Missing"}
          </span>
        </div>
        <div className="tooltip-row">
          <span className="tooltip-label">Signed Error (FC - Act):</span>
          <span
            className="tooltip-val"
            style={{ color: data.error > 0 ? "#f59e0b" : data.error < 0 ? "#ec4899" : "#fff" }}
          >
            {data.error !== null && data.error !== undefined
              ? `${data.error > 0 ? "+" : ""}${data.error.toLocaleString()} MW`
              : "N/A"}
          </span>
        </div>
        {data.abs_error_pct !== null && data.abs_error_pct !== undefined && (
          <div className="tooltip-row">
            <span className="tooltip-label">Percentage Error:</span>
            <span className="tooltip-val">{data.abs_error_pct.toFixed(1)}%</span>
          </div>
        )}
        <div className="tooltip-row" style={{ marginTop: 6, paddingTop: 6, borderTop: "1px dashed #334155" }}>
          <span className="tooltip-label">Selected Vintage:</span>
          <span className="tooltip-val" style={{ fontSize: 11 }}>
            {data.forecast_publish_time_utc ? data.forecast_publish_time_utc.replace("T", " ").replace("Z", "") : "None"}
          </span>
        </div>
        <div className="tooltip-row">
          <span className="tooltip-label">Decision Cutoff:</span>
          <span className="tooltip-val" style={{ fontSize: 11 }}>
            {data.decision_cutoff_utc ? data.decision_cutoff_utc.replace("T", " ").replace("Z", "") : "None"}
          </span>
        </div>
        <div style={{ marginTop: 8, fontSize: 11, color: "#38bdf8", textAlign: "right" }}>
          Click to inspect all forecast revisions &rarr;
        </div>
      </div>
    );
  };

  return (
    <div className="chart-card">
      <div className="chart-header">
        <div className="chart-title-group">
          <h2>Actual Wind Generation vs Day-Ahead Eligible Forecast (MW)</h2>
          <span style={{ fontSize: 12, color: "#94a3b8" }}>
            Interactive time-series showing outturn generation, committed Day-Ahead forecast (selected at D-1 11:00 cutoff), and signed error delta.
          </span>
        </div>
        <div className="chart-legend">
          <div className="legend-item">
            <div className="legend-color-box" style={{ background: "#10b981" }} />
            <span>Actual Outturn (FUELHH)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color-box" style={{ background: "#38bdf8" }} />
            <span>Day-Ahead Forecast (WINDFOR)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color-box" style={{ background: "#f59e0b" }} />
            <span>Overforecast (+MW)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color-box" style={{ background: "#ec4899" }} />
            <span>Underforecast (-MW)</span>
          </div>
        </div>
      </div>

      <div style={{ width: "100%", height: 420 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={chartData}
            margin={{ top: 10, right: 20, left: 10, bottom: 20 }}
            onClick={(state: any) => {
              if (state && state.activePayload && state.activePayload.length) {
                onSelectInterval(state.activePayload[0].payload);
              }
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis
              dataKey="label"
              stroke="#64748b"
              tick={{ fontSize: 11 }}
              minTickGap={40}
            />
            <YAxis
              stroke="#64748b"
              tick={{ fontSize: 11 }}
              tickFormatter={(val) => `${(val / 1000).toFixed(0)}k`}
              label={{ value: "Generation (MW)", angle: -90, position: "insideLeft", fill: "#94a3b8", fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={0} stroke="#334155" />
            
            {/* Actual Wind Generation Line */}
            <Line
              type="monotone"
              dataKey="actual"
              name="Actual Generation"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 5, fill: "#10b981" }}
            />

            {/* Selected Day-Ahead Forecast Line */}
            <Line
              type="monotone"
              dataKey="forecast"
              name="Day-Ahead Forecast"
              stroke="#38bdf8"
              strokeWidth={2}
              strokeDasharray="4 2"
              dot={false}
              activeDot={{ r: 5, fill: "#38bdf8" }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Synchronized Signed Error Delta Sub-chart */}
      <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid #1e293b" }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: "#94a3b8" }}>
            Signed Volume Imbalance Delta (Forecast - Actual, MW)
          </span>
          <span style={{ fontSize: 11, color: "#64748b" }}>
            Click any bar to inspect historical revision progression
          </span>
        </div>
        <div style={{ width: "100%", height: 130 }}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={chartData}
              margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
              onClick={(state: any) => {
                if (state && state.activePayload && state.activePayload.length) {
                  onSelectInterval(state.activePayload[0].payload);
                }
              }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="label" hide />
              <YAxis
                stroke="#64748b"
                tick={{ fontSize: 10 }}
                tickFormatter={(val) => `${val > 0 ? "+" : ""}${(val / 1000).toFixed(1)}k`}
              />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={0} stroke="#475569" strokeWidth={1.5} />
              <Bar dataKey="error" name="Signed Error" fill="#818cf8" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
