import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from .config import GAP_DAYS
from .forecast import forecast, climatology

HORIZONS = (7, 14, 30)

def metrics(y, p):
    return {
        "mae": float(mean_absolute_error(y, p)),
        "rmse": float(np.sqrt(mean_squared_error(y, p))),
        "r2": float(r2_score(y, p))
    }
    
def window(year):
    return pd.Timestamp(year, 6, 1), pd.Timestamp(year, 10, 31)

def split(feat, year):
    s, e = window(year)
    g = pd.Timedelta(days=GAP_DAYS)
    return feat[(feat["date"] >= s - g) | (feat["date"] > e + g)]

def horizon_errors(model, daily, year, days=30, step=15):
    s, e = window(year)
    g = pd.Timedelta(days=GAP_DAYS)
    clim = climatology(daily[(daily["date"] < s - g) | (daily["date"] > e + g)])
    err = {h: [] for h in HORIZONS}
    base = {h: [] for h in HORIZONS}
    for origin in pd.date_range(s, e - pd.Timedelta(days=days), freq=f"{step}D"):
        for sid, d in daily.groupby("station_id"):
            hist = d[d["date"] <= origin]
            truth = d.set_index("date")["level"]
            fut = pd.date_range(origin + pd.Timedelta(days=1), periods=days)
            if len(hist) < 130 or truth.reindex(fut).isna().any():
                continue
            fc = forecast(model, hist, sid, days, clim)
            last = hist["level"].dropna().iloc[-1]
            for h in HORIZONS:
                t = truth[fut[h - 1]]
                err[h].append(abs(fc[h - 1]["level"] - t))
                base[h].append(abs(last - t))
    return {h: (float(np.mean(err[h])), float(np.mean(base[h]))) for h in HORIZONS if err[h]}
