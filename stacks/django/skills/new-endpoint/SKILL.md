---
name: new-endpoint
description: Add one DRF endpoint (ViewSet action or APIView) end to end, documented with drf-spectacular extend_schema
---

# /new-endpoint

## What This Does

Adds a single endpoint (a custom ViewSet `@action` or an `APIView`) with its
request/response serializers, permissions, URL, OpenAPI docs via
drf-spectacular's `extend_schema`, and tests. For a full CRUD resource use
`/new-view`.

## Usage

```
/new-endpoint projects "POST /projects/{id}/archive"
/new-endpoint reports "GET /reports/revenue?from=&to="
```

## How It Works

1. **Read** `.claude/patterns/django-patterns.md`, `.claude/patterns/permissions.md`
   and the app's `views.py`, `serializers.py`, `urls.py`.

2. **drf-spectacular present?** If not, add the dep and wire it once:

   ```python
   # config/settings.py
   INSTALLED_APPS += ["drf_spectacular"]
   REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"] = "drf_spectacular.openapi.AutoSchema"
   SPECTACULAR_SETTINGS = {"TITLE": "API", "VERSION": "1.0.0", "SERVE_INCLUDE_SCHEMA": False}

   # config/urls.py
   from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

   urlpatterns += [
       path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
       path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
   ]
   ```

3. **Serializers** for the input and the output (separate classes when they
   differ). Query params get a serializer too.

4. **The view.** Thin: validate, call a service, serialize. Document it:

   ```python
   from drf_spectacular.utils import OpenApiResponse, extend_schema
   from rest_framework import status
   from rest_framework.decorators import action
   from rest_framework.response import Response


   class ProjectViewSet(viewsets.ModelViewSet):
       ...

       @extend_schema(
           summary="Archive a project",
           request=ProjectArchiveSerializer,
           responses={
               200: ProjectSerializer,
               400: OpenApiResponse(description="Project already archived"),
               404: OpenApiResponse(description="Not found or not yours"),
           },
           tags=["projects"],
       )
       @action(detail=True, methods=["post"])
       def archive(self, request, pk=None):
           project = self.get_object()  # runs object permissions
           payload = ProjectArchiveSerializer(data=request.data)
           payload.is_valid(raise_exception=True)
           project = ProjectArchiveService().archive(project, **payload.validated_data)
           return Response(ProjectSerializer(project).data, status=status.HTTP_200_OK)
   ```

   - Query params: `parameters=[ReportQuerySerializer]` (or `OpenApiParameter`).
   - `APIView`/`GenericAPIView` without a `serializer_class` always needs
     `extend_schema`, or the schema has no body.
   - Different permissions than the ViewSet: `@action(..., permission_classes=[...])`.

5. **URL.** ViewSet actions are routed by the router; an `APIView` gets a
   `path()` in `<app>/urls.py` with a `name`.

6. **Tests** in `<app>/tests/test_views.py`: success, validation error (400),
   anonymous (401/403), another user's object (404), and the query count
   (`django_assert_num_queries`).

7. **Check the schema** has no warnings and run quality gates:

   ```bash
   uv run python manage.py spectacular --validate --fail-on-warn --file /dev/null
   uv run ruff format . && uv run ruff check . && uv run mypy . && uv run pytest <app>/tests/ -v
   ```

## Generated Files

```
<app>/views.py         (action or APIView)
<app>/serializers.py   (request/response serializers)
<app>/urls.py          (APIView only)
<app>/services/...     (logic)
<app>/tests/test_views.py
```
