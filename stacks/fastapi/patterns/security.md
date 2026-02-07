# FastAPI Security Patterns

Security patterns and best practices for Python FastAPI applications. All agents
must follow these patterns to prevent OWASP Top 10 vulnerabilities.

---

## 1. SQL Injection Prevention

Always use parameterized queries. Never use string interpolation with SQL.

```python
# WRONG - SQL injection vulnerability
@router.get("/users")
async def get_users(email: str, db: AsyncSession = Depends(get_db)):
    query = f"SELECT * FROM users WHERE email = '{email}'"  # DANGEROUS!
    result = await db.execute(text(query))
    return result.fetchall()

# CORRECT - parameterized query with SQLAlchemy ORM
@router.get("/users")
async def get_users(email: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalars().all()

# CORRECT - parameterized raw SQL if needed
@router.get("/users")
async def get_users(email: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {"email": email}
    )
    return result.fetchall()
```

### Dynamic Column Names

```python
# WRONG - user input as column name
@router.get("/users")
async def get_users(sort_by: str, db: AsyncSession = Depends(get_db)):
    query = f"SELECT * FROM users ORDER BY {sort_by}"  # SQL injection!
    return await db.execute(text(query))

# CORRECT - whitelist allowed columns
ALLOWED_SORT_COLUMNS = {"created_at", "name", "email"}

@router.get("/users")
async def get_users(
    sort_by: str = Query(default="created_at"),
    db: AsyncSession = Depends(get_db)
):
    if sort_by not in ALLOWED_SORT_COLUMNS:
        raise HTTPException(400, f"Invalid sort column. Allowed: {ALLOWED_SORT_COLUMNS}")

    column = getattr(User, sort_by)
    result = await db.execute(select(User).order_by(column))
    return result.scalars().all()
```

---

## 2. Authentication & Authorization

### JWT Token Authentication

```python
# auth/jwt.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

### Role-Based Access Control

```python
# auth/permissions.py
from enum import Enum
from functools import wraps

class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


def require_role(*allowed_roles: Role):
    """Dependency that checks user role."""
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


# Usage
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_role(Role.ADMIN, Role.SUPERADMIN)),
    db: AsyncSession = Depends(get_db)
):
    # Only admins can reach here
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
    return {"status": "deleted"}
```

### Resource-Based Authorization

```python
# WRONG - no authorization check
@router.get("/projects/{project_id}")
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()  # Anyone can view any project!

# CORRECT - verify ownership or access
@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .where(
            or_(
                Project.owner_id == current_user.id,
                Project.members.any(User.id == current_user.id)
            )
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
```

---

## 3. Input Validation

Use Pydantic for all input validation.

```python
# schemas/user.py
from pydantic import BaseModel, EmailStr, Field, validator
import re


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)
    name: str = Field(..., min_length=2, max_length=100)

    @validator("password")
    def validate_password_strength(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain digit")
        return v

    @validator("name")
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    bio: str | None = Field(None, max_length=1000)

    class Config:
        # Prevent extra fields
        extra = "forbid"
```

### Path Parameter Validation

```python
from uuid import UUID

# CORRECT - validate UUID format
@router.get("/users/{user_id}")
async def get_user(user_id: UUID):  # Automatically validates UUID
    ...

# CORRECT - constrained integers
@router.get("/items")
async def get_items(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100)
):
    ...

# CORRECT - regex validation
@router.get("/users/{username}")
async def get_user_by_username(
    username: str = Path(..., regex=r"^[a-zA-Z0-9_]{3,30}$")
):
    ...
```

---

## 4. CORS Configuration

```python
# main.py
from fastapi.middleware.cors import CORSMiddleware

# WRONG - allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Too permissive!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CORRECT - explicit origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://myapp.com",
        "https://www.myapp.com",
        "http://localhost:3000" if settings.DEBUG else None,
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,  # Cache preflight for 10 minutes
)
```

---

## 5. Rate Limiting

```python
# middleware/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Usage on endpoints
@router.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: LoginRequest):
    ...


@router.post("/api/data")
@limiter.limit("100/hour")
async def create_data(request: Request, data: DataCreate):
    ...


# Per-user rate limiting
def get_user_identifier(request: Request) -> str:
    """Rate limit by user ID if authenticated, otherwise by IP."""
    auth_header = request.headers.get("Authorization")
    if auth_header:
        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return f"user:{payload.get('sub')}"
        except:
            pass
    return get_remote_address(request)


user_limiter = Limiter(key_func=get_user_identifier)
```

---

## 6. File Upload Security

```python
from fastapi import UploadFile, File
import magic  # python-magic for content type detection

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


async def validate_file(file: UploadFile) -> bytes:
    """Validate file type and size."""
    # Check file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(400, f"File too large. Max size: {MAX_FILE_SIZE} bytes")

    # Verify actual content type (not just extension)
    detected_type = magic.from_buffer(contents, mime=True)
    if detected_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            400,
            f"Invalid file type: {detected_type}. Allowed: {ALLOWED_CONTENT_TYPES}"
        )

    await file.seek(0)  # Reset for later use
    return contents


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    contents = await validate_file(file)

    # Generate safe filename
    ext = Path(file.filename).suffix.lower()
    safe_filename = f"{uuid4()}{ext}"

    # Store file
    file_path = UPLOAD_DIR / safe_filename
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(contents)

    return {"filename": safe_filename}
```

---

## 7. Secrets Management

```python
# config/settings.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Required secrets (no defaults - fail if missing)
    SECRET_KEY: str
    DATABASE_URL: str
    REDIS_URL: str

    # Optional with secure defaults
    DEBUG: bool = False
    ALLOWED_HOSTS: list[str] = ["localhost"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# WRONG - hardcoded secrets
SECRET_KEY = "my-secret-key"  # Never do this!

# WRONG - secrets in code comments
# DATABASE_URL = "postgres://user:password@host/db"

# CORRECT - use environment variables
# .env file (never commit!)
# SECRET_KEY=<generated-secret>
# DATABASE_URL=postgres://...
```

### Logging Sanitization

```python
# WRONG - logging sensitive data
logger.info(f"User login: {email}, password: {password}")
logger.debug(f"API request with token: {token}")

# CORRECT - redact sensitive fields
logger.info(f"User login: {email}")
logger.debug("API request with token: [REDACTED]")

# Use a logging filter for automatic redaction
class SensitiveDataFilter(logging.Filter):
    SENSITIVE_PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']?[^"\'}\s]+', 'password: [REDACTED]'),
        (r'token["\']?\s*[:=]\s*["\']?[^"\'}\s]+', 'token: [REDACTED]'),
        (r'secret["\']?\s*[:=]\s*["\']?[^"\'}\s]+', 'secret: [REDACTED]'),
    ]

    def filter(self, record):
        message = record.getMessage()
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
        record.msg = message
        record.args = ()
        return True
```

---

## 8. Security Headers

```python
# middleware/security_headers.py
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"  # Disabled, use CSP
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response


app.add_middleware(SecurityHeadersMiddleware)
```

---

## 9. Error Handling

Don't expose internal details in error messages.

```python
# WRONG - exposing internal errors
@router.get("/users/{user_id}")
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one()
    except Exception as e:
        raise HTTPException(500, str(e))  # Exposes SQL errors!

# CORRECT - generic error messages, log internally
@router.get("/users/{user_id}")
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(404, "User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching user {user_id}")
        raise HTTPException(500, "Internal server error")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error: {request.url}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

---

## 10. Dependency Injection Security

```python
# WRONG - mutable default argument
def get_db(db: AsyncSession = AsyncSession()):  # Same instance reused!
    return db

# CORRECT - use generator dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()


# CORRECT - scoped resources
async def get_current_user_project(
    project_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Project:
    """Dependency that verifies user owns/has access to project."""
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .where(Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.get("/projects/{project_id}/tasks")
async def get_project_tasks(
    project: Project = Depends(get_current_user_project)  # Already authorized!
):
    return project.tasks
```

---

## Security Checklist

Before deploying any feature, verify:

- [ ] All SQL uses parameterized queries (no string interpolation)
- [ ] JWT tokens have reasonable expiration times
- [ ] Role/permission checks on all protected endpoints
- [ ] Resource ownership verified before access
- [ ] All input validated with Pydantic schemas
- [ ] CORS configured with explicit origins
- [ ] Rate limiting on sensitive endpoints
- [ ] File uploads validate content type, not just extension
- [ ] Secrets loaded from environment, not hardcoded
- [ ] Error messages don't expose internal details
- [ ] Security headers configured
- [ ] Sensitive data excluded from logs
