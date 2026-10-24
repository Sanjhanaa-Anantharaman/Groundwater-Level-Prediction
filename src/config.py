from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data/raw"
IMD_DIR = ROOT / "data/imd"
PROC_DIR = ROOT / "data/processed"
STATIONS = PROC_DIR / "stations.csv"   
RAIN = PROC_DIR / "rain.csv"
DAILY = PROC_DIR / "daily.csv"
MODEL_PATH = ROOT / "models/model.joblib"
THRESHHOLDS = ROOT / "models/thresholds.json"

START_YEAR, END_YEAR = 2023, 2025
LAGS = [1, 2, 3, 7, 14, 30]
ROLL = 7
RAIN_WINDOWS = [7, 30, 90]
MAX_GAP = 5
MIN_DAYS = 365
MIN_COV = 0.85
MAX_HORIZON = 30
FOLD_YEARS = [2024, 2025]
GAP_DAYS = 30