# MongoDB Patterns (Python + PyMongo, sync and async)

Use **PyMongo** for both styles: `MongoClient` (sync) and `AsyncMongoClient` (async,
PyMongo 4.13+). Motor is deprecated by MongoDB in favour of the PyMongo Async API — do
not add it to new code. Models use the Pydantic v2 API and timezone-aware datetimes.

## PyMongo Document Model (Pydantic v2)

```python
# models/user.py
from datetime import UTC, datetime
from typing import Annotated

from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, ConfigDict, EmailStr, Field


def _validate_object_id(value: object) -> str:
    """Accept an ObjectId or its 24-char hex string; store it as a string."""
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, str) and ObjectId.is_valid(value):
        return value
    raise ValueError("Invalid ObjectId")


# Pydantic v2: Annotated + BeforeValidator (`__get_validators__` is Pydantic v1 only).
# With Beanie, use `beanie.PydanticObjectId` instead.
PyObjectId = Annotated[str, BeforeValidator(_validate_object_id)]


def utc_now() -> datetime:
    return datetime.now(UTC)


class UserModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId | None = Field(default=None, alias="_id")
    email: EmailStr
    name: str
    role: str = "user"
    settings: dict[str, object] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime | None = None
```

## Database Setup

```python
# db/mongodb.py
import os

from pymongo import AsyncMongoClient, MongoClient
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.database import Database

MONGODB_URI = os.environ["MONGODB_URI"]
DATABASE_NAME = os.environ.get("DATABASE_NAME", "myapp")

# Create ONE client per process and reuse it (it holds the connection pool).
# tz_aware=True returns timezone-aware datetimes from the database.
sync_client: MongoClient = MongoClient(MONGODB_URI, tz_aware=True)
async_client: AsyncMongoClient = AsyncMongoClient(MONGODB_URI, tz_aware=True)


def get_database() -> Database:
    return sync_client[DATABASE_NAME]


def get_async_database() -> AsyncDatabase:
    return async_client[DATABASE_NAME]

# Async: `await async_client.close()` on shutdown (e.g. in the app lifespan).
```

## Index Creation

```python
# db/indexes.py
from pymongo import ASCENDING, DESCENDING

def create_indexes(db):
    db.users.create_index("email", unique=True)
    db.users.create_index("role")
    db.users.create_index([("created_at", DESCENDING)])
    db.users.create_index([("tags", ASCENDING)])
```

## CRUD Operations

```python
# services/user_service.py
from datetime import UTC, datetime

from bson import ObjectId
from pymongo.database import Database

class UserService:
    def __init__(self, db: Database):
        self.collection = db.users

    def create(self, data: dict) -> str:
        data["created_at"] = datetime.now(UTC)
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def get_by_id(self, user_id: str) -> dict | None:
        return self.collection.find_one({"_id": ObjectId(user_id)})

    def get_by_email(self, email: str) -> dict | None:
        return self.collection.find_one({"email": email})

    def update(self, user_id: str, data: dict) -> bool:
        data["updated_at"] = datetime.now(UTC)
        result = self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": data},
        )
        return result.modified_count > 0

    def delete(self, user_id: str) -> bool:
        result = self.collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0
```

## Querying

```python
# Basic queries
users = list(db.users.find({"role": "admin"}))

# Complex queries
from datetime import UTC, datetime, timedelta

one_week_ago = datetime.now(UTC) - timedelta(weeks=1)
users = list(
    db.users.find({
        "role": "user",
        "created_at": {"$gte": one_week_ago},
        "tags": {"$in": ["python"]},
    })
    .sort("created_at", -1)
    .limit(10)
)

# Embedded document queries
users = list(db.users.find({"addresses.city": "NYC"}))

# Pagination
skip = page * limit
users = list(db.users.find().skip(skip).limit(limit))
total = db.users.count_documents({})
```

## Aggregation

```python
# Aggregation pipeline
pipeline = [
    {"$match": {"role": "user"}},
    {"$group": {"_id": "$organization", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
]
results = list(db.users.aggregate(pipeline))
```

## Async CRUD (PyMongo Async API)

```python
from pymongo.asynchronous.database import AsyncDatabase


class AsyncUserService:
    def __init__(self, db: AsyncDatabase) -> None:
        self.collection = db.users

    async def get_by_email(self, email: str) -> dict | None:
        return await self.collection.find_one({"email": email})

    async def list_admins(self, limit: int = 10) -> list[dict]:
        cursor = self.collection.find({"role": "admin"}).limit(limit)
        return await cursor.to_list()
```

## Key Rules

1. Use indexes on frequently queried fields
2. Use embedded documents for 1:1 and 1:few relationships
3. Use references (ObjectId) for 1:many with large sets
4. Always use `ObjectId` for `_id` field operations
5. Use aggregation pipeline for complex queries
6. Use `$set` for partial updates, not full document replacement
7. Validate data with Pydantic v2 before inserting
8. Store timezone-aware UTC datetimes (`datetime.now(UTC)`, `tz_aware=True`)
9. Async code uses `AsyncMongoClient` from `pymongo`, not Motor
