import datetime as dt
from typing import Literal
from pydantic import BaseModel, Field

Risk = Literal["SAFE", "WATCH", "CRITICAL"]


class Point(BaseModel):
    date: dt.date
    level: float


class Station(BaseModel):
    id: str
    name: str
    district: str
    lat: float
    lon: float
    level: float
    risk: Risk


class Status(BaseModel):
    station_id: str
    as_of: dt.date
    level: float
    trend: Literal["declining", "stable", "improving"]
    risk: Risk
    days: int
    forecast_level: float
    change_m: float
    advice: str


class ForecastOut(BaseModel):
    station_id: str
    observed: list[Point]
    forecast: list[Point]


class HistoryOut(BaseModel):
    station_id: str
    observed: list[Point]


class Alerts(BaseModel):
    station_id: str
    alerts: list[str]


class Anomaly(BaseModel):
    date: dt.date
    level: float
    change: float


class AnomaliesOut(BaseModel):
    station_id: str
    events: list[Anomaly]


class RechargeYear(BaseModel):
    year: int
    rise_m: float


class RechargeOut(BaseModel):
    station_id: str
    years: list[RechargeYear]


class WhatIfIn(BaseModel):
    station_id: str
    usage: Literal["low", "medium", "high"]
    days: int = Field(30, ge=1, le=30)


class WhatIfOut(BaseModel):
    simulated: bool = True
    note: str
    baseline: list[Point]
    scenario: list[Point]