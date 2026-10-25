
import pandas as pd

from .anomaly import anomalies as _anomalies
from .recharge import recharge as _recharge
from .risk import ADVICE, risk, trend


FACTOR = {"low": 0.5, "medium": 1.0, "high": 1.5}

# Initial engineering thresholds; adjust to your data collection frequency.
STALE_DAYS = 365
STUCK_READINGS = 7


def _hist(ml, sid):
    h = ml["hist"]
    return h[h["station_id"] == sid].sort_values("date")


def status(ml, sid, days=30):
    h = _hist(ml, sid).dropna(subset=["level"])

    if h.empty:
        return {
            "station_id": sid,
            "risk": "UNKNOWN",
            "data_age_days": None,
            "trend": "unknown",
            "days": days,
            "advice": ADVICE.get(
                "UNKNOWN",
                "Check station data before making decisions."
            ),
            "alerts": ["No groundwater observations available."]
        }

    latest_date = pd.Timestamp(h["date"].iloc[-1])
    today = pd.Timestamp.now().normalize()

    data_age_days = max(
        0,
        (today - latest_date.normalize()).days
    )

    cur = float(h["level"].iloc[-1])

    # Check whether the latest available readings are identical.
    recent = h.tail(STUCK_READINGS)["level"]
    stuck = (
        len(recent) >= STUCK_READINGS
        and recent.nunique() == 1
    )

    stale = data_age_days > STALE_DAYS

    # Get the requested forecast horizon.
    fc = ml["fc"].get(sid, [])
    forecast_available = len(fc) >= days

    if forecast_available:
        end = float(fc[days - 1]["level"])
        change = round(end - cur, 3)
    else:
        end = cur
        change = 0.0

    # Unreliable observations or insufficient forecasts mean UNKNOWN.
    if stale or stuck or not forecast_available:
        r = "UNKNOWN"
    else:
        r = risk(change, ml["th"])

    alerts_out = []

    if stale:
        alerts_out.append("Groundwater data is stale.")

    if stuck:
        alerts_out.append(
            "Groundwater station readings appear stuck."
        )

    if not forecast_available:
        alerts_out.append("Insufficient forecast data.")

    return {
        "station_id": sid,
        "as_of": latest_date.date(),
        "level": round(cur, 2),
        "trend": trend(h["level"].tail(14).tolist()),
        "risk": r,
        "days": days,
        "data_age_days": data_age_days,
        "forecast_level": end,
        "change_m": change,
        "advice": ADVICE.get(
            r,
            "Check station data before making decisions."
        ),
        "alerts": alerts_out
    }


def stations(ml):
    out = []

    for r in ml["stations"].itertuples():
        if r.station_id in ml["fc"]:
            s = status(ml, r.station_id)

            out.append({
                "id": r.station_id,
                "name": str(r.name),
                "district": str(r.district),
                "lat": r.lat,
                "lon": r.lon,
                "level": s.get("level"),
                "risk": s["risk"]
            })

    return out


def forecast_view(ml, sid, days):
    h = (
        _hist(ml, sid)
        .dropna(subset=["level"])
        .tail(90)
    )

    return {
        "station_id": sid,
        "observed": [
            {"date": d.date(), "level": round(v, 2)}
            for d, v in zip(h["date"], h["level"])
        ],
        "forecast": ml["fc"][sid][:days]
    }


def history(ml, sid, start=None, end=None):
    h = _hist(ml, sid).dropna(subset=["level"])

    if start:
        h = h[h["date"] >= pd.Timestamp(start)]

    if end:
        h = h[h["date"] <= pd.Timestamp(end)]

    return {
        "station_id": sid,
        "observed": [
            {"date": d.date(), "level": round(v, 2)}
            for d, v in zip(h["date"], h["level"])
        ]
    }


def alerts(ml, sid):
    s = status(ml, sid)
    out = list(s.get("alerts", []))

    if s.get("trend") == "declining":
        out.append(
            "Groundwater level is declining in your area."
        )

    if s["risk"] != "SAFE" and not any(
        f"Risk over the next {s['days']} days:" in a
        for a in out
    ):
        out.append(
            f"Risk over the next {s['days']} days: {s['risk']}."
        )

    return {
        "station_id": sid,
        "alerts": out
    }


def anomalies(ml, sid):
    h = (
        _hist(ml, sid)
        .dropna(subset=["level"])
        .reset_index(drop=True)
    )

    return {
        "station_id": sid,
        "events": _anomalies(h)
    }


def recharge(ml, sid):
    h = _hist(ml, sid).dropna(subset=["level"])

    return {
        "station_id": sid,
        "years": _recharge(h)
    }


def whatif(ml, sid, usage, days):
    cur = float(
        _hist(ml, sid)
        .dropna(subset=["level"])["level"]
        .iloc[-1]
    )

    base = ml["fc"][sid][:days]

    scen = [
        {
            "date": p["date"],
            "level": round(
                cur + (p["level"] - cur) * FACTOR[usage],
                3
            )
        }
        for p in base
    ]

    return {
        "note": (
            "Simulated scenario, not an ML forecast: "
            "usage scales the predicted change."
        ),
        "baseline": base,
        "scenario": scen
    }
