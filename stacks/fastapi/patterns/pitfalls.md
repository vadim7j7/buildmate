# FastAPI Common Pitfalls & Anti-Patterns

Common mistakes and performance issues in Python FastAPI applications. All agents
must recognize and avoid these patterns.

---

## 1. Async/Await Pitfalls

### Blocking the Event Loop

```python
# WRONG - blocking I/O in async function
@router.get("/users")
async def get_users():
    users = requests.get("https://api.example.com/users")  # BLOCKING!
    return users.json()

# CORRECT - use async HTTP client
import httpx

@router.get("/users")
async def get_users():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/users")
        return response.json()


# WRONG - blocking file I/O
@router.get("/file")
async def get_file():
    with open("large_file.txt") as f:
        return f.read()  # BLOCKING!

# CORRECT - use async file I/O
import aiofiles

@router.get("/file")
async def get_file():
    async with aiofiles.open("large_file.txt") as f:
        return await f.read()


# WRONG - CPU-bound work in async
@router.post("/process")
async def process_data(data: DataInput):
    result = expensive_computation(data)  # Blocks event loop!
    return result

# CORRECT - run in thread pool
from concurrent.futures import ThreadPoolExecutor
import asyncio

executor = ThreadPoolExecutor(max_workers=4)

@router.post("/process")
async def process_data(data: DataInput):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, expensive_computation, data)
    return result
```

### Forgetting await

```python
# WRONG - forgot await
@router.post("/users")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db.execute(insert(User).values(**user.dict()))  # Not awaited!
    db.commit()  # Not awaited!
    return {"status": "created"}

# User never gets created because operations weren't awaited

# CORRECT - await all async operations
@router.post("/users")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    await db.execute(insert(User).values(**user.dict()))
    await db.commit()
    return {"status": "created"}
```

### Mixing sync and async

```python
# WRONG - sync function using async DB
def get_users(db: Session):  # Note: not async def
    # Can't use async db here!
    return db.query(User).all()

# CORRECT - be consistent with async
async def get_users(db: AsyncSession):
    result = await db.execute(select(User))
    return result.scalars().all()


# If you MUST use sync code, use sync dependencies
def get_sync_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/users")
def get_users(db: Session = Depends(get_sync_db)):  # Note: def, not async def
    return db.query(User).all()
```

---

## 2. SQLAlchemy Session Pitfalls

### Session Scope Issues

```python
# WRONG - reusing session across requests
db_session = AsyncSession(engine)  # Global session - BAD!

@router.get("/users")
async def get_users():
    return await db_session.execute(select(User))  # Shared state!


# CORRECT - scoped session per request
async def get_db():
    async with AsyncSession(engine) as session:
        yield session

@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

### Not Committing

```python
# WRONG - changes not committed
@router.post("/users")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    # Forgot commit - user not saved!
    return db_user

# CORRECT - commit changes
@router.post("/users")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)  # Get updated fields like id
    return db_user


# BETTER - handle in dependency
async def get_db():
    async with AsyncSession(engine) as session:
        try:
            yield session
            await session.commit()  # Auto-commit on success
        except:
            await session.rollback()
            raise
```

### N+1 Query Problem

```python
# WRONG - N+1 queries
@router.get("/projects")
async def get_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project))
    projects = result.scalars().all()

    # Each access triggers a query!
    return [
        {"name": p.name, "owner": p.owner.name}  # N queries for owner
        for p in projects
    ]

# CORRECT - eager loading with joinedload
from sqlalchemy.orm import joinedload

@router.get("/projects")
async def get_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Project).options(joinedload(Project.owner))
    )
    projects = result.scalars().unique().all()  # unique() needed with joinedload
    return [
        {"name": p.name, "owner": p.owner.name}
        for p in projects
    ]


# CORRECT - selectinload for collections
@router.get("/projects/{project_id}")
async def get_project(project_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(
            joinedload(Project.owner),        # To-one: joinedload
            selectinload(Project.tasks)       # To-many: selectinload
        )
    )
    return result.scalar_one()
```

### Detached Instance Error

```python
# WRONG - accessing relationship after session closed
@router.get("/users/{user_id}")
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    return user  # Session closes after response

# Later in response serialization:
# user.projects  # DetachedInstanceError!


# CORRECT - eager load or access within session
@router.get("/users/{user_id}")
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.projects))
    )
    user = result.scalar_one()
    return UserResponse.from_orm(user)  # Serialize while session open
```

---

## 3. Dependency Injection Issues

### Mutable Default Arguments

```python
# WRONG - mutable default (shared across requests!)
@router.get("/search")
async def search(filters: list = []):  # Same list reused!
    filters.append("active=true")
    return do_search(filters)

# First request: filters = ["active=true"]
# Second request: filters = ["active=true", "active=true"]

# CORRECT - use None and create new list
@router.get("/search")
async def search(filters: list | None = None):
    filters = filters or []
    filters.append("active=true")
    return do_search(filters)

# OR use Query with default factory
from fastapi import Query

@router.get("/search")
async def search(filters: list[str] = Query(default=[])):
    ...
```

### Dependency Not Re-evaluated

```python
# WRONG - expecting fresh value each request
def get_timestamp():
    return datetime.now()  # Called once at startup if not a generator!

@router.get("/time")
async def get_time(ts: datetime = Depends(get_timestamp)):
    return ts

# CORRECT - use generator or async generator
def get_timestamp():
    yield datetime.now()  # Called each request


# Or use Depends with a callable class
class TimestampDep:
    def __call__(self) -> datetime:
        return datetime.now()

@router.get("/time")
async def get_time(ts: datetime = Depends(TimestampDep())):
    return ts
```

---

## 4. Response Model Issues

### Exposing Internal Data

```python
# WRONG - returning ORM model directly
@router.get("/users/{user_id}")
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one()  # Exposes password_hash!


# CORRECT - use response model
class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one()  # Filtered by response_model
```

### Missing Response Model Validation

```python
# WRONG - no response validation
@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()  # No type checking on response

# CORRECT - validate with response_model
@router.get("/users", response_model=list[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

---

## 5. Background Tasks Pitfalls

### Long-running Tasks Blocking

```python
# WRONG - background task blocks if too long
from fastapi import BackgroundTasks

@router.post("/process")
async def process(data: DataInput, background_tasks: BackgroundTasks):
    background_tasks.add_task(very_long_process, data)  # Still blocks worker
    return {"status": "processing"}

# For short tasks, BackgroundTasks is fine
# For long tasks, use a proper task queue

# CORRECT - use Celery or similar for long tasks
from app.tasks import process_data_task

@router.post("/process")
async def process(data: DataInput):
    task = process_data_task.delay(data.dict())  # Celery task
    return {"status": "processing", "task_id": task.id}
```

### Not Handling Task Failures

```python
# WRONG - silent failures
def send_email(email: str, content: str):
    smtp.send(email, content)  # What if this fails?

@router.post("/notify")
async def notify(background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, "user@example.com", "Hello")
    return {"status": "sent"}


# CORRECT - handle failures with retries and logging
import logging

logger = logging.getLogger(__name__)

def send_email_with_retry(email: str, content: str, retries: int = 3):
    for attempt in range(retries):
        try:
            smtp.send(email, content)
            return
        except Exception as e:
            logger.warning(f"Email attempt {attempt + 1} failed: {e}")
            if attempt == retries - 1:
                logger.error(f"Failed to send email to {email} after {retries} attempts")
                # Could also store failure for retry later
```

---

## 6. Validation Gotchas

### Not Validating Query Parameters

```python
# WRONG - unbounded pagination
@router.get("/items")
async def get_items(page: int = 1, per_page: int = 20):
    # User can request per_page=1000000!
    return await fetch_items(page, per_page)

# CORRECT - constrain query parameters
@router.get("/items")
async def get_items(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100)
):
    return await fetch_items(page, per_page)
```

### Schema Doesn't Match Model

```python
# WRONG - schema allows fields model doesn't have
class UserCreate(BaseModel):
    email: str
    password: str
    is_admin: bool = False  # User can set themselves as admin!

@router.post("/users")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = User(**user.dict())  # is_admin gets set!
    ...


# CORRECT - separate schemas for different contexts
class UserCreate(BaseModel):
    email: str
    password: str
    # No is_admin field

class AdminUserCreate(UserCreate):
    is_admin: bool = False
    # Only used by admin endpoints
```

---

## 7. Error Handling Issues

### Catching Too Broadly

```python
# WRONG - swallowing all exceptions
@router.get("/data")
async def get_data():
    try:
        return await fetch_data()
    except:
        return {"error": "Something went wrong"}

# Hides actual bugs, makes debugging impossible

# CORRECT - catch specific exceptions
@router.get("/data")
async def get_data():
    try:
        return await fetch_data()
    except DataNotFoundError:
        raise HTTPException(404, "Data not found")
    except ValidationError as e:
        raise HTTPException(400, str(e))
    # Let unexpected errors propagate to global handler
```

### Not Re-raising in Middleware

```python
# WRONG - middleware swallows exceptions
@app.middleware("http")
async def log_requests(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Error: {e}")
        return JSONResponse({"error": "Internal error"}, status_code=500)

# Client gets 500, but original exception context is lost

# CORRECT - log and re-raise
@app.middleware("http")
async def log_requests(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception:
        logger.exception("Unhandled exception")
        raise  # Let global exception handler deal with it
```

---

## 8. Testing Pitfalls

### Not Isolating Tests

```python
# WRONG - tests share database state
@pytest.fixture
def db():
    return SessionLocal()  # Uses production database!

def test_create_user(db):
    user = create_user(db, "test@example.com")
    assert user.email == "test@example.com"
    # User persists in database after test!


# CORRECT - use test database with rollback
@pytest.fixture
async def db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        async with session.begin():
            yield session
            await session.rollback()  # Rollback after test

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

### Not Testing Error Cases

```python
# WRONG - only testing happy path
def test_create_user(client):
    response = client.post("/users", json={"email": "test@example.com"})
    assert response.status_code == 201


# CORRECT - test error cases too
def test_create_user_success(client):
    response = client.post("/users", json={"email": "test@example.com", "password": "SecurePass123"})
    assert response.status_code == 201

def test_create_user_invalid_email(client):
    response = client.post("/users", json={"email": "not-an-email", "password": "SecurePass123"})
    assert response.status_code == 422

def test_create_user_duplicate_email(client, existing_user):
    response = client.post("/users", json={"email": existing_user.email, "password": "SecurePass123"})
    assert response.status_code == 409

def test_create_user_unauthorized(client):
    response = client.post("/admin/users", json={"email": "test@example.com"})
    assert response.status_code == 401
```

---

## 9. Performance Issues

### Loading Too Much Data

```python
# WRONG - loading all records
@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()  # Could be millions!

# CORRECT - always paginate
@router.get("/users")
async def get_users(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * per_page
    result = await db.execute(
        select(User)
        .offset(offset)
        .limit(per_page)
    )
    return result.scalars().all()
```

### Not Using Connection Pooling

```python
# WRONG - new connection per request
async def get_db():
    engine = create_async_engine(DATABASE_URL)  # New engine each time!
    async with AsyncSession(engine) as session:
        yield session


# CORRECT - reuse engine with connection pool
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with async_session_maker() as session:
        yield session
```

---

## Quick Reference

| Problem | Solution |
|---------|----------|
| Blocking event loop | Use async libraries (httpx, aiofiles) |
| Forgot await | Always await async operations |
| N+1 queries | Use joinedload/selectinload |
| Session issues | Scoped session per request |
| Mutable defaults | Use None or Query() |
| Exposing data | Use response_model |
| Long background tasks | Use Celery/task queue |
| Unbounded queries | Always paginate |
| Broad exception catch | Catch specific exceptions |
| Shared test state | Use rollback fixtures |
