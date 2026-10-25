# Project Directory Structure

```
Gridbricks/
├── backend/
│   ├── __init__.py            # Package initializer
│   ├── config.py              # Configuration tokens, timezone defaults, cache paths
│   ├── models.py              # Pydantic schemas (Elexon items, intervals, metrics)
│   ├── elexon_client.py       # Elexon BMRS API client with disk caching & retry logic
│   ├── forecast_matcher.py    # Timezone-aware day-ahead cutoff and matching engine
│   ├── metrics.py             # Numerical metrics: MAE, RMSE, MAPE, Bias
│   ├── main.py                # FastAPI routes, error handlers, and CORS configuration
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx                 # Title banner, timezone & source status
│   │   │   ├── InfoBanner.tsx             # Methodology, assumptions & rules
│   │   │   ├── ControlPanel.tsx           # Scope presets, cutoffs, threshold controls
│   │   │   ├── MetricCards.tsx            # MAE, RMSE, MAPE, Bias cards
│   │   │   ├── ActualVsForecastChart.tsx  # Interactive dual line & error bar chart
│   │   │   ├── IntervalTable.tsx          # Sortable interval-level analysis table
│   │   │   └── VintagesModal.tsx          # Revision progression & audit drawer
│   │   ├── api.ts             # API client functions with typed responses
│   │   ├── types.ts           # Frontend TypeScript interfaces
│   │   ├── App.tsx            # Root application layout and query state
│   │   ├── main.tsx           # React DOM root mounting
│   │   └── index.css          # Energy analytics stylesheet
│   ├── nginx.conf             # Nginx reverse proxy configuration
│   ├── vercel.json            # Vercel SPA deployment configuration
│   └── package.json           # Node scripts and dependencies
├── data/
│   └── cache/                 # Local disk cache of raw Elexon BMRS stream responses
├── tests/
│   ├── test_forecast_matcher.py          # Cutoff selection and tie-breaker unit tests
│   ├── test_metrics.py                   # MAE, RMSE, thresholded MAPE tests
│   ├── test_api.py                       # FastAPI integration tests with mock responses
│   └── test_vintages_and_boundaries.py   # Historical boundary and diagnostic tests
├── docker-compose.yml         # Container orchestration for frontend and backend
├── Dockerfile.backend         # Production Python container
├── Dockerfile.frontend        # Multi-stage production Nginx container
├── Procfile                   # Heroku web process definition
├── runtime.txt                # Heroku Python runtime pin
├── requirements.txt           # PaaS root dependency manifest
├── pytest.ini                 # Pytest runner configuration
└── README.md                  # Continuously maintained documentation
```
