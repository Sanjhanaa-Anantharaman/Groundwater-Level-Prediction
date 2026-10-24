import json
import joblib
import numpy as np
import pandas as pd
from .config import DAILY, STATIONS, MODEL_PATH, THRESHOLDS, MAX_HORIZON
from .features import make_features, FEATURES


def climatology(daily):
    d = daily.assign(m=daily["date"].dt.month)
    return d.groupby(["station_id", "m"])["rain"].mean().to_dict()


def forecast(model, hist, sid, days, clim):
    h = (hist[hist["station_id"] == sid].sort_values("date")[["station_id", "date", "level", "rain"]]
         .tail(130).reset_index(drop=True))
    h["level"] = h["level"].ffill()
    out = []
    for _ in range(days):
        nxt = h["date"].iloc[-1] + pd.Timedelta(days=1)
        h.loc[len(h)] = [sid, nxt, np.nan, clim.get((sid, nxt.month), 0.0)]
        pred = float(model.predict(make_features(h).iloc[[-1]][FEATURES])[0])
        h.loc[h.index[-1], "level"] = pred
        out.append({"date": nxt.date(), "level": round(pred, 3)})
    return out


def build_ml(bundle, hist, stations, th):
    clim = climatology(hist)
    fc = {sid: forecast(bundle["model"], hist, sid, MAX_HORIZON, clim) for sid in hist["station_id"].unique()}
    return {"bundle": bundle, "hist": hist, "stations": stations, "th": th, "clim": clim, "fc": fc}


def load():
    return build_ml(joblib.load(MODEL_PATH),
                    pd.read_csv(DAILY, parse_dates=["date"], dtype={"station_id": str}),
                    pd.read_csv(STATIONS, dtype={"station_id": str}),
                    json.loads(THRESHOLDS.read_text()))