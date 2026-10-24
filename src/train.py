import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from .config import DAILY, MODEL_PATH, THRESHOLDS, FOLD_YEARS, MAX_HORIZON
from .evaluate import horizon_errors, split, HORIZONS
from .features import make_features, FEATURES

CANDIDATES = {"ridge": lambda: Ridge(1.0), "gbr": lambda: GradientBoostingRegressor(random_state=42)}

def main():
    daily = pd.read_csv(DAILY, parse_dates=["date"], dtype={"station_id": str})
    feat = make_features(daily).dropna(subset=FEATURES+ ["level"])

    results = {}

    for name, make in CANDIDATES.items():
        folds = []

        for y in FOLD_YEARS:
            tr = split(feat, y)
            m = make().fit(tr[FEATURES], tr["level"])
            folds.append(horizon_errors(m, daily, y))

        results[name] = {
            h: tuple(
                np.mean([f[h] for f in folds if h in f], axis=0)
            )
            for h in HORIZONS
        }

        print(
            name,
            {
                h: f"model {a:.3f} m vs persistence {b:.3f} m"
                for h, (a, b) in results[name].items()
            }
        )

    best = min(results, key=lambda k: results[k][30][0])
    print("best:", best)

    model = CANDIDATES[best]().fit(feat[FEATURES], feat["level"])

    metrics = {
        f"mae_{h}": results[best][h][0]
        for h in HORIZONS
    }

    metrics.update({
        f"persistence_mae_{h}": results[best][h][1]
        for h in HORIZONS
    })

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        {
            "model": model,
            "name": best,
            "metrics": metrics,
        },
        MODEL_PATH,
    )

    chg = (
        daily.groupby("station_id")["level"].shift(-MAX_HORIZON)
        - daily["level"]
    ).dropna()

    th = {
        "watch": float(chg.quantile(0.70)),
        "critical": float(chg.quantile(0.90)),
    }

    THRESHOLDS.write_text(json.dumps(th))

    print("thresholds (m per", MAX_HORIZON, "days):", th)


if __name__ == "__main__":
    main()

    