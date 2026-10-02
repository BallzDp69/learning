import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from acme_orders.db import Base, build_engine, get_session
from acme_orders.main import app


@pytest.fixture
def session(tmp_path) -> Session:
    engine = build_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db_session:
        yield db_session
    engine.dispose()


@pytest.fixture
def client(session: Session):
    def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def user_payload():
    return {"email": "buyer@example.test", "full_name": "Casey Buyer"}


@pytest.fixture
def product_payload():
    return {
        "sku": "WIDGET-1", "name": "Useful Widget", "description": "Very useful",
        "price_cents": 2500, "initial_quantity": 10,
    }
