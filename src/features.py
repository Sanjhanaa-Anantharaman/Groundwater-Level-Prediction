
import numpy as np
from .config import LAGS, ROLL, RAIN_WINDOWS


FEATURES = (
    [f"lag_{l}" for l in LAGS]
    + [f"roll_{ROLL}", "doy_sin", "doy_cos"]
    + [f"rain_{w}" for w in RAIN_WINDOWS]
)


def make_features(df):
    df = df.sort_values(["station_id", "date"]).copy()

    g = df.groupby("station_id")["level"]

    for l in LAGS:
        df[f"lag_{l}"] = g.shift(l)

    df[f"roll_{ROLL}"] = g.transform(
        lambda s: s.shift(1).rolling(ROLL).mean()
    )

    r = df.groupby("station_id")["rain"]

    for w in RAIN_WINDOWS:
        df[f"rain_{w}"] = r.transform(
            lambda s: s.shift(1).rolling(w).sum()
        )

    doy = df["date"].dt.dayofyear

    df["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    df["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)

    return df
