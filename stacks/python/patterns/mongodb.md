# MongoDB Patterns (Python + PyMongo / Motor)

## PyMongo Document Model

```python
# models/user.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId

class PyObjectId(str):
    """Custom ObjectId type for Pydantic models."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

class UserModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    email: EmailStr
    name: str
    role: str = "user"
    settings: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    model_config = {"populate_by_name": True}
```

## Database Setup

```python
# db/mongodb.py
from pymongo import MongoClient
from pymongo.database import Database
import os

def get_database() -> Database:
    client = MongoClient(os.environ["MONGODB_URI"])
    return client[os.environ.get("DATABASE_NAME", "myapp")]

# Async variant with Motor
from motor.motor_asyncio import AsyncIOMotorClient

async def get_async_database():
    client = AsyncIOMotorClient(os.environ["MONGODB_URI"])
    return client[os.environ.get("DATABASE_NAME", "myapp")]
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
from bson import ObjectId
from pymongo.database import Database

class UserService:
    def __init__(self, db: Database):
        self.collection = db.users

    def create(self, data: dict) -> str:
        data["created_at"] = datetime.utcnow()
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def get_by_id(self, user_id: str) -> dict | None:
        return self.collection.find_one({"_id": ObjectId(user_id)})

    def get_by_email(self, email: str) -> dict | None:
        return self.collection.find_one({"email": email})

    def update(self, user_id: str, data: dict) -> bool:
        data["updated_at"] = datetime.utcnow()
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
from datetime import timedelta

one_week_ago = datetime.utcnow() - timedelta(weeks=1)
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

## Key Rules

1. Use indexes on frequently queried fields
2. Use embedded documents for 1:1 and 1:few relationships
3. Use references (ObjectId) for 1:many with large sets
4. Always use `ObjectId` for `_id` field operations
5. Use aggregation pipeline for complex queries
6. Use `$set` for partial updates, not full document replacement
7. Validate data with Pydantic before inserting
