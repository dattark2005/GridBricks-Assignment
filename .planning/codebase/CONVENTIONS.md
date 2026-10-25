# Development Conventions & Standards

## 1. Domain & Mathematical Conventions
- **Error Sign Convention:** 
  $$\text{Signed Error} = \text{Forecast} - \text{Actual}$$
  - $\text{Signed Error} > 0$: **Overforecasting** (procured surplus wind generation into wholesale market).
  - $\text{Signed Error} < 0$: **Underforecasting** (procured deficit, leaving utility exposed to imbalance cashout).
- **Timezone Standard:**
  - All internal time calculations use `Europe/London` timezone (`zoneinfo.ZoneInfo("Europe/London")`).
  - Wire formats use ISO-8601 UTC with explicit `Z` suffix.
- **MAPE Exclusions:**
  - Intervals with actual outturn $< 50.0\text{ MW}$ are strictly excluded from the percentage error denominator to prevent zero-division and distortion.

## 2. Code Quality & Formatting
- **Python:** Strict Pydantic models for request/response serialization; no raw untyped dictionaries passed across module boundaries.
- **TypeScript:** Strict type checking enabled (`strict: true`, `verbatimModuleSyntax: true`).
- **Styling:** Vanilla CSS design system using CSS custom properties (`--bg-primary`, `--color-actual`, etc.) and tabular numeric formatting (`font-variant-numeric: tabular-nums`).
- **Git Commit Messages:** Short, natural sentences without conventional commit prefixes (no `feat:`, `fix:`, `chore:`).
