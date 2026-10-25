import React from "react";
import { RefreshCw } from "lucide-react";

interface ControlPanelProps {
  startDate: string;
  endDate: string;
  cutoffTime: string;
  mapeThresholdMw: number;
  onlyMatched: boolean;
  loading: boolean;
  onStartDateChange: (date: string) => void;
  onEndDateChange: (date: string) => void;
  onCutoffTimeChange: (time: string) => void;
  onMapeThresholdChange: (threshold: number) => void;
  onOnlyMatchedChange: (onlyMatched: boolean) => void;
  onRefresh: () => void;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  startDate,
  endDate,
  cutoffTime,
  mapeThresholdMw,
  onlyMatched,
  loading,
  onStartDateChange,
  onEndDateChange,
  onCutoffTimeChange,
  onMapeThresholdChange,
  onOnlyMatchedChange,
  onRefresh,
}) => {
  const setPreset = (start: string, end: string) => {
    onStartDateChange(start);
    onEndDateChange(end);
  };

  const isPresetActive = (start: string, end: string) => startDate === start && endDate === end;

  return (
    <div className="control-panel">
      {/* Date Range & Presets */}
      <div className="control-group">
        <div className="control-item">
          <span className="control-label">Evaluation Scope Presets</span>
          <div className="preset-buttons">
            <button
              className={`btn-preset ${isPresetActive("2026-01-01", "2026-01-31") ? "active" : ""}`}
              onClick={() => setPreset("2026-01-01", "2026-01-31")}
            >
              Full Jan 2026
            </button>
            <button
              className={`btn-preset ${isPresetActive("2026-01-01", "2026-01-07") ? "active" : ""}`}
              onClick={() => setPreset("2026-01-01", "2026-01-07")}
            >
              W1 (1-7)
            </button>
            <button
              className={`btn-preset ${isPresetActive("2026-01-08", "2026-01-14") ? "active" : ""}`}
              onClick={() => setPreset("2026-01-08", "2026-01-14")}
            >
              W2 (8-14)
            </button>
            <button
              className={`btn-preset ${isPresetActive("2026-01-15", "2026-01-21") ? "active" : ""}`}
              onClick={() => setPreset("2026-01-15", "2026-01-21")}
            >
              W3 (15-21)
            </button>
            <button
              className={`btn-preset ${isPresetActive("2026-01-22", "2026-01-31") ? "active" : ""}`}
              onClick={() => setPreset("2026-01-22", "2026-01-31")}
            >
              W4 (22-31)
            </button>
          </div>
        </div>

        <div className="control-item">
          <span className="control-label">Delivery Start</span>
          <input
            type="date"
            className="input-date"
            value={startDate}
            min="2026-01-01"
            max="2026-01-31"
            onChange={(e) => onStartDateChange(e.target.value)}
          />
        </div>

        <div className="control-item">
          <span className="control-label">Delivery End</span>
          <input
            type="date"
            className="input-date"
            value={endDate}
            min="2026-01-01"
            max="2026-01-31"
            onChange={(e) => onEndDateChange(e.target.value)}
          />
        </div>
      </div>

      {/* Decision Cutoff & Filters */}
      <div className="control-group">
        <div className="control-item">
          <span className="control-label">Decision Cutoff (D-1 London)</span>
          <select
            className="input-select"
            value={cutoffTime}
            onChange={(e) => onCutoffTimeChange(e.target.value)}
          >
            <option value="11:00">11:00 (EPEX Day-Ahead Auction - Default)</option>
            <option value="12:00">12:00 (Noon Market Review)</option>
            <option value="17:00">17:00 (Evening Schedule Freeze)</option>
            <option value="09:00">09:00 (Morning Early Estimate)</option>
          </select>
        </div>

        <div className="control-item">
          <span className="control-label">MAPE Threshold (MW)</span>
          <input
            type="number"
            className="input-number"
            style={{ width: "90px" }}
            value={mapeThresholdMw}
            min="0"
            max="500"
            step="10"
            onChange={(e) => onMapeThresholdChange(Number(e.target.value))}
            title="Intervals with actual generation below this value are excluded from MAPE"
          />
        </div>

        <div className="control-item">
          <span className="control-label">View Granularity</span>
          <select
            className="input-select"
            value={onlyMatched ? "matched" : "all"}
            onChange={(e) => onOnlyMatchedChange(e.target.value === "matched")}
          >
            <option value="matched">Matched Only (Hourly WINDFOR)</option>
            <option value="all">All Half-Hours (Include Missing)</option>
          </select>
        </div>

        <div className="control-item" style={{ alignSelf: "flex-end" }}>
          <button className="btn-primary" onClick={onRefresh} disabled={loading}>
            <RefreshCw size={14} className={loading ? "spin" : ""} />
            {loading ? "Calculating..." : "Apply & Recalculate"}
          </button>
        </div>
      </div>
    </div>
  );
};
