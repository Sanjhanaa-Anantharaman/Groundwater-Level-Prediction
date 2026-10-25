import pandas as pd
from .anomaly import anomalies as _anomalies
from .recharge import recharge as _recharge
from .risk import ADVICE, risk, trend

FACTOR = {"low": 0.5, "medium": 1.0, "high": 1.5}

def _hist(ml, sid):
    h = ml["hist"]
    return h[h["station_id"] == sid].sort_values("date")

def status(ml, sid, days=30):
    h = _hist(ml, sid).dropna(subset=["level"])
    fc = ml["fc"][sid][:days]
    cur, end = float(h["level"].iloc[-1]), fc[-1]["level"]
    change = round(end - cur, 3)
    r = risk(change, ml["th"])
    return {"station_id": sid, "as_of": h["date"].iloc[-1].date(), "level": round(cur, 2),
            "trend": trend(h["level"].tail(14).tolist()), "risk": r, "days": days,
            "forecast_level": end, "change_m": change, "advice": ADVICE[r]}


def stations(ml):
    out = []
    for r in ml["stations"].itertuples():
        if r.station_id in ml["fc"]:
            s = status(ml, r.station_id)
            out.append({"id": r.station_id, "name": str(r.name), "district": str(r.district),
                        "lat": r.lat, "lon": r.lon, "level": s["level"], "risk": s["risk"]})
    return out

def forecast_view(ml, sid, days):
    h = _hist(ml, sid).dropna(subset=["level"]).tail(90)
    return {"station_id": sid,
            "observed": [{"date": d.date(), "level": round(v, 2)} for d, v in zip(h["date"], h["level"])],
            "forecast": ml["fc"][sid][:days]}


def history(ml, sid, start=None, end=None):
    h = _hist(ml, sid).dropna(subset=["level"])
    if start:
        h = h[h["date"] >= pd.Timestamp(start)]
    if end:
        h = h[h["date"] <= pd.Timestamp(end)]
    return {"station_id": sid, "observed": [{"date": d.date(), "level": round(v, 2)} for d, v in zip(h["date"], h["level"])]}

def alerts(ml, sid):
    s = status(ml, sid)
    out = []
    if s["trend"] == "declining":
        out.append("Groundwater level is declining in your area.")
    if s["risk"] != "SAFE":
        out.append(f"Risk over the next {s['days']} days: {s['risk']}.")
    return {"station_id": sid, "alerts": out}


def anomalies(ml, sid):
    return {"station_id": sid, "events": _anomalies(_hist(ml, sid).dropna(subset=["level"]).reset_index(drop=True))}

def recharge(ml, sid):
    return {"station_id": sid, "years": _recharge(_hist(ml, sid).dropna(subset=["level"]))}


def whatif(ml, sid, usage, days):
    cur = float(_hist(ml, sid).dropna(subset=["level"])["level"].iloc[-1])
    base = ml["fc"][sid][:days]
    scen = [{"date": p["date"], "level": round(cur + (p["level"] - cur) * FACTOR[usage], 3)} for p in base]
    return {"note": "Simulated scenario, not an ML forecast: usage scales the predicted change.",
            "baseline": base, "scenario": scen}
