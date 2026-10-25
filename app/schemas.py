
import datetime as dt
from typing import Literal, Optional

from pydantic import BaseModel, Field


Risk = Literal["SAFE", "WATCH", "CRITICAL", "UNKNOWN"]


class Point(BaseModel):
    date: dt.date
    level: float


class Station(BaseModel):
    id: str
    name: str
    district: str
    lat: float
    lon: float
    level: Optional[float] = None
    risk: Risk


class Status(BaseModel):
    station_id: str
    as_of: Optional[dt.date] = None
    level: Optional[float] = None
    trend: Literal["declining", "stable", "improving", "unknown"]
    risk: Risk
    days: int
    data_age_days: Optional[int] = None
    forecast_level: Optional[float] = None
    change_m: Optional[float] = None
    advice: str
    alerts: list[str] = Field(default_factory=list)


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
