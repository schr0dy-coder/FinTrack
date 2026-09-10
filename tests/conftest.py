"""Test suite configuration and fixtures."""

from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, get_password_hash
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User

# Use in-memory SQLite for fast, isolated testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Provide a clean in-memory database session for each test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide a TestClient connected to the in-memory test database."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_user(db_session: Session) -> User:
    """Create a test administrator user."""
    user = User(
        name="Admin Tester",
        email="admin_test@fintrack.com",
        password_hash=get_password_hash("AdminPass123"),
        role="ADMIN",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def regular_user(db_session: Session) -> User:
    """Create a standard test customer user."""
    user = User(
        name="John Tester",
        email="user_test@fintrack.com",
        password_hash=get_password_hash("UserPass123"),
        role="USER",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_headers(admin_user: User) -> dict:
    """Return authorization headers for the admin user."""
    token = create_access_token(subject=admin_user.id, role=admin_user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def user_headers(regular_user: User) -> dict:
    """Return authorization headers for the regular user."""
    token = create_access_token(subject=regular_user.id, role=regular_user.role)
    return {"Authorization": f"Bearer {token}"}
