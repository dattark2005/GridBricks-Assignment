# Technology Stack

## Runtimes & Languages
- **Backend:** Python 3.12 / 3.14 (FastAPI 0.162.0, Uvicorn 0.54.0, Pydantic 2.14.1)
- **Frontend:** Node.js 20+ / 24+ (React 19, TypeScript 5.8, Vite 8.3)
- **Containers:** Docker, Docker Compose, Nginx Alpine

## Core Dependencies
### Backend (`backend/requirements.txt`)
- `fastapi`: High-performance ASGI web framework with OpenAPI schemas.
- `uvicorn`: ASGI server implementation for asynchronous execution.
- `pydantic`: Type enforcement, serialization, and input validation.
- `httpx`: Synchronous and asynchronous HTTP client for external Elexon BMRS API integration.
- `python-dateutil`: Timezone-aware ISO-8601 string parsing.
- `pytest` & `pytest-asyncio`: Automated unit and integration testing suite.

### Frontend (`frontend/package.json`)
- `react` & `react-dom`: Declarative UI component tree.
- `recharts`: D3-based charting engine for composite time-series.
- `lucide-react`: Modern icon library for energy trading and financial metrics.
- `vite`: Build tool and dev server with Rolldown-based bundling.
