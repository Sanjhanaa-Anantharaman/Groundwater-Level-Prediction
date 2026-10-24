import numpy as np
import pandas as pd
from src.features import make_features

def test_no_leakage():
    df = pd.DataFrame({
        "station_id": "A",
        "date": pd.date_range("2020-01-01", periods=120),
        "level": np.arange(120.0),
        "rain": np.ones(120)})
    f = make_features(df)   
    row = f.iloc[100]
    assert row["lag_1"] == 99.0 and row["roll_7"] == np.mean(np.arange(93, 100))
    assert row["rain_7"] == 7.0