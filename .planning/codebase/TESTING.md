# Testing Strategy & Verification

## 1. Automated Test Architecture
- **Framework:** `pytest` with `pytest-asyncio` and FastAPI `TestClient`.
- **Location:** `tests/` directory.

### Covered Scenarios (18 Automated Tests)
1. **Timezone & Cutoff Calculations:**
   - Accurate UTC and London conversions during winter GMT and summer BST.
   - Day-Ahead cutoff generation on Day D-1 at 11:00 London time.
   - Month-boundary transitions (Dec 31 cutoff for Jan 1 delivery).
2. **Forecast Selection & Tie-Breaking:**
   - Filters candidate forecasts to `publishTime <= cutoff`.
   - Excludes later intraday or evening revisions.
   - Selects latest eligible vintage deterministically.
   - Deterministic tie-breaker for identical publish timestamps.
3. **Accuracy Metrics:**
   - Verification of MAE, RMSE, and Mean Signed Bias against known numerical fixtures.
   - Safe exclusion of zero and near-zero wind generation ($< 50\text{ MW}$) from MAPE.
   - Graceful handling of empty or missing intervals.
4. **API Integration:**
   - Mocking of external Elexon BMRS streaming responses.
   - Query parameter validation (e.g., rejecting invalid dates and out-of-range cutoff times).
   - Diagnostic `/api/interval/vintages` endpoint verification.

## 2. Frontend Verification
- TypeScript build check (`tsc -b && vite build`) verifying type-safety and bundle production with 0 errors.
- End-to-end browser subagent verification of chart interactivity, sorting, filtering, and modal dialogs.
