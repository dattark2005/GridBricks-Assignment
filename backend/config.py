import os
from pathlib import Path
from zoneinfo import ZoneInfo

# Base Directories
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Elexon BMRS API Config
ELEXON_BASE_URL = os.getenv("ELEXON_BASE_URL", "https://data.elexon.co.uk/bmrs/api/v1")
ELEXON_REQUEST_TIMEOUT_SECONDS = float(os.getenv("ELEXON_REQUEST_TIMEOUT_SECONDS", "30.0"))
ELEXON_MAX_RETRIES = int(os.getenv("ELEXON_MAX_RETRIES", "3"))

# Market & Forecast Selection Defaults
# EPEX SPOT UK Day-Ahead wholesale market auction order book gate closure is 11:00 London Time on D-1.
# This represents the actual point in time when purchasing decisions must be committed.
DEFAULT_CUTOFF_TIME = os.getenv("DEFAULT_CUTOFF_TIME", "11:00")
MARKET_TIMEZONE_NAME = "Europe/London"
MARKET_TIMEZONE = ZoneInfo(MARKET_TIMEZONE_NAME)

# MAPE Threshold: Wind generation below this threshold is excluded from percentage calculation
# to avoid division-by-zero or numerical explosions for near-zero wind.
DEFAULT_MAPE_THRESHOLD_MW = float(os.getenv("DEFAULT_MAPE_THRESHOLD_MW", "50.0"))

# Cache Settings
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() in ("true", "1", "yes")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "86400"))  # 24 hours for historical data
