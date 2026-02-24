# FastAPI OAuth Patterns

OAuth2 and JWT authentication patterns.

---

## 1. JWT Configuration

```python
# app/core/security.py
"""Security utilities for JWT and password handling."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings

ph = PasswordHasher()

ALGORITHM = "HS256"


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        **(extra_claims or {}),
    }

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """Create a JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": subject,
        "exp": expire,
        "type": "refresh",
    }

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


def hash_password(password: str) -> str:
    """Hash a password using Argon2."""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False
```

---

## 2. OAuth2 Password Flow

```python
# app/api/v1/auth.py
"""Authentication endpoints."""

from __future__ import annotations

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.dependencies.database import Database
from app.schemas.auth import Token, TokenRefresh
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Database,
) -> Token:
    """Authenticate user and return tokens."""
    service = UserService(db)
    user = await service.get_by_email(form_data.username)

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: Database,
) -> Token:
    """Refresh access token using refresh token."""
    try:
        payload = decode_token(token_data.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        user_id = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    service = UserService(db)
    user = await service.get_by_id(user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    access_token = create_access_token(subject=str(user.id))
    new_refresh_token = create_refresh_token(subject=str(user.id))

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )
```

---

## 3. Current User Dependency

```python
# app/dependencies/auth.py
"""Authentication dependencies."""

from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.security import ALGORITHM
from app.dependencies.database import Database
from app.models.user import User
from app.services.user_service import UserService

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Database,
) -> User:
    """Get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credentials_exception

    service = UserService(db)
    user = await service.get_by_id(user_id)

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user


async def get_current_active_superuser(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current user, ensuring they are a superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


# Type aliases
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentSuperuser = Annotated[User, Depends(get_current_active_superuser)]
```

---

## 4. OAuth2 Social Login

```python
# app/services/oauth_service.py
"""OAuth provider integration service."""

from __future__ import annotations

from typing import TYPE_CHECKING
import httpx

from app.core.config import settings

if TYPE_CHECKING:
    from app.models.user import User


class OAuthService:
    """Handle OAuth provider authentication."""

    async def get_google_user_info(self, access_token: str) -> dict:
        """Get user info from Google."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()

    async def get_github_user_info(self, access_token: str) -> dict:
        """Get user info from GitHub."""
        async with httpx.AsyncClient() as client:
            # Get user profile
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
            user_data = response.json()

            # Get primary email
            email_response = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/json",
                },
            )
            email_response.raise_for_status()
            emails = email_response.json()
            primary_email = next(
                (e["email"] for e in emails if e["primary"]),
                emails[0]["email"] if emails else None,
            )

            return {**user_data, "email": primary_email}

    async def exchange_code_for_token(
        self,
        provider: str,
        code: str,
        redirect_uri: str,
    ) -> str:
        """Exchange authorization code for access token."""
        if provider == "google":
            return await self._exchange_google_code(code, redirect_uri)
        elif provider == "github":
            return await self._exchange_github_code(code, redirect_uri)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _exchange_google_code(self, code: str, redirect_uri: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            return response.json()["access_token"]

    async def _exchange_github_code(self, code: str, redirect_uri: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "code": code,
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                },
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()["access_token"]
```

---

## 5. OAuth Callback Endpoint

```python
# app/api/v1/oauth.py
"""OAuth callback endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.dependencies.database import Database
from app.schemas.auth import OAuthCallback, Token
from app.services.oauth_service import OAuthService
from app.services.user_service import UserService
from app.core.security import create_access_token, create_refresh_token

router = APIRouter(prefix="/oauth", tags=["oauth"])


@router.post("/{provider}/callback", response_model=Token)
async def oauth_callback(
    provider: str,
    callback_data: OAuthCallback,
    db: Database,
) -> Token:
    """Handle OAuth callback and return tokens."""
    oauth_service = OAuthService()
    user_service = UserService(db)

    # Exchange code for access token
    try:
        access_token = await oauth_service.exchange_code_for_token(
            provider=provider,
            code=callback_data.code,
            redirect_uri=callback_data.redirect_uri,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange code: {str(e)}",
        )

    # Get user info from provider
    if provider == "google":
        user_info = await oauth_service.get_google_user_info(access_token)
    elif provider == "github":
        user_info = await oauth_service.get_github_user_info(access_token)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider: {provider}",
        )

    # Find or create user
    user = await user_service.get_or_create_from_oauth(
        provider=provider,
        provider_id=str(user_info["id"]),
        email=user_info["email"],
        name=user_info.get("name", user_info.get("login")),
    )

    # Generate tokens
    jwt_access_token = create_access_token(subject=str(user.id))
    jwt_refresh_token = create_refresh_token(subject=str(user.id))

    return Token(
        access_token=jwt_access_token,
        refresh_token=jwt_refresh_token,
        token_type="bearer",
    )
```

---

## 6. Schemas

```python
# app/schemas/auth.py
"""Authentication schemas."""

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Token refresh request schema."""

    refresh_token: str


class OAuthCallback(BaseModel):
    """OAuth callback request schema."""

    code: str
    redirect_uri: str


class UserCreate(BaseModel):
    """User creation schema."""

    email: EmailStr
    password: str
    name: str


class UserLogin(BaseModel):
    """User login schema."""

    email: EmailStr
    password: str
```

---

## 7. Token Blacklist

```python
# app/services/token_service.py
"""Token management service."""

from __future__ import annotations

from datetime import datetime, timezone

import redis.asyncio as redis

from app.core.config import settings


class TokenService:
    """Manage token blacklist for logout."""

    def __init__(self) -> None:
        self.redis = redis.from_url(settings.REDIS_URL)

    async def blacklist_token(self, token: str, exp: datetime) -> None:
        """Add token to blacklist until it expires."""
        ttl = int((exp - datetime.now(timezone.utc)).total_seconds())
        if ttl > 0:
            await self.redis.setex(f"blacklist:{token}", ttl, "1")

    async def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted."""
        return await self.redis.exists(f"blacklist:{token}") > 0

    async def close(self) -> None:
        """Close Redis connection."""
        await self.redis.close()
```

---

## 8. Logout Endpoint

```python
# app/api/v1/auth.py (continued)

@router.post("/logout")
async def logout(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> dict[str, str]:
    """Logout and blacklist the current token."""
    token = credentials.credentials

    try:
        payload = decode_token(token)
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        token_service = TokenService()
        await token_service.blacklist_token(token, exp)
        await token_service.close()

        return {"message": "Successfully logged out"}
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
```

---

## 9. Testing Authentication

```python
# tests/test_auth.py
"""Authentication tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    """Test successful login."""
    response = await client.post(
        "/api/v1/auth/token",
        data={
            "username": test_user.email,
            "password": "testpassword123",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with invalid credentials."""
    response = await client.post(
        "/api/v1/auth/token",
        data={
            "username": "wrong@example.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint(client: AsyncClient, auth_headers):
    """Test accessing protected endpoint with valid token."""
    response = await client.get("/api/v1/users/me", headers=auth_headers)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_protected_endpoint_no_token(client: AsyncClient):
    """Test accessing protected endpoint without token."""
    response = await client.get("/api/v1/users/me")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_token_refresh(client: AsyncClient, test_user):
    """Test token refresh."""
    # First login
    login_response = await client.post(
        "/api/v1/auth/token",
        data={
            "username": test_user.email,
            "password": "testpassword123",
        },
    )
    refresh_token = login_response.json()["refresh_token"]

    # Refresh
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
```
