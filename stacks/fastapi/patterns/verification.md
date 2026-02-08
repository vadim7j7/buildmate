# FastAPI Verification Pattern

## Overview

FastAPI implementations are verified by making HTTP requests to the dev server
using httpie or curl, validating responses against Pydantic schemas, and checking
OpenAPI documentation.

## Prerequisites

- Uvicorn server running on port 8000
- Test database available
- Authentication tokens for protected endpoints

## Verification Workflow

### 1. Start Dev Server

```bash
# Check if running
curl -s http://localhost:8000/health || uvicorn main:app --port 8000 &

# Wait for ready
until curl -s http://localhost:8000/docs; do sleep 1; done
```

### 2. Test Endpoint

```bash
# Using httpie (preferred)
http POST localhost:8000/api/users \
  email=test@example.com \
  name="Test User"

# Using curl
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "name": "Test User"}'
```

### 3. Validate Response

| Check | Expected |
|-------|----------|
| Status code | 201 for create, 200 for success |
| Content-Type | application/json |
| Body matches Pydantic schema | All fields present and typed |

### 4. Check OpenAPI Docs

```bash
# Get OpenAPI schema
curl http://localhost:8000/openapi.json | jq '.paths["/api/users"]'

# Verify endpoint documented
curl -s http://localhost:8000/openapi.json | \
  jq '.paths["/api/users"]["post"]' | \
  grep -q "requestBody" && echo "✓ Endpoint documented"
```

## Endpoint Testing

### GET Request

```bash
# List all
http localhost:8000/api/users

# Get one
http localhost:8000/api/users/1

# With query params
http localhost:8000/api/users skip==0 limit==10

# With auth
http localhost:8000/api/users Authorization:"Bearer $TOKEN"
```

### POST Request

```bash
# Create
http POST localhost:8000/api/users \
  email=test@example.com \
  name="Test User" \
  -v  # verbose to see status code

# Expected response:
# HTTP/1.1 201 Created
# {"id": 1, "email": "test@example.com", "name": "Test User"}
```

### PUT/PATCH Request

```bash
# Full update
http PUT localhost:8000/api/users/1 \
  email=updated@example.com \
  name="Updated User"

# Partial update
http PATCH localhost:8000/api/users/1 \
  name="Just Name"
```

### DELETE Request

```bash
# Delete
http DELETE localhost:8000/api/users/1

# Verify deleted
http localhost:8000/api/users/1
# Expected: 404
```

## Error Handling Verification

### Validation Errors

```bash
# Missing required field
http POST localhost:8000/api/users name="No Email"
# Expected: 422 with validation details

# Invalid type
http POST localhost:8000/api/users email:=123
# Expected: 422

# Invalid format
http POST localhost:8000/api/users email=invalid
# Expected: 422
```

### Not Found

```bash
http localhost:8000/api/users/99999
# Expected: 404 {"detail": "User not found"}
```

### Unauthorized

```bash
http localhost:8000/api/protected
# Expected: 401 {"detail": "Not authenticated"}
```

### Forbidden

```bash
http localhost:8000/api/admin Authorization:"Bearer $USER_TOKEN"
# Expected: 403 {"detail": "Not enough permissions"}
```

## Schema Validation

### Check Response Matches Schema

```python
# test_users.py
from pydantic import BaseModel
from httpx import AsyncClient

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime

async def test_create_user_response():
    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.post("/api/users", json={
            "email": "test@example.com",
            "name": "Test"
        })

        # Validate against schema
        user = UserResponse(**response.json())
        assert user.id > 0
        assert user.email == "test@example.com"
```

### Verify OpenAPI Schema

```bash
# Check endpoint exists in OpenAPI
curl -s http://localhost:8000/openapi.json | \
  jq '.paths | keys | map(select(contains("/users")))'

# Check request schema
curl -s http://localhost:8000/openapi.json | \
  jq '.paths["/api/users"]["post"]["requestBody"]["content"]["application/json"]["schema"]'

# Check response schema
curl -s http://localhost:8000/openapi.json | \
  jq '.paths["/api/users"]["post"]["responses"]["201"]["content"]["application/json"]["schema"]'
```

## Auto-Fix Patterns

### Route Not Found

**Error:** `404 Not Found` for new endpoint

**Fix:**
```python
# app/routers/users.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("/", status_code=201)
async def create_user(user: UserCreate) -> UserResponse:
    ...

# main.py
from app.routers import users
app.include_router(users.router)
```

### Validation Error

**Error:** `422 Unprocessable Entity`

**Check:**
```python
# Verify Pydantic model
class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
```

### Missing Response Model

**Error:** Response not validated

**Fix:**
```python
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int) -> UserResponse:
    ...
```

### Dependency Injection Issue

**Error:** `Dependency not found`

**Fix:**
```python
from fastapi import Depends

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    ...
```

## Performance Verification

### Response Time

```bash
# Time request
time http localhost:8000/api/users

# Or with curl
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/users
```

### Async Verification

```python
# Verify async endpoints
import asyncio

async def test_concurrent_requests():
    async with AsyncClient(base_url="http://localhost:8000") as client:
        tasks = [client.get("/api/users") for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        assert all(r.status_code == 200 for r in responses)
```

## Verification Report Template

```markdown
# FastAPI Verification Report

**Endpoint:** POST /api/users
**Router:** users.router
**Time:** TIMESTAMP

## Request

```http
POST /api/users HTTP/1.1
Content-Type: application/json

{"email": "test@example.com", "name": "Test"}
```

## Response

```http
HTTP/1.1 201 Created
Content-Type: application/json

{"id": 1, "email": "test@example.com", "name": "Test", "created_at": "..."}
```

## Checks

| Check | Status |
|-------|--------|
| Route exists | ✓ Pass |
| Status code 201 | ✓ Pass |
| Response matches schema | ✓ Pass |
| OpenAPI documented | ✓ Pass |

## Error Handling

| Case | Expected | Actual | Status |
|------|----------|--------|--------|
| Missing email | 422 | 422 | ✓ Pass |
| Invalid email | 422 | 422 | ✓ Pass |
| Duplicate email | 409 | 409 | ✓ Pass |
| Not found | 404 | 404 | ✓ Pass |
| Unauthorized | 401 | 401 | ✓ Pass |

## Performance

| Metric | Value | Status |
|--------|-------|--------|
| Response time | 45ms | ✓ Good |
| Concurrent (10) | 120ms | ✓ Good |
```
