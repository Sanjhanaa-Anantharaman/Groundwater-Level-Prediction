def test_health(client):
    assert client.get("/api/v1/health").json() == {"ok": True}


def test_stations_and_status(client):
    s = client.get("/api/v1/stations").json()
    assert {x["id"] for x in s} == {"A", "B", "C"}
    r = client.get("/api/v1/stations/A/status?days=10")
    assert r.status_code == 200 and r.json()["risk"] in {"SAFE", "WATCH", "CRITICAL", "UNKNOWN"}


def test_unknown_station_404(client):
    assert client.get("/api/v1/stations/NOPE/status").status_code == 404


def test_bad_days_422(client):
    assert client.get("/api/v1/stations/A/status?days=999").status_code == 422


def test_forecast_length(client):
    r = client.get("/api/v1/stations/A/forecast?days=7").json()
    assert len(r["forecast"]) == 7 and len(r["observed"]) == 90


def test_whatif_flagged_simulated(client):
    r = client.post("/api/v1/whatif", json={"station_id": "A", "usage": "high", "days": 5})
    assert r.status_code == 200 and r.json()["simulated"] is True
    assert client.post("/api/v1/whatif", json={"station_id": "A", "usage": "x"}).status_code == 422


def test_other_endpoints(client):
    for p in ("alerts", "anomalies", "recharge", "history"):
        assert client.get(f"/api/v1/stations/A/{p}").status_code == 200


def test_stuck_station_is_unknown(client):
    s = client.get("/api/v1/stations/C/status").json()
    assert s["risk"] == "UNKNOWN" and s["data_age_days"] > 0
    assert any("stuck" in a for a in client.get("/api/v1/stations/C/alerts").json()["alerts"])


def test_whatif_more_usage_is_never_better(client):
    last = {}
    for u in ("low", "medium", "high"):
        r = client.post("/api/v1/whatif", json={"station_id": "A", "usage": u, "days": 10}).json()
        last[u] = (r["scenario"][-1]["level"], r["baseline"][-1]["level"])
    assert last["low"][0] < last["medium"][0] < last["high"][0]
    assert last["medium"][0] == last["medium"][1]