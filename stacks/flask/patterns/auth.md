# Flask Authentication

Read when adding login, protecting routes, or reading the current user.
Pick one mechanism per client type:

| Client | Use |
|--------|-----|
| Server-rendered pages, or an SPA on the same site | **Flask-Login** (session cookie) + CSRF protection |
| Mobile app, cross-site SPA, third-party API clients | **Flask-JWT-Extended** (Bearer tokens) |

Passwords: hash with `werkzeug.security.generate_password_hash` (scrypt by
default) or `argon2-cffi`; never store or log them in plain text.

## Session Auth: Flask-Login

```python
# src/app/extensions.py
from flask_login import LoginManager

login_manager = LoginManager()

# src/app/__init__.py (in create_app)
login_manager.init_app(app)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=not app.debug,
)
```

```python
# src/app/auth.py
from flask_login import UserMixin

from app.extensions import db, login_manager
from app.models.user import User  # User(db.Model, UserMixin)


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    return db.session.get(User, int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    from flask import abort

    abort(401)  # JSON API: 401 problem+json, not a redirect to a login page
```

```python
# src/app/blueprints/auth.py
from flask import Blueprint, abort, request
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from app.schemas.auth import LoginIn
from app.services.user_service import UserService

bp = Blueprint("auth", __name__)


@bp.post("/login")
def login() -> tuple[dict[str, object], int]:
    data = LoginIn.model_validate(request.get_json())
    user = UserService().get_by_email(data.email)
    if user is None or not check_password_hash(user.password_hash, data.password):
        abort(401, description="Invalid email or password")  # same message for both
    login_user(user, remember=data.remember)
    return {"id": user.id, "email": user.email}, 200


@bp.post("/logout")
@login_required
def logout() -> tuple[str, int]:
    logout_user()
    return "", 204
```

Protect routes with `@login_required` and read `current_user`. State-changing
requests from a browser need CSRF protection (Flask-WTF's `CSRFProtect`, with
the token sent in a header by the SPA).

## Token Auth: Flask-JWT-Extended

```python
# src/app/extensions.py
from flask_jwt_extended import JWTManager

jwt = JWTManager()

# config: JWT_SECRET_KEY from the environment,
# JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
```

```python
from flask_jwt_extended import (
    create_access_token, create_refresh_token, get_jwt_identity, jwt_required,
)


@bp.post("/token")
def token() -> tuple[dict[str, str], int]:
    user = authenticate(request.get_json())  # abort(401) on failure
    identity = str(user.id)                 # identity must be a string
    return {
        "access_token": create_access_token(identity=identity),
        "refresh_token": create_refresh_token(identity=identity),
    }, 200


@bp.post("/token/refresh")
@jwt_required(refresh=True)
def refresh() -> tuple[dict[str, str], int]:
    return {"access_token": create_access_token(identity=get_jwt_identity())}, 200


@projects_bp.get("/")
@jwt_required()
def list_projects():
    user_id = int(get_jwt_identity())
    ...
```

Revocation (logout, stolen token): a `@jwt.token_in_blocklist_loader` backed by
Redis or a table, keyed by the token's `jti`. Make the JWT error loaders
(`@jwt.unauthorized_loader`, `@jwt.invalid_token_loader`,
`@jwt.expired_token_loader`) return the same problem+json shape as other errors.

## Authorization

Authentication says who; authorization says what they may touch. Filter by
owner in the service (`select(Project).where(Project.owner_id == user_id)`) and
return 404 for other users' objects, so ids do not leak. Role checks go in a
small decorator (`@require_role("admin")`) next to the auth code.

## Tests

- A `logged_in_client` fixture: create a user, then `client.post("/api/auth/login", ...)`
  (session) or add `Authorization: Bearer <create_access_token(...)>` inside
  `app.app_context()` (JWT).
- For each protected route: anonymous 401, other user's object 404, owner 2xx.
- Rate-limit the login/token routes (Flask-Limiter) and test the limit.
