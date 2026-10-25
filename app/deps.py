from fastapi import Depends, HTTPException, Request


def get_ml(request: Request):
    return request.app.state.ml


def valid_station(station_id: str, ml=Depends(get_ml)) -> str:
    if station_id not in ml["fc"]:
        raise HTTPException(404, f"Unknown station {station_id}")
    return station_id