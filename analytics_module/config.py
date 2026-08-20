"""Configuration for analytics module."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANALYTICS_DB = PROJECT_ROOT / "analytics" / "analytics.db"
OUTPUT_DIR = PROJECT_ROOT / "analytics_module" / "reports"
MODEL_DIR = PROJECT_ROOT / "analytics_module" / "models"
FIG_DIR = OUTPUT_DIR / "figures"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_SEED = 42
TEST_HORIZON_DAYS = 30
FORECAST_HORIZON_DAYS = 30
MIN_TRAIN_DAYS = 180
MAX_SAMPLE_PAIRS = 5000

CATEGORICAL_COLS = ["facility_type", "county", "commodity_category", "supplier_category"]
TARGET_COL = "stockout_risk"