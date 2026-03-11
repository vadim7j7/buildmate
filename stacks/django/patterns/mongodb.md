# Django + MongoDB Patterns (Djongo)

## Database Configuration

Configure `DATABASES` in `settings.py` to use Djongo as the engine:

```python
DATABASES = {
    "default": {
        "ENGINE": "djongo",
        "NAME": "your_database_name",
        "CLIENT": {
            "host": "mongodb://localhost:27017",
        },
    }
}
```

For MongoDB Atlas or authenticated connections:

```python
DATABASES = {
    "default": {
        "ENGINE": "djongo",
        "NAME": "your_database_name",
        "CLIENT": {
            "host": "mongodb+srv://<user>:<password>@cluster.mongodb.net",
            "username": "your_username",
            "password": "your_password",
            "authMechanism": "SCRAM-SHA-1",
        },
    }
}
```

## Model Definitions

### Supported Field Types

Djongo supports most standard Django fields. Prefer simple field types for broadest compatibility:

```python
from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    # NOTE: auto_now=True is NOT supported — use signals or save() override instead
    updated_at = models.DateTimeField(null=True, blank=True)
    view_count = models.IntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
```

### Embedded Documents (Djongo-specific)

Djongo supports embedded subdocuments via `EmbeddedField`:

```python
from django.db import models
from djongo import models as djongo_models

class Address(djongo_models.Model):
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    class Meta:
        abstract = True  # Required for embedded documents

class Customer(djongo_models.Model):
    name = models.CharField(max_length=200)
    address = djongo_models.EmbeddedField(model_container=Address)
```

### ArrayField for Lists

```python
from djongo import models as djongo_models

class Post(djongo_models.Model):
    title = models.CharField(max_length=200)
    tags = djongo_models.ArrayField(model_container=str)
```

## Known Limitations

### Unsupported Features

- `auto_now=True` on `DateTimeField` / `DateField` — use `save()` override or `pre_save` signal:

```python
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

@receiver(pre_save, sender=MyModel)
def set_updated_at(sender, instance, **kwargs):
    instance.updated_at = timezone.now()
```

- `ManyToManyField` — not supported by Djongo. Use `ArrayField` of IDs or a separate junction model with references:

```python
# Instead of ManyToManyField, store related IDs as an array
class Post(djongo_models.Model):
    title = models.CharField(max_length=200)
    tag_ids = djongo_models.ArrayField(model_container=int)
```

- Complex `JOIN`-based queries (e.g., `select_related` across collections) may not work. Use `prefetch_related` or fetch separately.

- Django's built-in `contenttypes` framework and some third-party packages relying on raw SQL may not be compatible.

### Migration Limitations

Djongo translates Django migrations into MongoDB operations. Keep migrations simple:

- Avoid `RunSQL` migrations
- Column renames may not propagate correctly; prefer adding new fields and migrating data manually
- Always test migrations on a staging database before production

## Using pymongo Directly

For queries that Djongo cannot handle, use `pymongo` directly alongside the Django ORM:

```python
from pymongo import MongoClient
from django.conf import settings

def get_mongo_collection(collection_name: str):
    db_settings = settings.DATABASES["default"]
    client = MongoClient(db_settings["CLIENT"]["host"])
    db = client[db_settings["NAME"]]
    return db[collection_name]

# Raw aggregation pipeline
def get_top_articles(limit: int = 10):
    collection = get_mongo_collection("myapp_article")
    pipeline = [
        {"$match": {"published": True}},
        {"$sort": {"view_count": -1}},
        {"$limit": limit},
    ]
    return list(collection.aggregate(pipeline))
```

## DRF Serializers with MongoDB Models

Standard DRF serializers work with Djongo models:

```python
from rest_framework import serializers
from .models import Article

class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "title", "body", "published", "created_at"]
        read_only_fields = ["id", "created_at"]
```

## Admin Configuration

Register models as usual; most admin features work with Djongo:

```python
from django.contrib import admin
from .models import Article

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "published", "created_at"]
    list_filter = ["published"]
    search_fields = ["title", "body"]
```

## Dependencies

Add to `requirements.txt` or `pyproject.toml`:

```
djongo>=1.3.6
pymongo>=3.12,<4.0  # Djongo requires pymongo 3.x
dnspython>=2.0      # Required for mongodb+srv:// URIs
```

Note: Djongo currently requires `pymongo<4.0`. Check the [Djongo releases](https://github.com/doableware/djongo) for updated compatibility.
