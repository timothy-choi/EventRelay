from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db.database import get_db_session
from backend.app.schemas.system import SystemStatsRead
from backend.app.services.queue_service import get_redis_client
from backend.app.services.stats_service import get_system_stats


router = APIRouter(prefix="/system", tags=["system"])


@router.get("/stats", response_model=SystemStatsRead)
def read_system_stats(session: Session = Depends(get_db_session)) -> SystemStatsRead:
    return get_system_stats(session, get_redis_client())
