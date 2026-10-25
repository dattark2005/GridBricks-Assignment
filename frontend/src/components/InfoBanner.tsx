import React, { useState } from "react";
import { Info, ChevronDown, ChevronUp } from "lucide-react";

export const InfoBanner: React.FC = () => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="info-callout">
      <Info size={18} style={{ flexShrink: 0, marginTop: 2, color: "#6366f1" }} />
      <div style={{ flex: 1 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <strong>Market Decision Assumptions & Methodological Rules:</strong> Day-Ahead purchasing decisions are committed on Day D-1 at <strong>11:00 London Time</strong> (EPEX SPOT auction gate closure).
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            style={{
              background: "none",
              border: "none",
              color: "#818cf8",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 4,
              fontSize: 12,
              fontWeight: 600,
            }}
          >
            {expanded ? "Hide Details" : "Learn More"}
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>

        {expanded && (
          <div style={{ marginTop: 12, paddingTop: 10, borderTop: "1px solid rgba(99, 102, 241, 0.2)", lineHeight: 1.6 }}>
            <ul style={{ paddingLeft: 20 }}>
              <li>
                <strong>Decision Cutoff Rule:</strong> For delivery interval on date <em>D</em>, only forecasts published by National Grid ESO on or before <strong>D-1 11:00 Europe/London</strong> are eligible. The latest eligible vintage (maximum publish timestamp) is selected.
              </li>
              <li>
                <strong>Error Convention:</strong> <code>Signed Error = Forecast - Actual</code>. A positive bias means <strong>overforecasting</strong> (surplus purchased), while negative bias indicates <strong>underforecasting</strong> (deficit/shortage).
              </li>
              <li>
                <strong>MAPE Exclusion Threshold:</strong> Intervals with actual wind generation &lt; 50 MW are strictly excluded from the percentage calculation to prevent division-by-zero and mathematical skew during low-wind periods.
              </li>
              <li>
                <strong>Data Resolution:</strong> Elexon <code>WINDFOR</code> forecasts are published at 1-hour resolution, while <code>FUELHH</code> outturn generation is 30-minute resolution. Exact hourly intervals match 100%, and half-hourly intervals are explicitly identified without synthetic interpolation.
              </li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};
