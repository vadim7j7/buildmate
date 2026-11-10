# Django REST Framework: Authentication and Permissions

Read when adding an endpoint that is not public, changing who can see or edit
something, or setting up auth.

## Defaults: Deny, Then Open Up

```python
# config/settings.py
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # Pick per client type, see below
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}
```

Every view is authenticated unless it says otherwise. A public endpoint sets
`permission_classes = [AllowAny]` explicitly (and usually a throttle).

## Session or JWT

| Client | Use |
|--------|-----|
| SPA on the same site (same registrable domain) | `SessionAuthentication`: HttpOnly cookie, CSRF token on unsafe methods |
| Mobile app, third-party or cross-site client | `djangorestframework-simplejwt` (add the dep) |
| Server-to-server | A scoped API key / token model, not a user's JWT |

simplejwt setup:

```python
# config/settings.py
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,  # needs "rest_framework_simplejwt.token_blacklist" app
}

# config/urls.py
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns += [
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
```

Unauthenticated requests get **401** with JWT (it sends `WWW-Authenticate`) and
**403** with session-only auth; tests assert what the project's first
authentication class gives.

## Permission Classes

```python
# projects/permissions.py
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """Anyone authenticated may read; only the owner may change."""

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return obj.owner_id == request.user.id


class IsProjectMember(BasePermission):
    """The user belongs to the project in the URL (nested routes)."""

    def has_permission(self, request, view) -> bool:
        return request.user.memberships.filter(
            project_id=view.kwargs["project_pk"]
        ).exists()
```

Combine with `&`, `|`, `~`: `permission_classes = [IsAuthenticated & (IsOwner | IsAdminUser)]`.

## Object-Level Checks: the Two Traps

1. **`has_object_permission` runs only when the view calls `get_object()`**
   (retrieve, update, destroy). It never runs for `list` or for custom actions
   that query the model themselves. Scope the queryset instead:

   ```python
   class ProjectViewSet(viewsets.ModelViewSet):
       permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
       serializer_class = ProjectSerializer

       def get_queryset(self):
           # Users only ever see their own projects: list AND detail are safe,
           # and another user's id returns 404 (no existence leak), not 403
           return Project.objects.filter(owner=self.request.user)
   ```

2. **Foreign keys in the request body are not checked by permissions.** A user
   can `POST {"project": <someone else's id>}`. Restrict the field's queryset:

   ```python
   class TaskSerializer(serializers.ModelSerializer):
       project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.none())

       def __init__(self, *args, **kwargs):
           super().__init__(*args, **kwargs)
           request = self.context.get("request")
           if request:
               self.fields["project"].queryset = Project.objects.filter(owner=request.user)
   ```

Also: set `owner` from `request.user` in `perform_create` (read-only on the
serializer), never from the body.

## Per-Action Permissions

```python
def get_permissions(self):
    if self.action in ("list", "retrieve"):
        return [AllowAny()]
    if self.action == "destroy":
        return [IsAdminUser()]
    return super().get_permissions()
```

## Django Model Permissions and Groups

For staff/back-office roles use Django's permissions (`user.has_perm("projects.change_project")`,
`DjangoModelPermissions`) and groups, rather than ad-hoc `is_manager` booleans.
Custom ones go in `Meta.permissions` (they get a migration).

## Throttling Public and Auth Endpoints

```python
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {"anon": "60/min", "user": "600/min", "login": "5/min"}
```

Token/login views get a `ScopedRateThrottle` (`throttle_scope = "login"`). DRF
throttles use the cache: configure a shared cache (Redis) in production.

## Test Every Permission Path

For each protected endpoint: anonymous (401/403), authenticated non-owner (404
when the queryset is scoped, 403 otherwise), owner (2xx), and a write with a
foreign key the user does not own (400).
