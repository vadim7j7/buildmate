# FastAPI Middleware Examples

Reference examples for generating ASGI middleware.

## BaseHTTPMiddleware: Timing

```python
"""Request timing middleware for performance monitoring."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

if TYPE_CHECKING:
    from collections.abc import Callable


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware that adds request timing headers."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Process the request and add timing header.

        Args:
            request: The incoming request.
            call_next: The next middleware or route handler.

        Returns:
            Response with X-Process-Time header.
        """
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        return response
```

## BaseHTTPMiddleware: Request ID

```python
"""Request ID middleware for request tracing."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

if TYPE_CHECKING:
    from collections.abc import Callable

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware that assigns a unique ID to each request."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Assign request ID and propagate to response.

        Args:
            request: The incoming request.
            call_next: The next middleware or route handler.

        Returns:
            Response with X-Request-ID header.
        """
        # Use existing header or generate new ID
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())

        # Store in request state for access in route handlers
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
```

## BaseHTTPMiddleware: Logging

```python
"""Structured request logging middleware."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs request details."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Log request and response details.

        Args:
            request: The incoming request.
            call_next: The next middleware or route handler.

        Returns:
            The response from the route handler.
        """
        start_time = time.perf_counter()
        request_id = getattr(request.state, "request_id", "unknown")

        # Log request
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
            },
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            logger.exception(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "error": str(exc),
                },
            )
            raise

        duration = time.perf_counter() - start_time

        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            },
        )

        return response
```

## Pure ASGI: Timing (High Performance)

```python
"""Pure ASGI timing middleware for maximum performance."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Message, Receive, Scope, Send


class TimingMiddleware:
    """Pure ASGI middleware that adds request timing headers."""

    def __init__(self, app: ASGIApp) -> None:
        """Initialize with the wrapped application.

        Args:
            app: The ASGI application to wrap.
        """
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """Process ASGI request with timing.

        Args:
            scope: ASGI connection scope.
            receive: ASGI receive callable.
            send: ASGI send callable.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                process_time = time.perf_counter() - start_time
                headers = list(message.get("headers", []))
                headers.append((b"x-process-time", f"{process_time:.4f}".encode()))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_wrapper)
```

## Pure ASGI: Correlation ID

```python
"""Correlation ID middleware for distributed tracing."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

CORRELATION_ID_HEADER = b"x-correlation-id"


class CorrelationMiddleware:
    """Pure ASGI middleware for correlation ID propagation."""

    def __init__(self, app: ASGIApp) -> None:
        """Initialize with the wrapped application.

        Args:
            app: The ASGI application to wrap.
        """
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """Process ASGI request with correlation ID.

        Args:
            scope: ASGI connection scope.
            receive: ASGI receive callable.
            send: ASGI send callable.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract or generate correlation ID
        headers = dict(scope.get("headers", []))
        correlation_id = headers.get(CORRELATION_ID_HEADER, b"").decode() or str(
            uuid.uuid4()
        )

        # Store in scope for access in route handlers
        scope["state"] = scope.get("state", {})
        scope["state"]["correlation_id"] = correlation_id

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((CORRELATION_ID_HEADER, correlation_id.encode()))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_wrapper)
```

## Test Example: Timing Middleware

```python
"""Tests for timing middleware."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.timing import TimingMiddleware


@pytest.fixture
def app() -> FastAPI:
    """Create test application with middleware."""
    app = FastAPI()
    app.add_middleware(TimingMiddleware)

    @app.get("/test")
    async def test_endpoint() -> dict[str, str]:
        return {"status": "ok"}

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


class TestTimingMiddleware:
    """Tests for TimingMiddleware."""

    def test_adds_timing_header(self, client: TestClient) -> None:
        """It should add X-Process-Time header."""
        response = client.get("/test")
        assert "X-Process-Time" in response.headers

    def test_timing_is_numeric(self, client: TestClient) -> None:
        """It should return a numeric timing value."""
        response = client.get("/test")
        timing = response.headers["X-Process-Time"]
        assert float(timing) >= 0

    def test_does_not_affect_response(self, client: TestClient) -> None:
        """It should not affect the response body."""
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
```

## Registration Example

```python
"""Application setup with middleware."""

from fastapi import FastAPI

from app.middleware.correlation import CorrelationMiddleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.timing import TimingMiddleware


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI()

    # Middleware order matters! First added = outermost
    # Request flow: Correlation -> Logging -> Timing -> Route
    # Response flow: Route -> Timing -> Logging -> Correlation
    app.add_middleware(TimingMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(CorrelationMiddleware)

    return app
```
