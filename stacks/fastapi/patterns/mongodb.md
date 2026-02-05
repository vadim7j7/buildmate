# MongoDB Patterns (FastAPI + Motor + Beanie)

## Beanie Document Model

```python
# models/user.py
from beanie import Document, Indexed, Link
from pydantic import EmailStr, Field
from datetime import datetime
from typing import Optional

class User(Document):
    email: Indexed(EmailStr, unique=True)
    name: str
    role: str = "user"
    settings: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    # Reference to another document
    organization: Optional[Link["Organization"]] = None

    class Settings:
        name = "users"  # Collection name
        indexes = [
            "role",
            [("created_at", -1)],
        ]

    async def before_save(self):
        self.updated_at = datetime.utcnow()
```

## Embedded Documents

```python
# models/user.py
from beanie import Document
from pydantic import BaseModel

class Address(BaseModel):
    street: str
    city: str
    zip: str
    primary: bool = False

class User(Document):
    email: str
    name: str
    addresses: list[Address] = Field(default_factory=list)

    class Settings:
        name = "users"

# Usage
user = await User.find_one(User.email == "test@example.com")
user.addresses.append(Address(street="123 Main", city="NYC", zip="10001"))
await user.save()
```

## Database Setup

```python
# db/mongodb.py
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models.user import User
from models.post import Post

async def init_db():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[User, Post],
    )

# main.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)
```

## CRUD Operations

```python
# services/user_service.py
from models.user import User
from beanie import PydanticObjectId

class UserService:
    @staticmethod
    async def create(data: UserCreate) -> User:
        user = User(**data.model_dump())
        await user.insert()
        return user

    @staticmethod
    async def get_by_id(user_id: PydanticObjectId) -> User | None:
        return await User.get(user_id)

    @staticmethod
    async def get_by_email(email: str) -> User | None:
        return await User.find_one(User.email == email)

    @staticmethod
    async def update(user_id: PydanticObjectId, data: UserUpdate) -> User | None:
        user = await User.get(user_id)
        if not user:
            return None
        await user.update({"$set": data.model_dump(exclude_unset=True)})
        return await User.get(user_id)

    @staticmethod
    async def delete(user_id: PydanticObjectId) -> bool:
        user = await User.get(user_id)
        if not user:
            return False
        await user.delete()
        return True
```

## Querying

```python
# Basic queries
users = await User.find(User.role == "admin").to_list()

# Complex queries
from beanie.operators import In, GTE

users = await User.find(
    User.role == "user",
    GTE(User.created_at, one_week_ago),
    In(User.tags, ["python", "fastapi"]),
).sort(-User.created_at).limit(10).to_list()

# Embedded document queries
users = await User.find({"addresses.city": "NYC"}).to_list()

# Pagination
users = await User.find_all().skip(page * limit).limit(limit).to_list()
total = await User.count()
```

## Aggregation

```python
# Aggregation pipeline
pipeline = [
    {"$match": {"role": "user"}},
    {"$group": {"_id": "$organization", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
]
results = await User.aggregate(pipeline).to_list()
```

## Router with MongoDB

```python
# routers/users.py
from fastapi import APIRouter, HTTPException
from beanie import PydanticObjectId
from models.user import User
from schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse)
async def create_user(data: UserCreate):
    existing = await User.find_one(User.email == data.email)
    if existing:
        raise HTTPException(400, "Email already registered")
    user = User(**data.model_dump())
    await user.insert()
    return user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: PydanticObjectId):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user

@router.get("/", response_model=list[UserResponse])
async def list_users(skip: int = 0, limit: int = 20):
    return await User.find_all().skip(skip).limit(limit).to_list()
```

## Links (References)

```python
# Fetch with linked documents
user = await User.find_one(
    User.email == "test@example.com",
    fetch_links=True,  # Resolves organization link
)
print(user.organization.name)

# Or fetch links manually
user = await User.find_one(User.email == "test@example.com")
await user.fetch_link(User.organization)
```

## Key Rules

1. Use `Indexed()` for frequently queried fields
2. Use embedded documents for 1:1 and 1:few relationships
3. Use `Link[]` for references to other collections
4. Always use `PydanticObjectId` for ID parameters
5. Use Beanie operators (In, GTE, etc.) for type-safe queries
6. Initialize Beanie in app lifespan, not at import time
7. Use aggregation pipeline for complex queries
