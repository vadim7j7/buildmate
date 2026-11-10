# MongoDB Patterns (Go + Official Driver v2)

Use the official driver **v2**: module `go.mongodb.org/mongo-driver/v2`
(`go get go.mongodb.org/mongo-driver/v2`). Do not mix in v1 imports
(`go.mongodb.org/mongo-driver/...` without `/v2`, `bson/primitive`): v1 is in
maintenance mode and its types do not interoperate with v2.

What changed from v1, in short:
- Every import path gains `/v2`: `.../v2/bson`, `.../v2/mongo`, `.../v2/mongo/options`.
- `primitive.ObjectID` is now `bson.ObjectID` (`bson.NewObjectID()`, `bson.ObjectIDFromHex()`);
  the `bson/primitive` package is gone (`primitive.M`/`D`/`A` are `bson.M`/`D`/`A`).
- `mongo.Connect(opts...)` takes no context; connecting is lazy, so `Ping` to fail fast.
- Option constructors (`options.Find()`, `options.Index()`, ...) return builders; pass them
  straight to the collection method as before.

## Model Definition

```go
// models/user.go
package models

import (
	"time"

	"go.mongodb.org/mongo-driver/v2/bson"
)

type User struct {
	ID        bson.ObjectID  `bson:"_id,omitempty" json:"id"`
	Email     string         `bson:"email" json:"email"`
	Name      string         `bson:"name" json:"name"`
	Role      string         `bson:"role" json:"role"`
	Settings  map[string]any `bson:"settings,omitempty" json:"settings,omitempty"`
	Tags      []string       `bson:"tags,omitempty" json:"tags,omitempty"`
	Addresses []Address      `bson:"addresses,omitempty" json:"addresses,omitempty"`
	CreatedAt time.Time      `bson:"created_at" json:"created_at"`
	UpdatedAt time.Time      `bson:"updated_at" json:"updated_at"`
}

type Address struct {
	Street  string `bson:"street" json:"street"`
	City    string `bson:"city" json:"city"`
	Zip     string `bson:"zip" json:"zip"`
	Primary bool   `bson:"primary" json:"primary"`
}
```

## Database Setup

```go
// db/mongodb.go
package db

import (
	"context"
	"fmt"
	"os"
	"time"

	"go.mongodb.org/mongo-driver/v2/mongo"
	"go.mongodb.org/mongo-driver/v2/mongo/options"
	"go.mongodb.org/mongo-driver/v2/mongo/readpref"
)

// Connect creates a client and pings the primary so a bad URI fails at startup.
// Call client.Disconnect(ctx) on shutdown.
func Connect(ctx context.Context) (*mongo.Client, error) {
	opts := options.Client().
		ApplyURI(os.Getenv("MONGODB_URI")).
		SetMaxPoolSize(10).
		SetServerSelectionTimeout(5 * time.Second)

	client, err := mongo.Connect(opts) // v2: no context argument
	if err != nil {
		return nil, fmt.Errorf("mongo connect: %w", err)
	}

	if err := client.Ping(ctx, readpref.Primary()); err != nil {
		_ = client.Disconnect(ctx)
		return nil, fmt.Errorf("mongo ping: %w", err)
	}

	return client, nil
}

func GetDatabase(client *mongo.Client) *mongo.Database {
	dbName := os.Getenv("DATABASE_NAME")
	if dbName == "" {
		dbName = "myapp"
	}
	return client.Database(dbName)
}
```

## Index Creation

```go
// db/indexes.go
package db

import (
	"context"

	"go.mongodb.org/mongo-driver/v2/bson"
	"go.mongodb.org/mongo-driver/v2/mongo"
	"go.mongodb.org/mongo-driver/v2/mongo/options"
)

func CreateIndexes(ctx context.Context, db *mongo.Database) error {
	users := db.Collection("users")

	indexes := []mongo.IndexModel{
		{
			Keys:    bson.D{{Key: "email", Value: 1}},
			Options: options.Index().SetUnique(true),
		},
		{Keys: bson.D{{Key: "role", Value: 1}}},
		{Keys: bson.D{{Key: "created_at", Value: -1}}},
	}

	_, err := users.Indexes().CreateMany(ctx, indexes)
	return err
}
```

## Repository Pattern

```go
// repository/user_repository.go
package repository

import (
	"context"
	"errors"
	"fmt"
	"time"

	"go.mongodb.org/mongo-driver/v2/bson"
	"go.mongodb.org/mongo-driver/v2/mongo"
	"go.mongodb.org/mongo-driver/v2/mongo/options"

	"example.com/myapp/internal/apperror"
)

type UserRepository struct {
	collection *mongo.Collection
}

func NewUserRepository(db *mongo.Database) *UserRepository {
	return &UserRepository{collection: db.Collection("users")}
}

func (r *UserRepository) Create(ctx context.Context, user *User) error {
	now := time.Now().UTC()
	user.ID = bson.NewObjectID()
	user.CreatedAt = now
	user.UpdatedAt = now

	if _, err := r.collection.InsertOne(ctx, user); err != nil {
		if mongo.IsDuplicateKeyError(err) {
			return fmt.Errorf("email taken: %w", apperror.ErrValidation)
		}
		return fmt.Errorf("insert user: %w", err)
	}
	return nil
}

func (r *UserRepository) GetByID(ctx context.Context, id bson.ObjectID) (*User, error) {
	var user User
	err := r.collection.FindOne(ctx, bson.M{"_id": id}).Decode(&user)
	if errors.Is(err, mongo.ErrNoDocuments) {
		return nil, apperror.ErrNotFound
	}
	if err != nil {
		return nil, fmt.Errorf("find user %s: %w", id.Hex(), err)
	}
	return &user, nil
}

func (r *UserRepository) GetByEmail(ctx context.Context, email string) (*User, error) {
	var user User
	err := r.collection.FindOne(ctx, bson.M{"email": email}).Decode(&user)
	if errors.Is(err, mongo.ErrNoDocuments) {
		return nil, apperror.ErrNotFound
	}
	if err != nil {
		return nil, fmt.Errorf("find user by email: %w", err)
	}
	return &user, nil
}

// UpdateFields sets only known fields; never pass a client-supplied map as the update.
func (r *UserRepository) UpdateFields(ctx context.Context, id bson.ObjectID, name, role string) error {
	res, err := r.collection.UpdateOne(ctx,
		bson.M{"_id": id},
		bson.M{"$set": bson.M{"name": name, "role": role, "updated_at": time.Now().UTC()}},
	)
	if err != nil {
		return fmt.Errorf("update user: %w", err)
	}
	if res.MatchedCount == 0 {
		return apperror.ErrNotFound
	}
	return nil
}

func (r *UserRepository) Delete(ctx context.Context, id bson.ObjectID) error {
	res, err := r.collection.DeleteOne(ctx, bson.M{"_id": id})
	if err != nil {
		return fmt.Errorf("delete user: %w", err)
	}
	if res.DeletedCount == 0 {
		return apperror.ErrNotFound
	}
	return nil
}

func (r *UserRepository) ListByRole(ctx context.Context, role string, skip, limit int64) ([]User, error) {
	opts := options.Find().
		SetSkip(skip).
		SetLimit(limit).
		SetSort(bson.D{{Key: "created_at", Value: -1}})

	cursor, err := r.collection.Find(ctx, bson.M{"role": role}, opts)
	if err != nil {
		return nil, fmt.Errorf("find users: %w", err)
	}
	defer cursor.Close(ctx)

	users := []User{}
	if err := cursor.All(ctx, &users); err != nil {
		return nil, fmt.Errorf("decode users: %w", err)
	}
	return users, nil
}
```

## IDs From Requests

```go
// Parse the path ID at the edge; an invalid hex string is a 400, not a 500.
id, err := bson.ObjectIDFromHex(idParam)
if err != nil {
	return fmt.Errorf("invalid id: %w", apperror.ErrValidation)
}
```

## Querying

```go
// Complex filter
oneWeekAgo := time.Now().UTC().AddDate(0, 0, -7)
filter := bson.M{
	"role":       "user",
	"created_at": bson.M{"$gte": oneWeekAgo},
	"tags":       bson.M{"$in": bson.A{"go"}},
}
opts := options.Find().
	SetSort(bson.D{{Key: "created_at", Value: -1}}).
	SetLimit(10)
cursor, err := collection.Find(ctx, filter, opts)
if err != nil {
	return fmt.Errorf("find recent users: %w", err)
}
defer cursor.Close(ctx)

// Embedded document field
cursor, err = collection.Find(ctx, bson.M{"addresses.city": "NYC"})

// Count (use EstimatedDocumentCount only when an approximate total is fine)
total, err := collection.CountDocuments(ctx, bson.M{"role": "user"})
```

## Aggregation

```go
pipeline := mongo.Pipeline{
	{{Key: "$match", Value: bson.M{"role": "user"}}},
	{{Key: "$group", Value: bson.M{
		"_id":   "$organization",
		"count": bson.M{"$sum": 1},
	}}},
	{{Key: "$sort", Value: bson.D{{Key: "count", Value: -1}}}},
}
cursor, err := collection.Aggregate(ctx, pipeline)
if err != nil {
	return fmt.Errorf("aggregate users: %w", err)
}
defer cursor.Close(ctx)
```

## Key Rules

1. Import only `go.mongodb.org/mongo-driver/v2/...`; never mix v1 packages in
2. Pass a `context.Context` with a deadline to every operation
3. Use `bson.M` for unordered filters, `bson.D` where order matters (index keys, sort)
4. Use `bson.ObjectID` for ID fields; parse request IDs with `bson.ObjectIDFromHex` and return 400 on error
5. Check `errors.Is(err, mongo.ErrNoDocuments)` after `FindOne` and map it to a domain `ErrNotFound`
6. Always `defer cursor.Close(ctx)` and check every returned error
7. Build filters and updates from typed values; never decode request JSON into `bson.M`
   and pass it through (operator injection such as `{"$ne": null}`)
8. Keep collection access inside repositories; create indexes at startup
9. Use `$set` with explicit fields for partial updates; map `mongo.IsDuplicateKeyError` to a validation error
