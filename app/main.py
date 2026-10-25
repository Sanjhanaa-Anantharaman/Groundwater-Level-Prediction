from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.forecast import load
from .routes import router


@asynccontextmanager
async def lifespan(app):
    app.state.ml = load()
    yield


app = FastAPI(title="Groundwater Forecast API", lifespan=lifespan)
app.include_router(router)