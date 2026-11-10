# Flask Error Responses: Problem Details (RFC 9457)

Read when adding an error case, a domain exception, or touching the error
handlers. Every error response is `application/problem+json` with one shape,
so clients parse one format and tests assert one format.

```json
{
  "type": "about:blank",
  "title": "Not Found",
  "status": 404,
  "detail": "Project 42 not found",
  "instance": "/api/projects/42"
}
```

Validation errors add an `errors` member (extension fields are allowed).

## Domain Exceptions

```python
# src/app/errors.py
class AppError(Exception):
    """Base for errors that map to an HTTP status."""

    status: int = 400
    title: str = "Bad Request"

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class NotFoundError(AppError):
    status = 404
    title = "Not Found"


class ConflictError(AppError):
    status = 409
    title = "Conflict"


class PermissionDeniedError(AppError):
    status = 403
    title = "Forbidden"
```

Services raise these; they never import Flask or build responses.

## Handlers

```python
# src/app/errors.py (continued)
import logging

from flask import Flask, Response, json, request
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from app.extensions import db

logger = logging.getLogger(__name__)


def problem(status: int, title: str, detail: str | None = None, **extra: object) -> Response:
    """Build an application/problem+json response."""
    body = {"type": "about:blank", "title": title, "status": status, "instance": request.path}
    if detail:
        body["detail"] = detail
    body.update(extra)
    return Response(json.dumps(body), status=status, mimetype="application/problem+json")


def register_error_handlers(app: Flask) -> None:
    """Map every error to a problem+json response."""

    @app.errorhandler(AppError)
    def app_error(error: AppError) -> Response:
        return problem(error.status, error.title, error.detail)

    @app.errorhandler(ValidationError)
    def validation_error(error: ValidationError) -> Response:
        return problem(
            422,
            "Unprocessable Content",
            "Request body is invalid",
            errors=error.errors(include_url=False, include_context=False),
        )

    @app.errorhandler(HTTPException)
    def http_error(error: HTTPException) -> Response:
        # abort(404, "..."), 405, 413, and Flask's own 400 on bad JSON
        return problem(error.code or 500, error.name, error.description)

    @app.errorhandler(Exception)
    def unhandled(error: Exception) -> Response:
        db.session.rollback()
        logger.exception("Unhandled error on %s %s", request.method, request.path)
        return problem(500, "Internal Server Error")  # no details to the client
```

In views, use `abort(404, description="Project 42 not found")` or raise a domain
error; never `return {"error": ...}, 404` by hand.

## Rules

- One format for every error, including 404/405 from routing and 500s.
- `detail` is for humans and never contains stack traces, SQL or secrets.
- The catch-all `Exception` handler logs with `logger.exception` (traceback) and
  rolls back the session; in debug mode Flask's debugger still wins for 500s.
- `request.get_json()` on a non-JSON body raises a 415/400 `HTTPException`: the
  `HTTPException` handler covers it.
- Tests assert `response.status_code`, `response.mimetype == "application/problem+json"`
  and `response.json["detail"]` (or `errors` for 422).
