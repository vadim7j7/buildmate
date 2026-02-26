# Django Code Patterns

Reference patterns for Django web application development. Agents should read this file
before writing code to ensure consistency across the codebase.

---

## 1. Model Pattern

```python
from __future__ import annotations

from django.db import models


class Project(models.Model):
    """A project with owner and status tracking."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    owner = models.ForeignKey(
        "auth.User",
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

- Use `from __future__ import annotations` at the top
- Define `Meta` class with `ordering` and `indexes`
- Add `__str__` for admin display
- Use `related_name` on all ForeignKey fields
- Add `created_at` and `updated_at` timestamps
- Use `models.Index` for frequently queried field combinations

---

## 2. Serializer Pattern

```python
from __future__ import annotations

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

    def create(self, validated_data: dict) -> Project:
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
from __future__ import annotations

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Project
from .serializers import ProjectSerializer, ProjectCreateSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for Project CRUD operations."""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(
            owner=self.request.user,
        ).select_related("owner")

    def get_serializer_class(self):
        if self.action == "create":
            return ProjectCreateSerializer
        return ProjectSerializer

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        """Archive a project."""
        project = self.get_object()
        project.is_active = False
        project.save(update_fields=["is_active", "updated_at"])
        return Response(ProjectSerializer(project).data)
```

### ViewSet Rules

- Use `ModelViewSet` for full CRUD
- Override `get_queryset()` to scope by user
- Use `select_related()` / `prefetch_related()` in querysets
- Use `@action` decorator for custom endpoints
- Set `permission_classes` at class level

---

## 4. URL Configuration Pattern

```python
from __future__ import annotations

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProjectViewSet

router = DefaultRouter()
router.register("projects", ProjectViewSet, basename="project")

urlpatterns = [
    path("", include(router.urls)),
]
```

### URL Rules

- Use DRF routers for ViewSets
- Set explicit `basename` on router registrations
- Use `include()` for app-level URL grouping
- Keep URL config in each app's `urls.py`

---

## 5. Settings Pattern

```python
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-key")
DEBUG = os.environ.get("DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

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
from __future__ import annotations

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

```python
from __future__ import annotations

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from projects.models import Project


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="test", password="testpass")


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


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

    def test_unauthenticated_returns_401(self, api_client) -> None:
        response = api_client.get("/api/projects/")
        assert response.status_code == 401
```

---

## 8. Middleware Pattern

```python
from __future__ import annotations

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
from __future__ import annotations

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
