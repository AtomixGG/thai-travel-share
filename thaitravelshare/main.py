from contextlib import asynccontextmanager
from fastapi import FastAPI

from .core.database import init_db, close_db
from . import routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(lifespan=lifespan)
app.include_router(routers.router)


@app.get("/")
def read_root() -> dict:
    return {"Hello": "World"}