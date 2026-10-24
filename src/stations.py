import pandas as pd
from .config import RAW_DIR, STATIONS
from .readers import read_station_file

def build_stations():
    rows = {}
    for f in sorted(RAW_DIR.glob("*.xlsx")):
        m, _ = read_station_file(f)
        code = str(m.get("station code", f.stem)).strip()
        rows[code] = {"station_id": code, "name":m.get("station name"), 
                      "district": m.get("district"), "lat": float(m["latitude"]), "lon": float(m["longitude"]),
                      "aquifer": m.get("aquifer type"), "well_depth_m": float(m.get("well depth"))}
    df = pd.DataFrame(rows.values())
    STATIONS.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(STATIONS, index=False)
    print(df)
    return df

if __name__ == "__main__":
    build_stations()