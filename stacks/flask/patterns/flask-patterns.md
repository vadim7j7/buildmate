# Flask Code Patterns

Reference patterns for Flask web application development. Agents should read this file
before writing code to ensure consistency across the codebase.

---

## 1. App Factory Pattern

All Flask applications use the factory pattern for testability and flexibility.

```python
from __future__ import annotations

from flask import Flask

from app.extensions import db, migrate, cors


def create_app(config_name: str = "default") -> Flask:
    """Create and configure the Flask application.

    Args:
        config_name: Configuration class name to load.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(f"app.config.{config_name}")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
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
    from pydantic import ValidationError

    @app.errorhandler(ValidationError)
    def validation_error(error: ValidationError):
        return {"errors": error.errors()}, 422

    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not found"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {"error": "Internal server error"}, 500
```

### App Factory Rules

- Always use `create_app()` — never instantiate `Flask()` at module level
- Initialize extensions with `ext.init_app(app)`, not in constructors
- Register blueprints in a dedicated function
- Register error handlers globally
- Load config from class-based config objects

---

## 2. Blueprint Pattern

Blueprints organize routes by resource. Each blueprint lives in its own module.

```python
from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.project_service import ProjectService

bp = Blueprint("projects", __name__)


@bp.get("/")
async def list_projects():
    """List all projects with pagination."""
    skip = request.args.get("skip", 0, type=int)
    limit = request.args.get("limit", 20, type=int)
    async with db.session() as session:
        service = ProjectService(session)
        projects = await service.list(skip=skip, limit=limit)
    return jsonify([ProjectRead.model_validate(p).model_dump() for p in projects])


@bp.post("/")
async def create_project():
    """Create a new project."""
    data = ProjectCreate.model_validate(request.get_json())
    async with db.session() as session:
        service = ProjectService(session)
        project = await service.create(data)
    return jsonify(ProjectRead.model_validate(project).model_dump()), 201


@bp.get("/<int:project_id>")
async def get_project(project_id: int):
    """Get a single project by ID."""
    async with db.session() as session:
        service = ProjectService(session)
        project = await service.get_by_id(project_id)
    if project is None:
        return {"error": "Project not found"}, 404
    return jsonify(ProjectRead.model_validate(project).model_dump())


@bp.patch("/<int:project_id>")
async def update_project(project_id: int):
    """Update a project by ID (partial update)."""
    data = ProjectUpdate.model_validate(request.get_json())
    async with db.session() as session:
        service = ProjectService(session)
        project = await service.update(project_id, data)
    if project is None:
        return {"error": "Project not found"}, 404
    return jsonify(ProjectRead.model_validate(project).model_dump())


@bp.delete("/<int:project_id>")
async def delete_project(project_id: int):
    """Delete a project by ID."""
    async with db.session() as session:
        service = ProjectService(session)
        deleted = await service.delete(project_id)
    if not deleted:
        return {"error": "Project not found"}, 404
    return "", 204
```

### Blueprint Rules

- Use `Blueprint("name", __name__)` — name matches the resource
- Use decorator shortcuts: `@bp.get()`, `@bp.post()`, `@bp.patch()`, `@bp.delete()`
- Parse query params with `request.args.get(key, default, type=int)`
- Parse JSON body with `request.get_json()`
- Validate input with Pydantic schemas
- Delegate business logic to service classes
- Return JSON with `jsonify()` and appropriate status codes
- Add docstrings on all route handlers

---

## 3. Extensions Pattern

Extensions are initialized as module-level singletons and connected to the app later.

```python
from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
```

### Extension Rules

- Define all extensions in a single `extensions.py` module
- Instantiate without app: `db = SQLAlchemy()`
- Connect in factory: `db.init_app(app)`
- Import from `app.extensions` everywhere else

---

## 4. Configuration Pattern

Use class-based configuration with environment variable overrides.

```python
from __future__ import annotations

import os


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///dev.db"
    )


class ProductionConfig(Config):
    """Production configuration."""

    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
```

### Configuration Rules

- Use class inheritance for environment-specific config
- Read secrets from environment variables
- Never hardcode credentials
- Use `app.config.from_object()` in the factory

---

## 5. Request Handling Pattern

```python
from __future__ import annotations

from flask import request
from pydantic import ValidationError


@bp.post("/")
async def create_resource():
    """Create a resource with validated input."""
    # Parse and validate JSON body
    try:
        data = ResourceCreate.model_validate(request.get_json())
    except ValidationError as e:
        return {"errors": e.errors()}, 422

    # Parse query parameters
    include_details = request.args.get("details", False, type=bool)

    # Parse headers
    api_key = request.headers.get("X-API-Key")

    # Business logic via service
    async with db.session() as session:
        service = ResourceService(session)
        resource = await service.create(data)

    return jsonify(ResourceRead.model_validate(resource).model_dump()), 201
```

---

## 6. Testing Pattern

```python
from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app("testing")
    yield app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create test client."""
    return app.test_client()


class TestProjectBlueprint:
    """Tests for the projects blueprint."""

    def test_list_projects(self, client: FlaskClient) -> None:
        response = client.get("/api/projects/")
        assert response.status_code == 200
        assert isinstance(response.get_json(), list)

    def test_create_project(self, client: FlaskClient) -> None:
        response = client.post(
            "/api/projects/",
            json={"name": "Test Project"},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == "Test Project"

    def test_get_project_not_found(self, client: FlaskClient) -> None:
        response = client.get("/api/projects/99999")
        assert response.status_code == 404
```

### Testing Rules

- Use `app.test_client()` for HTTP testing
- Use `create_app("testing")` with test config
- Test happy paths and error cases
- Use fixtures for app and client setup
- Isolate tests with per-function database state
