import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from watchtower.database import Base, get_db
from watchtower.main import app
from watchtower.rate_limit import limiter


@pytest.fixture()
def db_session():
    # StaticPool keeps every connection on the same in-memory SQLite DB —
    # without it, each new connection gets its own blank database and
    # tables created in setup "disappear" for later queries.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    limiter.reset()  # each test gets a fresh rate-limit window
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
