import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.database import Base, get_db
from src.api.models.enterprise import Enterprise
from src.api.models.client import Clients
from src.api.models.product import ProductModel

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(test_engine):
    TestingSessionLocal = sessionmaker(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def test_enterprise(db_session):
    enterprise = Enterprise(
        name="Test Enterprise",
        siret="12345678901234",
        address="123 Test Street",
        email="test@enterprise.com",
        phone="0123456789"
    )
    db_session.add(enterprise)
    db_session.commit()
    return enterprise

@pytest.fixture
def test_client(db_session, test_enterprise):
    client = Clients(
        name="Test Client",
        email="client@test.com",
        address="456 Client Road",
        phone="9876543210",
        enterprise_id=test_enterprise.id
    )
    db_session.add(client)
    db_session.commit()
    return client

@pytest.fixture
def test_product(db_session, test_enterprise):
    product = ProductModel(
        name="Test Product",
        description="Test Description",
        price=100.00,
        enterprise_id=test_enterprise.id
    )
    db_session.add(product)
    db_session.commit()
    return product