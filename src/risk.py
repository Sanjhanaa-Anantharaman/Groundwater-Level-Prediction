import numpy as np

ADVICE = {
    "SAFE": "Groundwater is stable or recovering. Continue normal use and keep monitoring.",
    "WATCH": "Groundwater is expected to fall. Use water efficiently and monitor the forecast.",
    "CRITICAL": "Groundwater is expected to fall sharply. Reduce extraction and adopt water-saving practices.",
}


def trend(levels, tol=0.002):
    slope = np.polyfit(range(len(levels)), levels, 1)[0]
    return "declining" if slope > tol else "improving" if slope < -tol else "stable"


def risk(change, th):
    return "CRITICAL" if change >= th["critical"] else "WATCH" if change >= th["watch"] else "SAFE"