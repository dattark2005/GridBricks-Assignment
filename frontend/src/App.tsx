import React, { useState, useEffect } from "react";
import type { EvaluationResponse, MatchedInterval } from "./types";
import { fetchEvaluation } from "./api";
import { Header } from "./components/Header";
import { InfoBanner } from "./components/InfoBanner";
import { ControlPanel } from "./components/ControlPanel";
import { MetricCards } from "./components/MetricCards";
import { ActualVsForecastChart } from "./components/ActualVsForecastChart";
import { IntervalTable } from "./components/IntervalTable";
import { VintagesModal } from "./components/VintagesModal";
import { AlertTriangle, RefreshCw } from "lucide-react";

export const App: React.FC = () => {
  const [startDate, setStartDate] = useState("2026-01-01");
  const [endDate, setEndDate] = useState("2026-01-31");
  const [cutoffTime, setCutoffTime] = useState("11:00");
  const [mapeThresholdMw, setMapeThresholdMw] = useState(50);
  const [onlyMatched, setOnlyMatched] = useState(true);

  const [data, setData] = useState<EvaluationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedInterval, setSelectedInterval] = useState<MatchedInterval | null>(null);

  const loadData = async (forceRefresh: boolean = false) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchEvaluation({
        startDate,
        endDate,
        cutoffTime,
        mapeThresholdMw,
        forceRefresh,
      });
      setData(res);
    } catch (err: any) {
      setError(err.message || "Failed to load forecast evaluation data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(false);
  }, [startDate, endDate, cutoffTime, mapeThresholdMw]);

  // Display intervals filtered according to user granularity preference
  const displayedIntervals = React.useMemo(() => {
    if (!data) return [];
    if (onlyMatched) {
      return data.intervals.filter((iv) => iv.status === "MATCHED");
    }
    return data.intervals;
  }, [data, onlyMatched]);

  return (
    <div className="dashboard-container">
      <Header
        dataSource={data?.data_source || "Elexon BMRS"}
        cacheStatus={data?.cache_status || "Live Stream"}
        periodStart={startDate}
        periodEnd={endDate}
      />

      <InfoBanner />

      <ControlPanel
        startDate={startDate}
        endDate={endDate}
        cutoffTime={cutoffTime}
        mapeThresholdMw={mapeThresholdMw}
        onlyMatched={onlyMatched}
        loading={loading}
        onStartDateChange={setStartDate}
        onEndDateChange={setEndDate}
        onCutoffTimeChange={setCutoffTime}
        onMapeThresholdChange={setMapeThresholdMw}
        onOnlyMatchedChange={setOnlyMatched}
        onRefresh={() => loadData(true)}
      />

      {loading && !data && (
        <div style={{ padding: "80px 20px", textAlign: "center", color: "#94a3b8" }}>
          <RefreshCw size={32} className="spin" style={{ margin: "0 auto 16px auto", color: "#38bdf8" }} />
          <h3 style={{ color: "#fff", marginBottom: 6 }}>Calculating Day-Ahead Forecast Accuracies...</h3>
          <p style={{ fontSize: 13 }}>Streaming official Elexon FUELHH actuals & WINDFOR forecast archives for January 2026</p>
        </div>
      )}

      {error && (
        <div
          style={{
            padding: 24,
            background: "rgba(244, 63, 94, 0.1)",
            border: "1px solid rgba(244, 63, 94, 0.3)",
            borderRadius: 8,
            marginBottom: 24,
            display: "flex",
            alignItems: "flex-start",
            gap: 12,
            color: "#fecdd3",
          }}
        >
          <AlertTriangle size={20} color="#f43f5e" style={{ flexShrink: 0 }} />
          <div>
            <strong style={{ color: "#fff" }}>Unable to load evaluation dataset:</strong>
            <p style={{ marginTop: 4, fontSize: 13 }}>{error}</p>
            <button
              className="btn-preset"
              style={{ marginTop: 12, borderColor: "#f43f5e", color: "#fff" }}
              onClick={() => loadData(true)}
            >
              Retry Request
            </button>
          </div>
        </div>
      )}

      {data && (
        <>
          <MetricCards metrics={data.metrics} />

          <ActualVsForecastChart
            intervals={displayedIntervals}
            onSelectInterval={(iv) => setSelectedInterval(iv)}
          />

          <IntervalTable
            intervals={displayedIntervals}
            onSelectInterval={(iv) => setSelectedInterval(iv)}
          />
        </>
      )}

      {selectedInterval && (
        <VintagesModal
          interval={selectedInterval}
          cutoffTime={cutoffTime}
          onClose={() => setSelectedInterval(null)}
        />
      )}
    </div>
  );
};

export default App;
