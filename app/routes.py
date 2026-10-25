import datetime as dt
from typing import Optional
from fastapi import APIRouter, Depends, Query
from src import service
from src.config import MAX_HORIZON
from .deps import get_ml, valid_station
from .schemas import (Alerts, AnomaliesOut, ForecastOut, HistoryOut, RechargeOut,
                      Station, Status, WhatIfIn, WhatIfOut)

router = APIRouter(prefix="/api/v1")
Days = Query(30, ge=1, le=MAX_HORIZON)


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/model")
def model_info(ml=Depends(get_ml)):
    return {"name": ml["bundle"]["name"], "metrics": ml["bundle"]["metrics"]}


@router.get("/stations", response_model=list[Station])
def stations(ml=Depends(get_ml)):
    return service.stations(ml)


@router.get("/stations/{station_id}/status", response_model=Status)
def status(station_id: str = Depends(valid_station), days: int = Days, ml=Depends(get_ml)):
    return service.status(ml, station_id, days)


@router.get("/stations/{station_id}/forecast", response_model=ForecastOut)
def forecast(station_id: str = Depends(valid_station), days: int = Days, ml=Depends(get_ml)):
    return service.forecast_view(ml, station_id, days)


@router.get("/stations/{station_id}/history", response_model=HistoryOut)
def history(station_id: str = Depends(valid_station), start: Optional[dt.date] = None,
            end: Optional[dt.date] = None, ml=Depends(get_ml)):
    return service.history(ml, station_id, start, end)


@router.get("/stations/{station_id}/alerts", response_model=Alerts)
def alerts(station_id: str = Depends(valid_station), ml=Depends(get_ml)):
    return service.alerts(ml, station_id)


@router.get("/stations/{station_id}/anomalies", response_model=AnomaliesOut)
def anomalies(station_id: str = Depends(valid_station), ml=Depends(get_ml)):
    return service.anomalies(ml, station_id)


@router.get("/stations/{station_id}/recharge", response_model=RechargeOut)
def recharge(station_id: str = Depends(valid_station), ml=Depends(get_ml)):
    return service.recharge(ml, station_id)


@router.post("/whatif", response_model=WhatIfOut)
def whatif(body: WhatIfIn, ml=Depends(get_ml)):
    valid_station(body.station_id, ml)
    return service.whatif(ml, body.station_id, body.usage, body.days)