import type { EvaluationResponse, IntervalVintagesResponse, SystemStatusResponse } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function fetchSystemStatus(): Promise<SystemStatusResponse> {
  const resp = await fetch(`${API_BASE_URL}/api/status`);
  if (!resp.ok) {
    throw new Error(`Failed to fetch system status: ${resp.statusText}`);
  }
  return resp.json();
}

export async function fetchEvaluation(params: {
  startDate: string;
  endDate: string;
  cutoffTime: string;
  mapeThresholdMw: number;
  forceRefresh?: boolean;
}): Promise<EvaluationResponse> {
  const query = new URLSearchParams({
    start_date: params.startDate,
    end_date: params.endDate,
    cutoff_time: params.cutoffTime,
    mape_threshold_mw: params.mapeThresholdMw.toString(),
    force_refresh: (params.forceRefresh || false).toString(),
  });

  const resp = await fetch(`${API_BASE_URL}/api/evaluation?${query.toString()}`);
  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error (${resp.status}): ${resp.statusText}`);
  }
  return resp.json();
}

export async function fetchIntervalVintages(
  intervalTime: string,
  cutoffTime: string
): Promise<IntervalVintagesResponse> {
  const query = new URLSearchParams({
    interval_time: intervalTime,
    cutoff_time: cutoffTime,
  });

  const resp = await fetch(`${API_BASE_URL}/api/interval/vintages?${query.toString()}`);
  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch interval vintages: ${resp.statusText}`);
  }
  return resp.json();
}
