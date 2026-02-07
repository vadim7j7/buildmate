# FastAPI Testing Patterns

Testing patterns and conventions for Python FastAPI applications using pytest.
All agents must follow these patterns when writing tests.

---

## 1. Test File Organization

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── test_services.py
│   ├── test_schemas.py
│   └── test_utils.py
├── integration/             # Integration tests
│   ├── test_api_users.py
│   ├── test_api_projects.py
│   └── test_auth.py
├── e2e/                     # End-to-end tests
│   └── test_user_journey.py
└── factories/               # Test data factories
    ├── __init__.py
    └── user.py
```

---

## 2. Fixtures Setup

### conftest.py

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.database import get_db, Base
from app.config import settings

# Use test database
TEST_DATABASE_URL = settings.DATABASE_URL.replace("/myapp", "/myapp_test")

engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,  # Disable pooling for tests
)
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db():
    """Create tables and provide a test database session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db: AsyncSession):
    """Create test client with database override."""
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def authenticated_client(client: AsyncClient, user: "User"):
    """Client with authentication headers."""
    from app.auth.jwt import create_access_token

    token = create_access_token({"sub": str(user.id)})
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
async def user(db: AsyncSession):
    """Create a test user."""
    from app.models import User
    from app.auth.jwt import get_password_hash

    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("TestPassword123!"),
        name="Test User",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def admin_user(db: AsyncSession):
    """Create an admin user."""
    from app.models import User
    from app.auth.jwt import get_password_hash

    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("AdminPassword123!"),
        name="Admin User",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
```

---

## 3. API Endpoint Tests

### CRUD Endpoint Tests

```python
# tests/integration/test_api_users.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


class TestUserEndpoints:
    """Tests for /api/v1/users endpoints."""

    async def test_list_users(
        self, authenticated_client: AsyncClient, user: User
    ):
        """GET /users returns list of users."""
        response = await authenticated_client.get("/api/v1/users")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 1
        assert data["data"][0]["email"] == user.email

    async def test_list_users_pagination(
        self, authenticated_client: AsyncClient, db: AsyncSession
    ):
        """GET /users respects pagination params."""
        # Create 25 users
        for i in range(25):
            db.add(User(email=f"user{i}@example.com", name=f"User {i}"))
        await db.commit()

        response = await authenticated_client.get(
            "/api/v1/users", params={"page": 2, "per_page": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 10
        assert data["meta"]["page"] == 2
        assert data["meta"]["total"] >= 25

    async def test_get_user(
        self, authenticated_client: AsyncClient, user: User
    ):
        """GET /users/{id} returns user details."""
        response = await authenticated_client.get(f"/api/v1/users/{user.id}")

        assert response.status_code == 200
        assert response.json()["email"] == user.email

    async def test_get_user_not_found(self, authenticated_client: AsyncClient):
        """GET /users/{id} returns 404 for non-existent user."""
        response = await authenticated_client.get(
            "/api/v1/users/00000000-0000-0000-0000-000000000000"
        )

        assert response.status_code == 404

    async def test_create_user(self, client: AsyncClient, db: AsyncSession):
        """POST /users creates a new user."""
        response = await client.post(
            "/api/v1/users",
            json={
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
                "name": "New User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "password" not in data  # Password not exposed
        assert "id" in data

    async def test_create_user_duplicate_email(
        self, client: AsyncClient, user: User
    ):
        """POST /users rejects duplicate email."""
        response = await client.post(
            "/api/v1/users",
            json={
                "email": user.email,  # Existing email
                "password": "SecurePassword123!",
                "name": "Another User",
            },
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    async def test_create_user_invalid_email(self, client: AsyncClient):
        """POST /users validates email format."""
        response = await client.post(
            "/api/v1/users",
            json={
                "email": "not-an-email",
                "password": "SecurePassword123!",
                "name": "User",
            },
        )

        assert response.status_code == 422

    async def test_update_user(
        self, authenticated_client: AsyncClient, user: User
    ):
        """PATCH /users/{id} updates user."""
        response = await authenticated_client.patch(
            f"/api/v1/users/{user.id}",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    async def test_delete_user(
        self, authenticated_client: AsyncClient, user: User, db: AsyncSession
    ):
        """DELETE /users/{id} removes user."""
        response = await authenticated_client.delete(
            f"/api/v1/users/{user.id}"
        )

        assert response.status_code == 204

        # Verify deleted
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.id == user.id))
        assert result.scalar_one_or_none() is None
```

---

## 4. Authentication Tests

```python
# tests/integration/test_auth.py
import pytest
from httpx import AsyncClient
from datetime import timedelta

from app.auth.jwt import create_access_token


class TestAuthentication:
    """Tests for authentication endpoints and middleware."""

    async def test_login_success(self, client: AsyncClient, user):
        """POST /auth/token returns token for valid credentials."""
        response = await client.post(
            "/auth/token",
            data={
                "username": "test@example.com",
                "password": "TestPassword123!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_password(self, client: AsyncClient, user):
        """POST /auth/token rejects invalid password."""
        response = await client.post(
            "/auth/token",
            data={
                "username": "test@example.com",
                "password": "WrongPassword!",
            },
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_login_user_not_found(self, client: AsyncClient):
        """POST /auth/token rejects non-existent user."""
        response = await client.post(
            "/auth/token",
            data={
                "username": "nonexistent@example.com",
                "password": "Password123!",
            },
        )

        assert response.status_code == 401

    async def test_protected_endpoint_without_token(self, client: AsyncClient):
        """Protected endpoint returns 401 without token."""
        response = await client.get("/api/v1/users/me")

        assert response.status_code == 401

    async def test_protected_endpoint_with_invalid_token(
        self, client: AsyncClient
    ):
        """Protected endpoint returns 401 with invalid token."""
        client.headers["Authorization"] = "Bearer invalid-token"
        response = await client.get("/api/v1/users/me")

        assert response.status_code == 401

    async def test_protected_endpoint_with_expired_token(
        self, client: AsyncClient, user
    ):
        """Protected endpoint returns 401 with expired token."""
        expired_token = create_access_token(
            {"sub": str(user.id)},
            expires_delta=timedelta(seconds=-1),  # Already expired
        )
        client.headers["Authorization"] = f"Bearer {expired_token}"

        response = await client.get("/api/v1/users/me")

        assert response.status_code == 401

    async def test_get_current_user(
        self, authenticated_client: AsyncClient, user
    ):
        """GET /users/me returns current user."""
        response = await authenticated_client.get("/api/v1/users/me")

        assert response.status_code == 200
        assert response.json()["email"] == user.email
```

---

## 5. Service Layer Tests

```python
# tests/unit/test_services.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_service import UserService
from app.schemas.user import UserCreate


class TestUserService:
    """Unit tests for UserService."""

    async def test_create_user(self, db: AsyncSession):
        """create() creates and returns a new user."""
        service = UserService(db)
        user_data = UserCreate(
            email="new@example.com",
            password="SecurePassword123!",
            name="New User",
        )

        user = await service.create(user_data)

        assert user.email == "new@example.com"
        assert user.name == "New User"
        assert user.id is not None

    async def test_create_user_hashes_password(self, db: AsyncSession):
        """create() hashes the password."""
        service = UserService(db)
        user_data = UserCreate(
            email="new@example.com",
            password="SecurePassword123!",
            name="New User",
        )

        user = await service.create(user_data)

        assert user.hashed_password != "SecurePassword123!"
        assert len(user.hashed_password) > 50  # bcrypt hash length

    async def test_get_by_email(self, db: AsyncSession, user):
        """get_by_email() returns user with matching email."""
        service = UserService(db)

        result = await service.get_by_email("test@example.com")

        assert result is not None
        assert result.id == user.id

    async def test_get_by_email_not_found(self, db: AsyncSession):
        """get_by_email() returns None for non-existent email."""
        service = UserService(db)

        result = await service.get_by_email("nonexistent@example.com")

        assert result is None

    async def test_authenticate_success(self, db: AsyncSession, user):
        """authenticate() returns user for valid credentials."""
        service = UserService(db)

        result = await service.authenticate(
            "test@example.com", "TestPassword123!"
        )

        assert result is not None
        assert result.id == user.id

    async def test_authenticate_wrong_password(self, db: AsyncSession, user):
        """authenticate() returns None for wrong password."""
        service = UserService(db)

        result = await service.authenticate(
            "test@example.com", "WrongPassword!"
        )

        assert result is None

    async def test_update_user(self, db: AsyncSession, user):
        """update() modifies user fields."""
        service = UserService(db)

        updated = await service.update(user.id, {"name": "Updated Name"})

        assert updated.name == "Updated Name"
        assert updated.email == user.email  # Unchanged

    async def test_delete_user(self, db: AsyncSession, user):
        """delete() removes user from database."""
        service = UserService(db)

        await service.delete(user.id)

        result = await service.get_by_id(user.id)
        assert result is None
```

---

## 6. Schema Validation Tests

```python
# tests/unit/test_schemas.py
import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserUpdate


class TestUserCreateSchema:
    """Tests for UserCreate schema validation."""

    def test_valid_user(self):
        """Valid data creates schema instance."""
        user = UserCreate(
            email="test@example.com",
            password="SecurePassword123!",
            name="Test User",
        )

        assert user.email == "test@example.com"

    def test_invalid_email(self):
        """Invalid email raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="not-an-email",
                password="SecurePassword123!",
                name="Test",
            )

        assert "email" in str(exc_info.value)

    def test_password_too_short(self):
        """Short password raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="short",
                name="Test",
            )

        assert "password" in str(exc_info.value)

    def test_password_requires_uppercase(self):
        """Password without uppercase raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="nouppercase123!",
                name="Test",
            )

        assert "uppercase" in str(exc_info.value).lower()

    def test_password_requires_digit(self):
        """Password without digit raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="NoDigitsHere!",
                name="Test",
            )

        assert "digit" in str(exc_info.value).lower()

    def test_name_too_short(self):
        """Name that's too short raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="SecurePassword123!",
                name="X",
            )

        assert "name" in str(exc_info.value).lower()

    def test_extra_fields_rejected(self):
        """Extra fields raise ValidationError."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="SecurePassword123!",
                name="Test",
                is_admin=True,  # Extra field
            )
```

---

## 7. Database Query Tests

```python
# tests/unit/test_queries.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.models import User, Project
from app.queries.project import get_user_projects, get_project_with_tasks


class TestProjectQueries:
    """Tests for project database queries."""

    @pytest.fixture
    async def projects(self, db: AsyncSession, user):
        """Create test projects."""
        projects = [
            Project(name="Project 1", owner_id=user.id),
            Project(name="Project 2", owner_id=user.id),
            Project(name="Project 3", owner_id=user.id, archived=True),
        ]
        for p in projects:
            db.add(p)
        await db.commit()
        return projects

    async def test_get_user_projects(
        self, db: AsyncSession, user, projects
    ):
        """get_user_projects() returns user's non-archived projects."""
        result = await get_user_projects(db, user.id)

        assert len(result) == 2
        assert all(p.owner_id == user.id for p in result)
        assert all(not p.archived for p in result)

    async def test_get_user_projects_empty(self, db: AsyncSession, user):
        """get_user_projects() returns empty list for user with no projects."""
        result = await get_user_projects(db, user.id)

        assert result == []

    async def test_get_user_projects_include_archived(
        self, db: AsyncSession, user, projects
    ):
        """get_user_projects() can include archived projects."""
        result = await get_user_projects(db, user.id, include_archived=True)

        assert len(result) == 3

    async def test_get_project_with_tasks_eager_loads(
        self, db: AsyncSession, user, projects
    ):
        """get_project_with_tasks() eager loads tasks."""
        project = projects[0]
        # Add tasks
        from app.models import Task
        for i in range(3):
            db.add(Task(name=f"Task {i}", project_id=project.id))
        await db.commit()

        result = await get_project_with_tasks(db, project.id)

        # Accessing tasks shouldn't trigger additional query
        assert len(result.tasks) == 3
```

---

## 8. Mocking External Services

```python
# tests/integration/test_external_services.py
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

from app.services.payment import PaymentService


class TestPaymentIntegration:
    """Tests for payment service integration."""

    @pytest.fixture
    def mock_stripe(self):
        """Mock Stripe API."""
        with patch("app.services.payment.stripe") as mock:
            mock.Charge.create = AsyncMock(
                return_value={"id": "ch_test123", "status": "succeeded"}
            )
            yield mock

    async def test_charge_success(
        self, authenticated_client: AsyncClient, mock_stripe
    ):
        """POST /payments/charge succeeds with valid data."""
        response = await authenticated_client.post(
            "/api/v1/payments/charge",
            json={"amount": 1000, "source": "tok_visa"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "succeeded"
        mock_stripe.Charge.create.assert_called_once()

    async def test_charge_failure(
        self, authenticated_client: AsyncClient, mock_stripe
    ):
        """POST /payments/charge handles Stripe errors."""
        mock_stripe.Charge.create.side_effect = Exception("Card declined")

        response = await authenticated_client.post(
            "/api/v1/payments/charge",
            json={"amount": 1000, "source": "tok_chargeDeclined"},
        )

        assert response.status_code == 400
        assert "declined" in response.json()["detail"].lower()


class TestEmailService:
    """Tests for email service."""

    @pytest.fixture
    def mock_smtp(self):
        """Mock SMTP client."""
        with patch("app.services.email.smtp_client") as mock:
            mock.send = AsyncMock(return_value=True)
            yield mock

    async def test_send_welcome_email(self, mock_smtp, user):
        """send_welcome_email() sends email to user."""
        from app.services.email import send_welcome_email

        await send_welcome_email(user)

        mock_smtp.send.assert_called_once()
        call_args = mock_smtp.send.call_args
        assert user.email in call_args[1]["to"]
        assert "welcome" in call_args[1]["subject"].lower()
```

---

## 9. Fixtures and Factories

```python
# tests/factories/user.py
from typing import Any
from faker import Faker

from app.models import User
from app.auth.jwt import get_password_hash

fake = Faker()


def build_user(**overrides: Any) -> dict:
    """Build user data dict without persisting."""
    return {
        "email": fake.email(),
        "name": fake.name(),
        "hashed_password": get_password_hash("Password123!"),
        **overrides,
    }


async def create_user(db, **overrides: Any) -> User:
    """Create and persist a user."""
    data = build_user(**overrides)
    user = User(**data)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_users(db, count: int, **overrides: Any) -> list[User]:
    """Create multiple users."""
    users = []
    for _ in range(count):
        user = await create_user(db, **overrides)
        users.append(user)
    return users


# Usage in tests
async def test_with_factory(db):
    user = await create_user(db, name="Custom Name")
    assert user.name == "Custom Name"

    users = await create_users(db, 10, role="admin")
    assert len(users) == 10
    assert all(u.role == "admin" for u in users)
```

---

## 10. Performance Testing

```python
# tests/performance/test_endpoints.py
import pytest
from httpx import AsyncClient
import asyncio
import time


class TestEndpointPerformance:
    """Performance tests for critical endpoints."""

    @pytest.mark.slow
    async def test_list_users_performance(
        self, authenticated_client: AsyncClient, db
    ):
        """GET /users responds within acceptable time with many users."""
        # Create 1000 users
        from tests.factories.user import create_users
        await create_users(db, 1000)

        start = time.time()
        response = await authenticated_client.get(
            "/api/v1/users", params={"per_page": 100}
        )
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.5  # Should respond within 500ms

    @pytest.mark.slow
    async def test_concurrent_requests(
        self, authenticated_client: AsyncClient
    ):
        """Endpoint handles concurrent requests."""
        async def make_request():
            return await authenticated_client.get("/api/v1/users")

        # Make 50 concurrent requests
        tasks = [make_request() for _ in range(50)]
        responses = await asyncio.gather(*tasks)

        assert all(r.status_code == 200 for r in responses)
```

---

## Quick Reference

| Test Type | Location | Purpose |
|-----------|----------|---------|
| Unit | `tests/unit/` | Services, schemas, utils |
| Integration | `tests/integration/` | API endpoints |
| E2E | `tests/e2e/` | Full user flows |
| Performance | `tests/performance/` | Load testing |

### pytest Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific file
pytest tests/integration/test_api_users.py

# Run specific test
pytest tests/integration/test_api_users.py::TestUserEndpoints::test_create_user

# Run tests matching pattern
pytest -k "test_create"

# Run tests with markers
pytest -m "not slow"

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Markers

```python
# In pyproject.toml or pytest.ini
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
]

# Usage
@pytest.mark.slow
async def test_large_dataset():
    ...

@pytest.mark.integration
async def test_api_endpoint():
    ...
```
