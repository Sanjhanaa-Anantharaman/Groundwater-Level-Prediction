def anomalies(h, win=30, z=3.0):
    d = h["level"].diff()
    s = ((d - d.rolling(win).mean()) / d.rolling(win).std()).abs()
    x = h[h.index.isin(s[s > z].index)]
    return [{"date": r.date.date(), "level": round(r.level, 2), "change": round(c, 3)}
            for r, c in zip(x.itertuples(), d[x.index])]