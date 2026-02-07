# FastAPI Structured Logging Patterns

Structured logging patterns for FastAPI applications.

---

## 1. Structlog Setup

### Installation

```bash
pip install structlog python-json-logger
```

### Configuration

```python
# app/core/logging.py
"""Structured logging configuration."""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from app.core.config import settings


def setup_logging() -> None:
    """Configure structured logging."""

    # Shared processors for all environments
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.DEBUG:
        # Development: pretty console output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # Production: JSON output
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
    )

    # Quiet noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger."""
    return structlog.get_logger(name)
```

---

## 2. Request Logging Middleware

```python
# app/middleware/logging.py
"""Request logging middleware."""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

if TYPE_CHECKING:
    from collections.abc import Callable

logger = structlog.get_logger("http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Bind request context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
        )

        start_time = time.perf_counter()

        logger.info(
            "Request started",
            query_params=dict(request.query_params),
            user_agent=request.headers.get("User-Agent"),
        )

        try:
            response = await call_next(request)

            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "Request completed",
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )

            # Add request ID to response
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.exception(
                "Request failed",
                duration_ms=round(duration_ms, 2),
                error=str(exc),
            )

            raise


# app/main.py
from app.middleware.logging import RequestLoggingMiddleware

app = FastAPI()
app.add_middleware(RequestLoggingMiddleware)
```

---

## 3. Context Variables

```python
# app/core/context.py
"""Request context management."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

import structlog

# Context variables
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def get_request_id() -> str | None:
    """Get current request ID."""
    return request_id_var.get()


def set_request_id(request_id: str) -> None:
    """Set current request ID."""
    request_id_var.set(request_id)
    structlog.contextvars.bind_contextvars(request_id=request_id)


def set_user_context(user_id: str, **extra: Any) -> None:
    """Set user context for logging."""
    user_id_var.set(user_id)
    structlog.contextvars.bind_contextvars(user_id=user_id, **extra)


def clear_context() -> None:
    """Clear all context variables."""
    request_id_var.set(None)
    user_id_var.set(None)
    correlation_id_var.set(None)
    structlog.contextvars.clear_contextvars()
```

---

## 4. Service Logging

```python
# app/services/base.py
"""Base service with logging."""

from __future__ import annotations

import functools
import time
from typing import Any, Callable, TypeVar

import structlog

F = TypeVar("F", bound=Callable[..., Any])


class LoggedService:
    """Base class for services with logging."""

    def __init__(self) -> None:
        self.logger = structlog.get_logger(self.__class__.__name__)

    def log_operation(
        self,
        operation: str,
        **context: Any,
    ) -> None:
        """Log a service operation."""
        self.logger.info(f"{operation}", **context)


def log_method(operation: str | None = None) -> Callable[[F], F]:
    """Decorator for logging method execution."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            logger = structlog.get_logger(self.__class__.__name__)
            op_name = operation or func.__name__

            start_time = time.perf_counter()
            logger.info(f"{op_name} started")

            try:
                result = await func(self, *args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.info(f"{op_name} completed", duration_ms=round(duration_ms, 2))
                return result
            except Exception as exc:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.exception(
                    f"{op_name} failed",
                    duration_ms=round(duration_ms, 2),
                    error=str(exc),
                )
                raise

        return wrapper  # type: ignore

    return decorator


# Usage
class OrderService(LoggedService):
    @log_method("create_order")
    async def create(self, data: OrderCreate) -> Order:
        self.logger.info("Creating order", user_id=data.user_id, items=len(data.items))
        # Implementation
        return order
```

---

## 5. Database Query Logging

```python
# app/core/database.py
"""Database logging configuration."""

from __future__ import annotations

import logging
import time

import structlog
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = structlog.get_logger("database")


def setup_query_logging(engine: Engine, slow_query_threshold_ms: float = 100) -> None:
    """Setup database query logging."""

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault("query_start_time", []).append(time.perf_counter())

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        start_time = conn.info["query_start_time"].pop()
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log slow queries
        if duration_ms > slow_query_threshold_ms:
            logger.warning(
                "Slow query detected",
                query=statement[:500],  # Truncate long queries
                duration_ms=round(duration_ms, 2),
                parameters=str(parameters)[:200],
            )
        elif logging.getLogger().isEnabledFor(logging.DEBUG):
            logger.debug(
                "Query executed",
                query=statement[:200],
                duration_ms=round(duration_ms, 2),
            )
```

---

## 6. Background Task Logging

```python
# app/tasks/base.py
"""Background task logging."""

from __future__ import annotations

import functools
import time
import uuid
from typing import Any, Callable, TypeVar

import structlog

F = TypeVar("F", bound=Callable[..., Any])

logger = structlog.get_logger("tasks")


def log_task(task_name: str | None = None) -> Callable[[F], F]:
    """Decorator for logging background tasks."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            name = task_name or func.__name__
            task_id = str(uuid.uuid4())[:8]

            # Bind task context
            structlog.contextvars.clear_contextvars()
            structlog.contextvars.bind_contextvars(
                task_name=name,
                task_id=task_id,
            )

            start_time = time.perf_counter()
            logger.info("Task started", args=str(args)[:200], kwargs=str(kwargs)[:200])

            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.info("Task completed", duration_ms=round(duration_ms, 2))
                return result
            except Exception as exc:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.exception(
                    "Task failed",
                    duration_ms=round(duration_ms, 2),
                    error=str(exc),
                )
                raise
            finally:
                structlog.contextvars.clear_contextvars()

        return wrapper  # type: ignore

    return decorator


# Usage with ARQ or Celery
@log_task("send_welcome_email")
async def send_welcome_email(user_id: str) -> None:
    # Implementation
    pass
```

---

## 7. External Service Logging

```python
# app/services/http_client.py
"""HTTP client with logging."""

from __future__ import annotations

import time
from typing import Any

import httpx
import structlog

logger = structlog.get_logger("http_client")


class LoggingHTTPClient:
    """HTTP client with request/response logging."""

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.client = httpx.AsyncClient(base_url=base_url, timeout=timeout)
        self.base_url = base_url

    async def request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an HTTP request with logging."""
        start_time = time.perf_counter()

        logger.info(
            "External request started",
            service=self.base_url,
            method=method,
            path=path,
        )

        try:
            response = await self.client.request(method, path, **kwargs)
            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "External request completed",
                service=self.base_url,
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )

            return response

        except httpx.RequestError as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.error(
                "External request failed",
                service=self.base_url,
                method=method,
                path=path,
                error=str(exc),
                duration_ms=round(duration_ms, 2),
            )

            raise

    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self.request("POST", path, **kwargs)

    async def close(self) -> None:
        await self.client.aclose()
```

---

## 8. Log Filtering

```python
# app/core/logging.py
"""Log filtering for sensitive data."""

from __future__ import annotations

import re
from typing import Any

import structlog


SENSITIVE_PATTERNS = [
    (re.compile(r'password["\']?\s*[:=]\s*["\']?[^"\'}\s]+', re.I), 'password=***'),
    (re.compile(r'token["\']?\s*[:=]\s*["\']?[^"\'}\s]+', re.I), 'token=***'),
    (re.compile(r'authorization["\']?\s*[:=]\s*["\']?[^"\'}\s]+', re.I), 'authorization=***'),
    (re.compile(r'\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}'), '****-****-****-****'),  # Credit card
]


def filter_sensitive_data(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Filter sensitive data from log events."""

    def filter_value(value: Any) -> Any:
        if isinstance(value, str):
            for pattern, replacement in SENSITIVE_PATTERNS:
                value = pattern.sub(replacement, value)
        elif isinstance(value, dict):
            value = {k: filter_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            value = [filter_value(v) for v in value]
        return value

    return {k: filter_value(v) for k, v in event_dict.items()}


# Add to processors
structlog.configure(
    processors=[
        # ... other processors
        filter_sensitive_data,
        structlog.processors.JSONRenderer(),
    ],
)
```

---

## 9. Health Check Logging

```python
# app/api/health.py
"""Health check with logging."""

from __future__ import annotations

import structlog
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.database import engine
from app.core.cache import redis

logger = structlog.get_logger("health")

router = APIRouter(tags=["health"])


class HealthCheck(BaseModel):
    status: str
    checks: dict[str, dict[str, str]]


@router.get("/health")
async def health_check() -> HealthCheck:
    """Check health of all services."""
    checks = {}

    # Database check
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        checks["database"] = {"status": "unhealthy", "error": str(e)}

    # Redis check
    try:
        await redis.ping()
        checks["redis"] = {"status": "healthy"}
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        checks["redis"] = {"status": "unhealthy", "error": str(e)}

    # Determine overall status
    all_healthy = all(c["status"] == "healthy" for c in checks.values())
    status = "healthy" if all_healthy else "degraded"

    if not all_healthy:
        logger.warning("Health check degraded", checks=checks)

    return HealthCheck(status=status, checks=checks)
```

---

## 10. Log Aggregation

```python
# app/core/logging.py
"""Log aggregation configuration."""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog


def configure_for_cloud() -> None:
    """Configure logging for cloud environments (GCP, AWS, etc.)."""

    # JSON format for cloud log aggregation
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            add_cloud_context,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def add_cloud_context(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Add cloud-specific context for log aggregation."""
    import os

    # GCP Cloud Run context
    event_dict["service"] = os.getenv("K_SERVICE", "unknown")
    event_dict["revision"] = os.getenv("K_REVISION", "unknown")

    # Map log levels to GCP severity
    level_to_severity = {
        "debug": "DEBUG",
        "info": "INFO",
        "warning": "WARNING",
        "error": "ERROR",
        "critical": "CRITICAL",
    }

    event_dict["severity"] = level_to_severity.get(
        event_dict.get("level", "info"),
        "DEFAULT",
    )

    return event_dict
```
