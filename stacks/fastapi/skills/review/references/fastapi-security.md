# FastAPI Security Patterns

OWASP-aligned security patterns for FastAPI applications.

---

## Authentication

### OAuth2 with JWT

```python
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id: int | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user
```

---

## Input Validation

### Pydantic Validators

```python
from __future__ import annotations

import re

from pydantic import BaseModel, field_validator


class UserCreate(BaseModel):
    """Schema for creating a user with validated fields."""

    email: str
    password: str
    username: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", v):
            msg = "Invalid email format"
            raise ValueError(msg)
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            msg = "Password must be at least 8 characters"
            raise ValueError(msg)
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            msg = "Username must be alphanumeric with underscores"
            raise ValueError(msg)
        return v
```

---

## SQL Injection Prevention

### SAFE: SQLAlchemy parameterized queries

```python
# Safe - uses parameterized query
stmt = select(User).where(User.email == email)

# Safe - uses SQLAlchemy text with bind params
from sqlalchemy import text
stmt = text("SELECT * FROM users WHERE email = :email")
result = await db.execute(stmt, {"email": email})
```

### UNSAFE: Raw SQL with f-strings

```python
# NEVER DO THIS - SQL injection vulnerability
query = f"SELECT * FROM users WHERE email = '{email}'"
result = await db.execute(text(query))
```

---

## CORS Configuration

```python
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


def configure_cors(app: FastAPI) -> None:
    """Configure CORS middleware with environment-specific origins."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,  # Never use ["*"] in production
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
```

---

## Secrets Management

```python
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Never hardcode secrets - always load from environment
    secret_key: str
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = ["http://localhost:3000"]
    debug: bool = False
```

---

## Rate Limiting

```python
from __future__ import annotations

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


# Apply to specific routes
@router.post("/api/v1/auth/token")
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """Rate-limited login endpoint."""
    ...
```

---

## Security Checklist

| Category | Check | Status |
|----------|-------|--------|
| Authentication | JWT tokens with expiry | Required |
| Authentication | Password hashing (bcrypt/argon2) | Required |
| Authorization | Role-based access control | Required |
| Input | Pydantic schemas on all endpoints | Required |
| SQL | No raw SQL with string interpolation | Required |
| CORS | Environment-specific origins | Required |
| Secrets | Pydantic Settings from env vars | Required |
| Headers | Security headers middleware | Recommended |
| Rate Limiting | On auth and public endpoints | Recommended |
| Logging | No sensitive data in logs | Required |
