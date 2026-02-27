# MongoDB Patterns (Go + Official Driver)

## Model Definition

```go
// models/user.go
package models

import (
	"time"

	"go.mongodb.org/mongo-driver/bson/primitive"
)

type User struct {
	ID           primitive.ObjectID `bson:"_id,omitempty" json:"id"`
	Email        string             `bson:"email" json:"email"`
	Name         string             `bson:"name" json:"name"`
	Role         string             `bson:"role" json:"role"`
	Settings     map[string]any     `bson:"settings,omitempty" json:"settings,omitempty"`
	Tags         []string           `bson:"tags,omitempty" json:"tags,omitempty"`
	CreatedAt    time.Time          `bson:"created_at" json:"created_at"`
	UpdatedAt    time.Time          `bson:"updated_at" json:"updated_at"`
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
	"os"
	"time"

	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

func Connect(ctx context.Context) (*mongo.Client, error) {
	uri := os.Getenv("MONGODB_URI")
	opts := options.Client().
		ApplyURI(uri).
		SetMaxPoolSize(10).
		SetServerSelectionTimeout(5 * time.Second)

	client, err := mongo.Connect(ctx, opts)
	if err != nil {
		return nil, err
	}

	if err := client.Ping(ctx, nil); err != nil {
		return nil, err
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

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

func CreateIndexes(ctx context.Context, db *mongo.Database) error {
	users := db.Collection("users")

	indexes := []mongo.IndexModel{
		{
			Keys:    bson.D{{Key: "email", Value: 1}},
			Options: options.Index().SetUnique(true),
		},
		{
			Keys: bson.D{{Key: "role", Value: 1}},
		},
		{
			Keys: bson.D{{Key: "created_at", Value: -1}},
		},
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
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

type UserRepository struct {
	collection *mongo.Collection
}

func NewUserRepository(db *mongo.Database) *UserRepository {
	return &UserRepository{
		collection: db.Collection("users"),
	}
}

func (r *UserRepository) Create(ctx context.Context, user *User) error {
	user.ID = primitive.NewObjectID()
	user.CreatedAt = time.Now()
	user.UpdatedAt = time.Now()

	_, err := r.collection.InsertOne(ctx, user)
	return err
}

func (r *UserRepository) GetByID(ctx context.Context, id primitive.ObjectID) (*User, error) {
	var user User
	err := r.collection.FindOne(ctx, bson.M{"_id": id}).Decode(&user)
	if err == mongo.ErrNoDocuments {
		return nil, nil
	}
	return &user, err
}

func (r *UserRepository) GetByEmail(ctx context.Context, email string) (*User, error) {
	var user User
	err := r.collection.FindOne(ctx, bson.M{"email": email}).Decode(&user)
	if err == mongo.ErrNoDocuments {
		return nil, nil
	}
	return &user, err
}

func (r *UserRepository) Update(ctx context.Context, id primitive.ObjectID, update bson.M) error {
	update["updated_at"] = time.Now()
	_, err := r.collection.UpdateOne(
		ctx,
		bson.M{"_id": id},
		bson.M{"$set": update},
	)
	return err
}

func (r *UserRepository) Delete(ctx context.Context, id primitive.ObjectID) error {
	_, err := r.collection.DeleteOne(ctx, bson.M{"_id": id})
	return err
}

func (r *UserRepository) List(ctx context.Context, filter bson.M, skip, limit int64) ([]*User, error) {
	opts := options.Find().
		SetSkip(skip).
		SetLimit(limit).
		SetSort(bson.D{{Key: "created_at", Value: -1}})

	cursor, err := r.collection.Find(ctx, filter, opts)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	var users []*User
	if err := cursor.All(ctx, &users); err != nil {
		return nil, err
	}
	return users, nil
}
```

## Querying

```go
// Basic queries
filter := bson.M{"role": "admin"}
cursor, _ := collection.Find(ctx, filter)

// Complex queries
oneWeekAgo := time.Now().AddDate(0, 0, -7)
filter = bson.M{
	"role":       "user",
	"created_at": bson.M{"$gte": oneWeekAgo},
	"tags":       bson.M{"$in": bson.A{"go"}},
}
opts := options.Find().
	SetSort(bson.D{{Key: "created_at", Value: -1}}).
	SetLimit(10)
cursor, _ = collection.Find(ctx, filter, opts)

// Embedded document queries
filter = bson.M{"addresses.city": "NYC"}
cursor, _ = collection.Find(ctx, filter)

// Count
total, _ := collection.CountDocuments(ctx, bson.M{})
```

## Aggregation

```go
pipeline := mongo.Pipeline{
	{{Key: "$match", Value: bson.M{"role": "user"}}},
	{{Key: "$group", Value: bson.M{
		"_id":   "$organization",
		"count": bson.M{"$sum": 1},
	}}},
	{{Key: "$sort", Value: bson.M{"count": -1}}},
}
cursor, _ := collection.Aggregate(ctx, pipeline)
```

## Key Rules

1. Always use `context.Context` for all MongoDB operations
2. Use `bson.M` for unordered filters, `bson.D` for ordered (indexes, sort)
3. Use `primitive.ObjectID` for ID fields, not strings
4. Check for `mongo.ErrNoDocuments` on `FindOne`
5. Always close cursors with `defer cursor.Close(ctx)`
6. Use the repository pattern to encapsulate collection access
7. Create indexes at application startup
8. Use `$set` for partial updates
