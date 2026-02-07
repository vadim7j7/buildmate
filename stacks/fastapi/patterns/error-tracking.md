# FastAPI Error Tracking Patterns

Error tracking patterns using Sentry for FastAPI applications.

---

## 1. Sentry Setup

### Installation

```bash
pip install sentry-sdk[fastapi]
```

### Configuration

```python
# app/core/sentry.py
"""Sentry configuration."""

from __future__ import annotations

import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration

from app.core.config import settings


def init_sentry() -> None:
    """Initialize Sentry SDK."""
    if not settings.SENTRY_DSN:
        return

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        release=settings.GIT_SHA,

        # Performance monitoring
        traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
        profiles_sample_rate=0.1,

        # Enable integrations
        integrations=[
            AsyncioIntegration(),
            SqlalchemyIntegration(),
            RedisIntegration(),
            HttpxIntegration(),
        ],

        # Filter events
        before_send=before_send,
        before_send_transaction=before_send_transaction,

        # Don't send PII by default
        send_default_pii=False,

        # Attach stack traces to messages
        attach_stacktrace=True,
    )


def before_send(event: dict, hint: dict) -> dict | None:
    """Filter events before sending to Sentry."""
    exception = hint.get("exc_info")

    if exception:
        exc_type = exception[0]

        # Don't report expected exceptions
        if exc_type.__name__ in ("HTTPException", "RequestValidationError"):
            return None

        # Don't report 404s
        if hasattr(exception[1], "status_code") and exception[1].status_code == 404:
            return None

    return event


def before_send_transaction(event: dict, hint: dict) -> dict | None:
    """Filter transactions before sending to Sentry."""
    # Don't track health checks
    if event.get("transaction") in ("/health", "/ready", "/metrics"):
        return None

    return event


# app/main.py
from app.core.sentry import init_sentry

init_sentry()

app = FastAPI()
```

---

## 2. Sentry Middleware

```python
# app/middleware/sentry.py
"""Sentry integration middleware."""

from __future__ import annotations

from typing import TYPE_CHECKING

import sentry_sdk
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

if TYPE_CHECKING:
    from collections.abc import Callable


class SentryContextMiddleware(BaseHTTPMiddleware):
    """Add request context to Sentry."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        # Set request context
        sentry_sdk.set_context("request", {
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "headers": dict(request.headers),
        })

        # Add user context if available
        if hasattr(request.state, "user") and request.state.user:
            sentry_sdk.set_user({
                "id": str(request.state.user.id),
                "email": request.state.user.email,
                "username": request.state.user.name,
            })

        # Add tags
        sentry_sdk.set_tag("path", request.url.path)
        sentry_sdk.set_tag("method", request.method)

        return await call_next(request)


# app/main.py
from app.middleware.sentry import SentryContextMiddleware

app.add_middleware(SentryContextMiddleware)
```

---

## 3. Custom Error Classes

```python
# app/core/errors.py
"""Custom error classes with Sentry integration."""

from __future__ import annotations

from typing import Any

import sentry_sdk
from fastapi import HTTPException


class AppError(Exception):
    """Base application error."""

    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
        report_to_sentry: bool = True,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        self.report_to_sentry = report_to_sentry
        super().__init__(message)

    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=self.status_code,
            detail={
                "code": self.code,
                "message": self.message,
                **self.details,
            },
        )

    def capture(self, **extra: Any) -> str | None:
        """Capture exception in Sentry."""
        if not self.report_to_sentry:
            return None

        with sentry_sdk.push_scope() as scope:
            scope.set_tag("error_code", self.code)
            scope.set_extra("details", self.details)
            for key, value in extra.items():
                scope.set_extra(key, value)
            return sentry_sdk.capture_exception(self)


class ValidationError(AppError):
    """Validation error."""

    def __init__(
        self,
        message: str,
        errors: dict[str, list[str]],
    ) -> None:
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details={"errors": errors},
            report_to_sentry=False,
        )


class NotFoundError(AppError):
    """Resource not found error."""

    def __init__(self, resource: str, identifier: Any) -> None:
        super().__init__(
            message=f"{resource} not found",
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "identifier": str(identifier)},
            report_to_sentry=False,
        )


class AuthenticationError(AppError):
    """Authentication error."""

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(
            message=message,
            code="UNAUTHENTICATED",
            status_code=401,
            report_to_sentry=False,
        )


class AuthorizationError(AppError):
    """Authorization error."""

    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
            report_to_sentry=False,
        )


class ExternalServiceError(AppError):
    """External service error."""

    def __init__(
        self,
        service: str,
        message: str,
        response: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={"service": service, "response": str(response)[:500]},
            report_to_sentry=True,
        )


class RateLimitError(AppError):
    """Rate limit exceeded error."""

    def __init__(self, limit: int, window: int) -> None:
        super().__init__(
            message="Rate limit exceeded",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"limit": limit, "window": window},
            report_to_sentry=False,
        )
```

---

## 4. Global Exception Handler

```python
# app/api/exception_handlers.py
"""Global exception handlers."""

from __future__ import annotations

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.core.errors import AppError
from app.core.config import settings


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """Handle application errors."""
        if exc.report_to_sentry:
            exc.capture(
                path=request.url.path,
                method=request.method,
            )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    **exc.details,
                }
            },
        )

    @app.exception_handler(PydanticValidationError)
    async def validation_error_handler(
        request: Request,
        exc: PydanticValidationError,
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request data",
                    "details": exc.errors(),
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Handle unhandled exceptions."""
        sentry_sdk.capture_exception(exc)

        message = str(exc) if settings.DEBUG else "An unexpected error occurred"

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": message,
                }
            },
        )


# app/main.py
from app.api.exception_handlers import register_exception_handlers

app = FastAPI()
register_exception_handlers(app)
```

---

## 5. User Context

```python
# app/dependencies/sentry.py
"""Sentry context dependencies."""

from __future__ import annotations

from typing import Annotated

import sentry_sdk
from fastapi import Depends

from app.dependencies.auth import get_current_user
from app.models.user import User


async def set_sentry_user(
    user: Annotated[User | None, Depends(get_current_user)],
) -> None:
    """Set Sentry user context."""
    if user:
        sentry_sdk.set_user({
            "id": str(user.id),
            "email": user.email,
            "username": user.name,
        })

        sentry_sdk.set_tag("user_plan", user.subscription_plan)
        sentry_sdk.set_tag("user_role", user.role)


# Usage in router
@router.get("/profile")
async def get_profile(
    user: CurrentUser,
    _: Annotated[None, Depends(set_sentry_user)],
) -> UserResponse:
    return user
```

---

## 6. Transaction Monitoring

```python
# app/services/transaction.py
"""Transaction monitoring with Sentry."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import sentry_sdk


@asynccontextmanager
async def track_transaction(
    name: str,
    op: str,
    **tags: str,
) -> AsyncGenerator[None, None]:
    """Context manager for tracking transactions."""
    with sentry_sdk.start_transaction(name=name, op=op) as transaction:
        for key, value in tags.items():
            transaction.set_tag(key, value)

        try:
            yield
            transaction.set_status("ok")
        except Exception:
            transaction.set_status("internal_error")
            raise


def track_span(
    op: str,
    description: str,
    **data: Any,
):
    """Decorator for tracking spans within a transaction."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            with sentry_sdk.start_span(op=op, description=description) as span:
                for key, value in data.items():
                    span.set_data(key, value)

                try:
                    result = await func(*args, **kwargs)
                    span.set_status("ok")
                    return result
                except Exception:
                    span.set_status("internal_error")
                    raise

        return wrapper

    return decorator


# Usage
class OrderService:
    async def create_order(self, data: OrderCreate) -> Order:
        async with track_transaction("create_order", "order", user_id=str(data.user_id)):
            order = await self._create_order(data)
            await self._process_payment(order)
            await self._send_confirmation(order)
            return order

    @track_span("db", "Create order record")
    async def _create_order(self, data: OrderCreate) -> Order:
        # Implementation
        pass

    @track_span("payment", "Process payment")
    async def _process_payment(self, order: Order) -> None:
        # Implementation
        pass

    @track_span("notification", "Send confirmation email")
    async def _send_confirmation(self, order: Order) -> None:
        # Implementation
        pass
```

---

## 7. Background Task Error Handling

```python
# app/tasks/base.py
"""Background task error handling."""

from __future__ import annotations

import functools
from typing import Any, Callable, TypeVar

import sentry_sdk
from arq import ArqRedis

F = TypeVar("F", bound=Callable[..., Any])


def sentry_task(task_name: str | None = None) -> Callable[[F], F]:
    """Decorator for background tasks with Sentry integration."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(ctx: dict, *args, **kwargs):
            name = task_name or func.__name__

            with sentry_sdk.start_transaction(name=name, op="task") as transaction:
                sentry_sdk.set_tag("task_name", name)
                sentry_sdk.set_context("task", {
                    "name": name,
                    "args": str(args)[:200],
                    "kwargs": str(kwargs)[:200],
                })

                try:
                    result = await func(ctx, *args, **kwargs)
                    transaction.set_status("ok")
                    return result
                except Exception as exc:
                    transaction.set_status("internal_error")
                    sentry_sdk.capture_exception(exc)
                    raise

        return wrapper  # type: ignore

    return decorator


# Usage
@sentry_task("send_welcome_email")
async def send_welcome_email(ctx: dict, user_id: str) -> None:
    # Implementation
    pass
```

---

## 8. Breadcrumbs

```python
# app/core/sentry_utils.py
"""Sentry utility functions."""

from __future__ import annotations

from typing import Any

import sentry_sdk


def add_breadcrumb(
    category: str,
    message: str,
    level: str = "info",
    data: dict[str, Any] | None = None,
) -> None:
    """Add a breadcrumb to the current Sentry scope."""
    sentry_sdk.add_breadcrumb(
        category=category,
        message=message,
        level=level,
        data=data,
    )


def capture_message(
    message: str,
    level: str = "info",
    **extra: Any,
) -> str | None:
    """Capture a message in Sentry."""
    with sentry_sdk.push_scope() as scope:
        for key, value in extra.items():
            scope.set_extra(key, value)
        return sentry_sdk.capture_message(message, level=level)


# Usage in services
class PaymentService:
    async def process_payment(self, order: Order) -> PaymentResult:
        add_breadcrumb(
            category="payment",
            message=f"Processing payment for order {order.id}",
            data={"amount": order.total, "currency": order.currency},
        )

        try:
            result = await self.gateway.charge(order)
            add_breadcrumb(
                category="payment",
                message="Payment successful",
                data={"transaction_id": result.transaction_id},
            )
            return result
        except PaymentError as e:
            add_breadcrumb(
                category="payment",
                message="Payment failed",
                level="error",
                data={"error": str(e)},
            )
            raise
```

---

## 9. Error Fingerprinting

```python
# app/core/sentry.py
"""Sentry error fingerprinting."""

from __future__ import annotations

import sentry_sdk

from app.core.errors import ExternalServiceError


def before_send(event: dict, hint: dict) -> dict | None:
    """Add custom fingerprinting."""
    exception = hint.get("exc_info")

    if exception:
        exc_instance = exception[1]

        # Group external service errors by service name
        if isinstance(exc_instance, ExternalServiceError):
            event["fingerprint"] = [
                "external-service",
                exc_instance.details.get("service", "unknown"),
            ]

        # Group database connection errors
        if "connection" in str(exc_instance).lower():
            event["fingerprint"] = ["database-connection-error"]

        # Group timeout errors
        if "timeout" in str(exc_instance).lower():
            event["fingerprint"] = ["timeout-error"]

    return event
```

---

## 10. Health Check Integration

```python
# app/api/health.py
"""Health check with Sentry integration."""

from __future__ import annotations

import sentry_sdk
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    checks: dict[str, dict[str, str]]


@router.get("/health")
async def health_check() -> HealthResponse:
    """Check health of all dependencies."""
    checks = {}

    # Check database
    try:
        await check_database()
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}

    # Check Redis
    try:
        await check_redis()
        checks["redis"] = {"status": "healthy"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}

    # Determine overall status
    all_healthy = all(c["status"] == "healthy" for c in checks.values())
    status = "healthy" if all_healthy else "degraded"

    # Report degraded status to Sentry
    if not all_healthy:
        sentry_sdk.capture_message(
            "Health check degraded",
            level="warning",
            extra={"checks": checks},
        )

    return HealthResponse(status=status, checks=checks)
```

---

## 11. Testing Sentry Integration

```python
# app/api/debug.py
"""Debug endpoints for testing Sentry."""

from __future__ import annotations

import sentry_sdk
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.core.errors import AppError

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/sentry-test")
async def test_sentry():
    """Test Sentry error capture."""
    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=403, detail="Not available in production")

    try:
        raise ValueError("Test Sentry error - please ignore")
    except ValueError as e:
        event_id = sentry_sdk.capture_exception(e)
        return {"message": "Test error sent to Sentry", "event_id": event_id}


@router.get("/sentry-message")
async def test_sentry_message():
    """Test Sentry message capture."""
    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=403, detail="Not available in production")

    event_id = sentry_sdk.capture_message("Test message from FastAPI")
    return {"message": "Test message sent to Sentry", "event_id": event_id}
```

---

## 12. Release Tracking

```python
# app/core/sentry.py
"""Sentry release tracking."""

from __future__ import annotations

import os

import sentry_sdk


def get_release_version() -> str:
    """Get release version from environment."""
    # Try various CI/CD environment variables
    return (
        os.getenv("GIT_SHA")
        or os.getenv("HEROKU_SLUG_COMMIT")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or os.getenv("RENDER_GIT_COMMIT")
        or "development"
    )


def init_sentry() -> None:
    """Initialize Sentry with release tracking."""
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        release=get_release_version(),
        environment=os.getenv("ENVIRONMENT", "development"),
        # ... other config
    )
```
