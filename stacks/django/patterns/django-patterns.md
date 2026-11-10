# Django Code Patterns

Reference patterns for Django web application development. Agents should read this file
before writing code to ensure consistency across the codebase. The service layer,
querysets and transactions are in `patterns/backend-patterns.md`.

### Project Layout (one layout, everywhere)

```
manage.py
pyproject.toml          # deps, ruff, mypy, pytest (DJANGO_SETTINGS_MODULE)
config/                 # project package: settings.py, urls.py, wsgi.py, asgi.py, views.py
<app>/                  # each Django app at the project root (projects/, users/, ...)
    models.py  serializers.py  views.py  urls.py  admin.py
    services/           # business logic (see backend-patterns.md)
    migrations/
    tests/              # __init__.py, test_models.py, test_views.py, test_services.py ...
conftest.py             # shared pytest fixtures (api_client, user, ...)
```

Apps live at the project root as `<app>/` (never `src/<app>/`); tests live in
`<app>/tests/` (never a top-level `tests/<app>/`).

---

## 1. Model Pattern

```python
# projects/models.py
from django.conf import settings
from django.db import models


class Project(models.Model):
    """A project with owner and status tracking."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.name
```

### Model Rules

- Define `Meta` class with `ordering` and `indexes`
- Add `__str__` for admin display
- Reference users with `settings.AUTH_USER_MODEL` in FKs (never `"auth.User"` or `User`);
  in other code call `get_user_model()`
- Use `related_name` on all ForeignKey fields
- Add `created_at` and `updated_at` timestamps
- Use `models.Index` for frequently queried field combinations

---

## 2. Serializer Pattern

```python
# projects/serializers.py
from typing import Any

from rest_framework import serializers

from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project read operations."""

    class Meta:
        model = Project
        fields = [
            "id", "name", "description", "owner",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a Project."""

    class Meta:
        model = Project
        fields = ["name", "description"]

    def create(self, validated_data: dict[str, Any]) -> Project:
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)
```

### Serializer Rules

- Separate read and create serializers when needed
- Use `read_only_fields` for computed/auto fields
- Set owner/user in `create()` from request context
- Explicit `fields` list (never `__all__`)

---

## 3. ViewSet Pattern

```python
# projects/views.py
from django.db.models import QuerySet
from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Project
from .serializers import ProjectCreateSerializer, ProjectSerializer
from .services.project_archive import ProjectArchiveService


class ProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for Project CRUD operations."""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Project]:
        return Project.objects.filter(owner=self.request.user).select_related("owner")

    def get_serializer_class(self) -> type[serializers.BaseSerializer]:
        if self.action == "create":
            return ProjectCreateSerializer
        return ProjectSerializer

    @action(detail=True, methods=["post"])
    def archive(self, request: Request, pk: str | None = None) -> Response:
        """Archive a project (business logic lives in the service)."""
        project = ProjectArchiveService().execute(self.get_object())
        return Response(ProjectSerializer(project).data)
```

### ViewSet Rules

- Use `ModelViewSet` for full CRUD
- Override `get_queryset()` to scope by user
- Use `select_related()` / `prefetch_related()` in querysets
- Use `@action` decorator for custom endpoints; delegate multi-step logic to a service
- Views are sync by default (no `async def` views unless the whole path is async)
- Set `permission_classes` at class level

---

## 4. URL Configuration Pattern

```python
# projects/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProjectViewSet

router = DefaultRouter()
router.register("projects", ProjectViewSet, basename="project")

urlpatterns = [
    path("", include(router.urls)),
]
```

```python
# config/views.py
from django.http import HttpRequest, JsonResponse


def health(request: HttpRequest) -> JsonResponse:
    """Liveness check used by the dev server verification (no auth, no DB)."""
    return JsonResponse({"status": "ok"})
```

```python
# config/urls.py
from django.contrib import admin
from django.urls import include, path

from config.views import health

urlpatterns = [
    path("health", health, name="health"),
    path("admin/", admin.site.urls),
    path("api/", include("projects.urls")),
]
```

### URL Rules

- Use DRF routers for ViewSets
- Set explicit `basename` on router registrations
- Use `include()` for app-level URL grouping
- Keep URL config in each app's `urls.py`; include it from `config/urls.py`
- Keep the unauthenticated `/health` route in `config/urls.py`

---

## 5. Settings Pattern

Secrets come from the environment and there is **no insecure fallback**: a missing
`DJANGO_SECRET_KEY` fails at startup, and `DEBUG` is off unless explicitly enabled.
Local development sets both in an untracked `.env` (loaded by your shell, `direnv` or
`uv run --env-file .env`).

```python
# config/settings.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]  # KeyError at startup when unset
DEBUG = os.environ.get("DJANGO_DEBUG") == "1"  # off unless explicitly "1"
ALLOWED_HOSTS = [
    h for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h
]

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.environ.get("DB_NAME", "app"),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", ""),
        "CONN_MAX_AGE": 60,
    }
}

ROOT_URLCONF = "config.urls"
AUTH_USER_MODEL = "users.User"  # set before the first migration
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    # Local
    "projects",
    "users",
]

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}
```

---

## 6. Admin Pattern

```python
from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["owner"]
```

---

## 7. Testing Pattern

pytest-django needs the settings module. Configure it once in `pyproject.toml`
(tests also need a `DJANGO_SECRET_KEY`; set it in CI and your `.env`, or use a
dedicated `config/settings_test.py` that sets one):

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
python_files = ["test_*.py"]
addopts = "-v --tb=short --reuse-db"
```

```python
# conftest.py (project root)
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username="test", password="testpass")


@pytest.fixture
def auth_client(api_client: APIClient, user) -> APIClient:
    api_client.force_authenticate(user=user)
    return api_client
```

```python
# projects/tests/test_views.py
import pytest

from projects.models import Project

pytestmark = pytest.mark.django_db


class TestProjectViewSet:
    def test_list_projects(self, auth_client, user) -> None:
        Project.objects.create(name="Test", owner=user)
        response = auth_client.get("/api/projects/")
        assert response.status_code == 200
        assert len(response.data["results"]) == 1

    def test_create_project(self, auth_client) -> None:
        response = auth_client.post("/api/projects/", {"name": "New Project"})
        assert response.status_code == 201
        assert response.data["name"] == "New Project"

    def test_unauthenticated_is_rejected(self, api_client) -> None:
        response = api_client.get("/api/projects/")
        # 401 with token/JWT auth, 403 with DRF's default session auth
        assert response.status_code in (401, 403)

    def test_health(self, api_client) -> None:
        assert api_client.get("/health").status_code == 200
```

---

## 8. Middleware Pattern

```python
import time
import logging

logger = logging.getLogger(__name__)


class RequestTimingMiddleware:
    """Log request timing for performance monitoring."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration = (time.monotonic() - start) * 1000

        logger.info(
            "%s %s %s %.2fms",
            request.method,
            request.path,
            response.status_code,
            duration,
        )
        return response
```

---

## 9. Signal Pattern

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Project


@receiver(post_save, sender=Project)
def project_post_save(sender, instance, created, **kwargs):
    """Handle project creation side effects."""
    if created:
        # Send notification, create related objects, etc.
        pass
```
