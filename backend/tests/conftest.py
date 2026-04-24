from __future__ import annotations

import os
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

TEST_DATABASE_PATH = os.path.join(tempfile.gettempdir(), "eventrelay_test.db")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DATABASE_PATH}")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from backend.app.api import deliveries, events  # noqa: E402
from backend.app.db.database import Base, SessionLocal, engine, get_db_session  # noqa: E402
from backend.app.main import app  # noqa: E402


class FakeRedis:
    def __init__(self) -> None:
        self.items: list[str] = []

    def lpush(self, _queue_name: str, value: str) -> None:
        self.items.append(value)


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Generator:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, db_session) -> Generator[TestClient, None, None]:
    fake_redis = FakeRedis()

    def override_get_db() -> Generator:
        try:
            yield db_session
        finally:
            pass

    monkeypatch.setattr(events, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(deliveries, "get_redis_client", lambda: fake_redis)
    app.dependency_overrides[get_db_session] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
