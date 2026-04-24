from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api.deliveries import router as deliveries_router
from backend.app.api.endpoints import router as endpoints_router
from backend.app.api.events import router as events_router
from backend.app.api.system import router as system_router
from backend.app.api.test_webhooks import router as test_webhooks_router
from backend.app.db.database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="EventRelay", version="0.1.0", lifespan=lifespan)

app.include_router(endpoints_router)
app.include_router(events_router)
app.include_router(deliveries_router)
app.include_router(system_router)
app.include_router(test_webhooks_router)


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
