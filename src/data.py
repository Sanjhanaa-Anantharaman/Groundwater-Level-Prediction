import pandas as pd
from .config import RAW_DIR, DAILY, RAIN, MAX_GAP, MIN_DAYS, MIN_COV
from .readers import read_station_file


def load_levels():
    out = []
    for f in sorted(RAW_DIR.glob("*.xlsx")):
        meta, d = read_station_file(f)
        if d.empty:
            print("no readings sheet:", f.name)
            continue
        d = d[d["data type description"].astype(str).str.contains("water level", case=False)].copy()
        d["date"] = pd.to_datetime(d["data time"], errors="coerce").dt.normalize()
        d["level"] = pd.to_numeric(d["data value"], errors="coerce")
        d["station_id"] = str(meta.get("station code", f.stem))
        out.append(d[["station_id", "date", "level"]])
    df = pd.concat(out).dropna()
    flip = df.groupby("station_id")["level"].transform("median") < 0
    df.loc[flip, "level"] = -df.loc[flip, "level"]
    return df[df["level"] > 0]


def build_dataset():
    df = load_levels()
    rain = pd.read_csv(RAIN, parse_dates=["date"], dtype={"station_id": str})
    rows = []
    for sid, g in df.groupby("station_id"):
        med = g["level"].median()
        mad = (g["level"] - med).abs().median() or 1e-6
        g = g[(g["level"] - med).abs() < 8 * 1.4826 * mad]
        s = g.groupby("date")["level"].mean().asfreq("D")
        s = s.where((s - s.rolling(7, center=True, min_periods=3).median()).abs() < 1.0)
        s = s.loc[s.first_valid_index(): s.last_valid_index()]
        cov = s.notna().mean()
        s = s.interpolate(limit=MAX_GAP)
        ok = len(s) >= MIN_DAYS and cov >= MIN_COV
        print(f"{sid}: {s.index.min().date()} to {s.index.max().date()} days={len(s)} coverage={cov:.2f} {'KEEP' if ok else 'DROP'}")
        if ok:
            s.index.name = "date"
            r = s.rename("level").reset_index()
            r["station_id"] = sid
            rows.append(r)
    res = pd.concat(rows).merge(rain, on=["station_id", "date"], how="left")
    print("rows without rain (dropped):", int(res["rain"].isna().sum()))
    res = res.dropna(subset=["rain"])
    DAILY.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(DAILY, index=False)
    return res


if __name__ == "__main__":
    build_dataset()