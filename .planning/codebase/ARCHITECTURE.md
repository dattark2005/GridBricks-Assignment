# System Architecture

## Overview
GridBricks follows a clean, decoupled architecture separating data ingestion, market domain logic, numerical evaluation, and presentation:

```
[ Elexon BMRS API ]
       │  (HTTP Streams: FUELHH & WINDFOR)
       ▼
[ ElexonClient ] ──► [ Disk Cache (JSON) ]
       │
       ▼
[ ForecastMatcher Service ]
       │  ├── Europe/London Timezone Mapping
       │  ├── Day-Ahead Cutoff Calculation (D-1 11:00 London)
       │  ├── Eligibility Filter (publishTime <= cutoff)
       │  └── Deterministic Tie-Breaker
       ▼
[ MetricsCalculator ]
       │  ├── MAE, RMSE, Mean Signed Bias
       │  └── Thresholded MAPE (actual >= 50 MW)
       ▼
[ FastAPI App Routes ]
       │  (JSON API /api/evaluation, /api/interval/vintages)
       ▼
[ React Analytics Dashboard ]
```

## Architectural Highlights
1. **Isolated Market Domain Logic:** `ForecastMatcher` is completely independent of FastAPI web layers, allowing 100% test coverage and reusable execution.
2. **Deterministic Tie-Breaking:** If multiple forecasts have the identical latest `publishTime`, the record with highest generation is selected deterministically.
3. **Data Granularity Transparency:** Recognizes that WINDFOR is published hourly while FUELHH is recorded half-hourly, explicitly marking non-matching half-hours rather than inventing synthetic data.
