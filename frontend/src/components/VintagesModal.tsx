import React, { useEffect, useState } from "react";
import type { MatchedInterval, IntervalVintagesResponse } from "../types";
import { fetchIntervalVintages } from "../api";
import { Check, Clock, X } from "lucide-react";

interface VintagesModalProps {
  interval: MatchedInterval | null;
  cutoffTime: string;
  onClose: () => void;
}

export const VintagesModal: React.FC<VintagesModalProps> = ({ interval, cutoffTime, onClose }) => {
  const [data, setData] = useState<IntervalVintagesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!interval) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    fetchIntervalVintages(interval.start_time_utc, cutoffTime)
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch((err) => {
        if (isMounted) setError(err.message || "Failed to load vintages");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [interval, cutoffTime]);

  if (!interval) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: "#fff" }}>
              Forecast Revision Progression & Vintage Audit
            </h3>
            <span style={{ fontSize: 12, color: "#94a3b8" }}>
              Delivery Interval: {interval.start_time_utc.replace("T", " ").replace(":00Z", " UTC")} (SP {interval.settlement_period || "—"})
            </span>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              color: "#94a3b8",
              cursor: "pointer",
              padding: 4,
            }}
          >
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          {/* Summary Box */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: 12,
              padding: 14,
              background: "var(--bg-secondary)",
              borderRadius: 8,
              border: "1px solid var(--border-color)",
              marginBottom: 20,
              fontSize: 12,
            }}
          >
            <div>
              <span style={{ color: "#64748b", textTransform: "uppercase", fontSize: 10, fontWeight: 600 }}>
                Outturn Actual
              </span>
              <div style={{ fontSize: 18, fontWeight: 700, color: "#10b981", marginTop: 4 }}>
                {interval.actual_generation_mw !== null && interval.actual_generation_mw !== undefined
                  ? `${interval.actual_generation_mw.toLocaleString()} MW`
                  : "Missing"}
              </div>
            </div>

            <div>
              <span style={{ color: "#64748b", textTransform: "uppercase", fontSize: 10, fontWeight: 600 }}>
                Committed Day-Ahead Forecast
              </span>
              <div style={{ fontSize: 18, fontWeight: 700, color: "#38bdf8", marginTop: 4 }}>
                {interval.forecast_generation_mw !== null && interval.forecast_generation_mw !== undefined
                  ? `${interval.forecast_generation_mw.toLocaleString()} MW`
                  : "None Available"}
              </div>
            </div>

            <div>
              <span style={{ color: "#64748b", textTransform: "uppercase", fontSize: 10, fontWeight: 600 }}>
                Decision Cutoff Applied
              </span>
              <div style={{ fontSize: 14, fontWeight: 600, color: "#cbd5e1", marginTop: 4 }}>
                {interval.decision_cutoff_utc ? interval.decision_cutoff_utc.replace("T", " ").replace(":00Z", " UTC") : "—"}
              </div>
              <div style={{ fontSize: 11, color: "#64748b" }}>
                ({cutoffTime} London on D-1)
              </div>
            </div>
          </div>

          <div style={{ marginBottom: 12, display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "#94a3b8" }}>
            <Clock size={14} />
            <span>Chronological Forecast Revisions Published for this Delivery Interval:</span>
          </div>

          {loading && (
            <div style={{ padding: 40, textAlign: "center", color: "#94a3b8" }}>
              Loading all published forecast vintages from Elexon archive...
            </div>
          )}

          {error && (
            <div style={{ padding: 20, background: "rgba(244, 63, 94, 0.1)", color: "#f43f5e", borderRadius: 8 }}>
              {error}
            </div>
          )}

          {data && data.all_vintages.length === 0 && !loading && (
            <div style={{ padding: 30, textAlign: "center", color: "#94a3b8" }}>
              No WINDFOR forecast revisions were published by National Grid ESO for this exact delivery interval.
            </div>
          )}

          {data && data.all_vintages.map((v, idx) => {
            return (
              <div
                key={idx}
                className={`vintage-timeline-item ${v.is_selected ? "selected" : ""}`}
              >
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <strong className="tabular" style={{ fontSize: 14, color: "#fff" }}>
                      {v.generation_mw.toLocaleString()} MW
                    </strong>
                    {v.is_selected && (
                      <span
                        className="badge-status"
                        style={{ background: "#0284c7", color: "#fff", display: "inline-flex", alignItems: "center", gap: 4 }}
                      >
                        <Check size={10} /> Selected Day-Ahead Forecast
                      </span>
                    )}
                    {v.is_eligible && !v.is_selected && (
                      <span className="badge-status" style={{ background: "rgba(100, 116, 139, 0.2)", color: "#94a3b8" }}>
                        Earlier Eligible Vintage
                      </span>
                    )}
                    {!v.is_eligible && (
                      <span className="badge-status" style={{ background: "rgba(244, 63, 94, 0.15)", color: "#f43f5e" }}>
                        Ineligible (Post-Cutoff / Intraday)
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 4 }}>
                    Published: {v.publish_time_utc.replace("T", " ").replace(":00Z", " UTC")}
                  </div>
                </div>

                <div style={{ textAlign: "right", fontSize: 12 }}>
                  <div style={{ color: v.is_eligible ? "#38bdf8" : "#f43f5e", fontWeight: 500 }}>
                    {v.is_eligible
                      ? `${v.hours_before_cutoff}h before cutoff`
                      : `${Math.abs(v.hours_before_cutoff)}h AFTER cutoff`}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
