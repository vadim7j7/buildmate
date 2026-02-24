---
name: new-middleware
description: Generate an ASGI middleware with async handling
---

# /new-middleware

## What This Does

Generates an ASGI middleware class that wraps the FastAPI application to handle
cross-cutting concerns like request timing, logging, CORS, rate limiting, or
custom headers. Also generates the corresponding test file.

## Usage

```
/new-middleware timing              # Creates TimingMiddleware
/new-middleware request_id          # Creates RequestIdMiddleware
/new-middleware logging             # Creates LoggingMiddleware
/new-middleware correlation         # Creates CorrelationMiddleware
```

## How It Works

1. **Read reference patterns.** Load middleware patterns from:
   - `skills/new-middleware/references/middleware-examples.md`
   - `patterns/backend-patterns.md`
   - `styles/backend-python.md`

2. **Determine middleware name.** Parse the argument to determine:
   - Class name (e.g., `TimingMiddleware`)
   - File path (e.g., `src/app/middleware/timing.py`)

3. **Generate the middleware file.** Create the middleware with:
   - `from __future__ import annotations`
   - `BaseHTTPMiddleware` or pure ASGI implementation
   - Async `dispatch` or `__call__` method
   - Proper type annotations
   - Exception handling

4. **Generate the test file.** Create the test with:
   - Test app fixture
   - Tests for middleware behavior
   - Edge cases and error conditions

5. **Update the app setup.** Provide instructions for registering the middleware:

   ```python
   from app.middleware.timing import TimingMiddleware

   app.add_middleware(TimingMiddleware)
   ```

6. **Run quality checks.**

   ```bash
   uv run ruff format src/app/middleware/<name>.py tests/middleware/test_<name>.py
   uv run ruff check src/app/middleware/<name>.py tests/middleware/test_<name>.py
   uv run mypy src/app/middleware/<name>.py
   uv run pytest tests/middleware/test_<name>.py
   ```

7. **Report results.** Show the generated files.

## Generated Files

```
src/app/middleware/<name>.py
tests/middleware/test_<name>.py
```

## Example Output

For `/new-middleware timing`:

**Middleware:** `src/app/middleware/timing.py`
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

    from starlette.types import ASGIApp


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

**Pure ASGI Alternative:** `src/app/middleware/timing_asgi.py`
```python
"""Pure ASGI timing middleware for maximum performance."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Message, Receive, Scope, Send


class TimingMiddleware:
    """ASGI middleware that adds request timing headers."""

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
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)
```

**Test:** `tests/middleware/test_timing.py`

## Rules

- Use `BaseHTTPMiddleware` for simple cases
- Use pure ASGI implementation for performance-critical middleware
- Always handle exceptions gracefully
- Use `time.perf_counter()` for timing (not `time.time()`)
- Add type annotations for all parameters and returns
- Document the middleware purpose and usage
- Middleware order matters - document any ordering requirements
