from src.risk import risk, trend

TH = {"watch": 0.1, "critical": 0.4}


def test_risk_levels():
    assert risk(0.0, TH) == "SAFE"
    assert risk(0.2, TH) == "WATCH"
    assert risk(0.5, TH) == "CRITICAL"


def test_trend():
    assert trend([5.0, 5.1, 5.2, 5.3]) == "declining"
    assert trend([5.3, 5.2, 5.1, 5.0]) == "improving"
    assert trend([5.0, 5.0, 5.0, 5.0]) == "stable"