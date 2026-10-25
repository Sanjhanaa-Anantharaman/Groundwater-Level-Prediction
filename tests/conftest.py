import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import Ridge
from app.deps import get_ml
from app.main import app
from src.features import FEATURES, make_features
from src.forecast import build_ml


@pytest.fixture(scope="session")
def client():
    rng = np.random.default_rng(0)
    d = pd.date_range("2024-01-01", periods=400)
    hist = pd.concat([
        pd.DataFrame({"station_id": sid, "date": d,
                      "level": 5 + i + 0.004 * np.arange(400) + rng.normal(0, 0.02, 400),
                      "rain": rng.gamma(1, 2, 400)})
        for i, sid in enumerate(["A", "B"])]
        + [pd.DataFrame({"station_id": "C", "date": d, "level": 5.0, "rain": rng.gamma(1, 2, 400)})])
    f = make_features(hist).dropna(subset=FEATURES)
    model = Ridge().fit(f[FEATURES], f["level"])
    st = pd.DataFrame({"station_id": ["A", "B", "C"], "name": ["a", "b", "c"], "district": ["x"] * 3,
                       "lat": [18.0, 18.1, 18.2], "lon": [73.0, 73.1, 73.2]})
    ml = build_ml({"model": model, "name": "ridge", "metrics": {}}, hist, st,
                  {"watch": 0.1, "critical": 0.4})
    app.dependency_overrides[get_ml] = lambda: ml
    yield TestClient(app)
    app.dependency_overrides.clear()