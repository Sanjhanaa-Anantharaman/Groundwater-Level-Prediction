def recharge(h, pre=5, post=10):
    h = h.assign(y=h["date"].dt.year, m=h["date"].dt.month)
    out = []
    for y, g in h.groupby("y"):
        a, b = g[g["m"] == pre]["level"].mean(), g[g["m"] == post]["level"].mean()
        if a == a and b == b:
            out.append({"year": int(y), "rise_m": round(float(a - b), 2)})
    return out