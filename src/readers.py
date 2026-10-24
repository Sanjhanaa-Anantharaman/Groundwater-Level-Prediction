import pandas as pd

def read_station_file(path):
    meta, tabs = {}, []
    for raw in pd.read_excel(path, sheet_name=None, header=None).values():
        c0 = raw[0].astype(str).str.strip().str.lower()
        if (c0 == "station code").any():
            meta = dict(zip(c0, raw[1]))
        elif (c0 == "data type code").any():
            k = c0.index[c0 == "data type code"][0]
            t = raw.loc[k+1:].copy()
            t.columns = [str(c).strip().lower() for c in raw.loc[k]]
            tabs.append(t)
    return meta, (pd.concat(tabs) if tabs else pd.DataFrame())