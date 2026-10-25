"""Build a static copy of the dashboard for GitHub Pages.

    python frontend/export_static.py [out_dir]      (default: dist/)

Runs the FastAPI backend in-process (unchanged; needs models/model.joblib, so run
`python -m src.train` first), calls every endpoint the dashboard uses, and saves each
response as a JSON file next to the frontend files. The .github/workflows/pages.yml
workflow runs this on every push to main and publishes the result.
"""
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "dist"
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

HORIZONS = (7, 14, 30)
USAGES = ("low", "medium", "high")


def save(rel, resp):
    if resp.status_code != 200:
        raise SystemExit(f"{rel}: API returned {resp.status_code} {resp.text}")
    f = OUT / "data" / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(resp.json()))


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    with TestClient(app) as c:
        save("model.json", c.get("/api/v1/model"))
        stations = c.get("/api/v1/stations")
        save("stations.json", stations)
        for s in stations.json():
            sid = s["id"]
            base = f"/api/v1/stations/{sid}"
            for d in HORIZONS:
                save(f"stations/{sid}/status-{d}.json", c.get(f"{base}/status?days={d}"))
                save(f"stations/{sid}/forecast-{d}.json", c.get(f"{base}/forecast?days={d}"))
                for u in USAGES:
                    save(f"whatif/{sid}-{u}-{d}.json",
                         c.post("/api/v1/whatif", json={"station_id": sid, "usage": u, "days": d}))
            save(f"stations/{sid}/recharge.json", c.get(f"{base}/recharge"))
            save(f"stations/{sid}/anomalies.json", c.get(f"{base}/anomalies"))
            print("exported", sid, s["name"])

    for name in ("index.html", "styles.css", "app.js"):
        shutil.copy(HERE / name, OUT / name)
    (OUT / "config.js").write_text(
        "// Static build: data/ holds saved API responses.\n"
        f'window.STATIC_SNAPSHOT = "{dt.date.today().isoformat()}";\n')
    (OUT / ".nojekyll").write_text("")   # serve files as-is on GitHub Pages
    print("static site written to", OUT)


if __name__ == "__main__":
    main()
