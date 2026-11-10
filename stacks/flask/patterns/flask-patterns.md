# Flask Code Patterns

Reference patterns for Flask web application development. Agents should read this file
before writing code to ensure consistency across the codebase.

**Flask code is synchronous.** Flask-SQLAlchemy 3.1 gives a scoped, synchronous
`db.session` bound to the app context: call `db.session.execute(...)`,
`db.session.get(...)`, `db.session.commit()` directly. Never write
`async with db.session()` or `await db.session...` (Flask-SQLAlchemy's session is
not an async context manager — that raises `TypeError`), and do not write
`async def` views or services that touch the database.

Layout: `src/app/` package (`__init__.py` holds `create_app`), `tests/` at the
project root. `.flaskenv` sets `FLASK_APP=app` so `flask run` / `flask db` find the
factory.

---

## 1. App Factory Pattern

All Flask applications use the factory pattern for testability and flexibility.

```python
# src/app/__init__.py
import os

from flask import Flask
from pydantic import ValidationError

from app.config import CONFIGS
from app.extensions import cors, db, migrate


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config_name: Key in ``CONFIGS`` ("development", "testing", "production").
            Defaults to the ``APP_ENV`` environment variable, then "development".

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(CONFIGS[config_name or os.environ.get("APP_ENV", "development")])
    for key in ("SECRET_KEY", "SQLALCHEMY_DATABASE_URI"):
        if not app.config.get(key):
            raise RuntimeError(f"{key} is not configured")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    @app.get("/health")
    def health() -> dict[str, str]:
        """Liveness check used by the dev server verification."""
        return {"status": "ok"}

    register_blueprints(app)
    register_error_handlers(app)

    return app


def register_blueprints(app: Flask) -> None:
    """Register all application blueprints."""
    from app.blueprints.projects import bp as projects_bp
    from app.blueprints.users import bp as users_bp

    app.register_blueprint(projects_bp, url_prefix="/api/projects")
    app.register_blueprint(users_bp, url_prefix="/api/users")


def register_error_handlers(app: Flask) -> None:
    """Register global error handlers."""

    @app.errorhandler(ValidationError)
    def validation_error(error: ValidationError) -> tuple[dict[str, object], int]:
        return {"errors": error.errors(include_url=False)}, 422

    @app.errorhandler(404)
    def not_found(error: Exception) -> tuple[dict[str, str], int]:
        return {"error": "Not found"}, 404

    @app.errorhandler(500)
    def internal_error(error: Exception) -> tuple[dict[str, str], int]:
        db.session.rollback()
        return {"error": "Internal server error"}, 500
```

### App Factory Rules

- Always use `create_app()` — never instantiate `Flask()` at module level
- Initialize extensions with `ext.init_app(app)`, not in constructors
- Keep the `/health` route (the dev-server verification calls it)
- Register blueprints in a dedicated function
- Register error handlers globally
- Load config from the `CONFIGS` mapping of config classes

---

## 2. Blueprint Pattern

Blueprints organize routes by resource. Each blueprint lives in its own module.
Views are plain (sync) functions.

```python
# src/app/blueprints/projects.py
from flask import Blueprint, Response, g, jsonify, request

from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.project_service import ProjectService

bp = Blueprint("projects", __name__)


@bp.get("/")
def list_projects() -> Response:
    """List all projects with pagination."""
    skip = request.args.get("skip", 0, type=int)
    limit = min(request.args.get("limit", 20, type=int), 100)
    projects = ProjectService().list(skip=skip, limit=limit)
    return jsonify([ProjectRead.model_validate(p).model_dump(mode="json") for p in projects])


@bp.post("/")
def create_project() -> tuple[Response, int]:
    """Create a new project."""
    data = ProjectCreate.model_validate(request.get_json())
    project = ProjectService().create(data, owner_id=g.user.id)  # g.user set by your auth hook
    return jsonify(ProjectRead.model_validate(project).model_dump(mode="json")), 201


@bp.get("/<int:project_id>")
def get_project(project_id: int) -> Response | tuple[dict[str, str], int]:
    """Get a single project by ID."""
    project = ProjectService().get_by_id(project_id)
    if project is None:
        return {"error": "Project not found"}, 404
    return jsonify(ProjectRead.model_validate(project).model_dump(mode="json"))


@bp.patch("/<int:project_id>")
def update_project(project_id: int) -> Response | tuple[dict[str, str], int]:
    """Update a project by ID (partial update)."""
    data = ProjectUpdate.model_validate(request.get_json())
    project = ProjectService().update(project_id, data)
    if project is None:
        return {"error": "Project not found"}, 404
    return jsonify(ProjectRead.model_validate(project).model_dump(mode="json"))


@bp.delete("/<int:project_id>")
def delete_project(project_id: int) -> tuple[str, int] | tuple[dict[str, str], int]:
    """Delete a project by ID."""
    if not ProjectService().delete(project_id):
        return {"error": "Project not found"}, 404
    return "", 204
```

### Blueprint Rules

- Use `Blueprint("name", __name__)` — name matches the resource
- Use decorator shortcuts: `@bp.get()`, `@bp.post()`, `@bp.patch()`, `@bp.delete()`
- Views are sync `def` functions (no `async def`, no `await`)
- Parse numeric query params with `request.args.get(key, default, type=int)`
- Never use `type=bool` for query params (`bool("false")` is `True`); use `parse_bool` (section 5)
- Parse JSON body with `request.get_json()`
- Validate input with Pydantic schemas
- Delegate business logic to service classes
- Return JSON with `jsonify()` and appropriate status codes
- Add docstrings on all route handlers

---

## 3. Extensions and Models

Extensions are module-level singletons connected to the app later. Flask-SQLAlchemy 3.1
takes a SQLAlchemy 2.0 `DeclarativeBase`, so models use `Mapped[]` annotations.

```python
# src/app/extensions.py
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base shared by all models."""


db = SQLAlchemy(model_class=Base)
migrate = Migrate()
cors = CORS()
```

```python
# src/app/models/project.py
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Project(db.Model):
    """A project owned by a user."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped["User"] = relationship(back_populates="projects")

    def __repr__(self) -> str:
        return f"<Project {self.id} {self.name!r}>"
```

### Extension and Model Rules

- Define all extensions in a single `extensions.py` module
- Instantiate without app: `db = SQLAlchemy(model_class=Base)`
- Connect in factory: `db.init_app(app)`
- Models inherit `db.Model` and use `Mapped[]` / `mapped_column()` (never legacy `db.Column`)
- Quote related model names (`Mapped["User"]`) — they live in other modules
- Query with `db.session.execute(select(...))`, never the legacy `Model.query`

---

## 4. Configuration Pattern

Class-based configuration; secrets and the database URL come from the environment.
Database URLs use the sync drivers: `postgresql+psycopg://...` (psycopg 3),
`mysql+pymysql://...` or `sqlite:///...`.

```python
# src/app/config.py
import os


class Config:
    """Base configuration. Production reads everything from the environment."""

    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}


class DevelopmentConfig(Config):
    """Local development."""

    DEBUG = True
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-not-secret")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///dev.db")


class TestingConfig(Config):
    """Test runs."""

    TESTING = True
    SECRET_KEY = "test-only"
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite://")


class ProductionConfig(Config):
    """Production: SECRET_KEY and DATABASE_URL must be set (create_app checks)."""


CONFIGS: dict[str, type[Config]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
```

### Configuration Rules

- Use class inheritance for environment-specific config, selected via `CONFIGS`
- Read secrets from environment variables; no insecure fallback outside dev/test
- Never read `os.environ["X"]` at class level (it fails on import in every environment)
- Never hardcode credentials

---

## 5. Request Handling Pattern

```python
from flask import Response, jsonify, request

from app.schemas.resource import ResourceCreate, ResourceRead
from app.services.resource_service import ResourceService

TRUE_VALUES = {"1", "true", "yes", "on"}


def parse_bool(value: str) -> bool:
    """Parse a query-string flag: "true"/"1"/"yes"/"on" -> True, anything else False."""
    return value.strip().lower() in TRUE_VALUES


@bp.post("/")
def create_resource() -> tuple[Response, int]:
    """Create a resource with validated input."""
    # Parse and validate JSON body (ValidationError -> 422 via the global handler)
    data = ResourceCreate.model_validate(request.get_json())

    # Parse query parameters. NOT type=bool: bool("false") is True.
    include_details = request.args.get("details", default=False, type=parse_bool)

    # Parse headers
    api_key = request.headers.get("X-API-Key")

    # Business logic via service (sync, uses db.session)
    resource = ResourceService().create(data, include_details=include_details)

    return jsonify(ResourceRead.model_validate(resource).model_dump(mode="json")), 201
```

---

## 6. Testing Pattern

```python
# tests/conftest.py
from collections.abc import Iterator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from app.extensions import db


@pytest.fixture
def app() -> Iterator[Flask]:
    """Create the application with a fresh schema for each test."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create test client."""
    return app.test_client()
```

```python
# tests/blueprints/test_projects.py
from flask.testing import FlaskClient


class TestProjectBlueprint:
    """Tests for the projects blueprint."""

    def test_health(self, client: FlaskClient) -> None:
        assert client.get("/health").status_code == 200

    def test_list_projects(self, client: FlaskClient) -> None:
        response = client.get("/api/projects/")
        assert response.status_code == 200
        assert isinstance(response.get_json(), list)

    def test_create_project(self, client: FlaskClient) -> None:
        response = client.post("/api/projects/", json={"name": "Test Project"})
        assert response.status_code == 201
        assert response.get_json()["name"] == "Test Project"

    def test_get_project_not_found(self, client: FlaskClient) -> None:
        response = client.get("/api/projects/99999")
        assert response.status_code == 404
```

### Testing Rules

- Tests are sync `def` functions (no pytest-asyncio needed)
- Use `create_app("testing")` and `app.test_client()` for HTTP testing
- Run DB work inside `app.app_context()`
- Test happy paths and error cases
- Isolate tests with per-function database state
