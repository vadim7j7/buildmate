# Django + MongoDB Patterns (django-mongodb-backend)

Use MongoDB's official backend, **django-mongodb-backend**. Its version follows
Django's: the `5.2.x` releases support Django 5.2 (`django-mongodb-backend>=5.2,<5.3`;
use `6.1.x` with Django 6.1). Do not use Djongo — it is unmaintained and does not
support Django 5.

## Project Setup

Start from MongoDB's project template for the matching Django line; it creates the
app configs and migrations below:

```bash
uv run django-admin startproject config \
  --template https://github.com/mongodb-labs/django-mongodb-project/archive/refs/heads/5.2.x.zip
```

## Settings

```python
# config/settings.py
import os

DATABASES = {
    "default": {
        "ENGINE": "django_mongodb_backend",
        "HOST": os.environ["MONGODB_URI"],  # mongodb://... or mongodb+srv://...
        "NAME": os.environ.get("MONGODB_DB", "app"),
    }
}

# MongoDB primary keys are ObjectIds
DEFAULT_AUTO_FIELD = "django_mongodb_backend.fields.ObjectIdAutoField"

INSTALLED_APPS = [
    # contrib apps replaced by ObjectId-keyed configs from the template's config/apps.py
    "config.apps.MongoAdminConfig",
    "config.apps.MongoAuthConfig",
    "config.apps.MongoContentTypesConfig",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_mongodb_backend",
    "rest_framework",
    # Local apps
    "projects",
]

# The contrib apps' migrations are regenerated for ObjectId keys
MIGRATION_MODULES = {
    "admin": "mongo_migrations.admin",
    "auth": "mongo_migrations.auth",
    "contenttypes": "mongo_migrations.contenttypes",
}
```

## Models

Regular Django models work; IDs are `ObjectId`s, so URLs and serializers treat `pk`
as a string (`<str:pk>`, `lookup_value_regex = "[0-9a-f]{24}"` on ViewSets).

```python
# projects/models.py
from django.conf import settings
from django.db import models
from django_mongodb_backend.fields import ArrayField, EmbeddedModelField
from django_mongodb_backend.models import EmbeddedModel


class Address(EmbeddedModel):
    """Stored inside the parent document, not in its own collection."""

    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)


class Customer(models.Model):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customers"
    )
    address = EmbeddedModelField(Address, null=True, blank=True)
    tags = ArrayField(models.CharField(max_length=50), default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name
```

## Rules

- Embed data that is read with its parent (1:1, 1:few) using `EmbeddedModelField`;
  use `ForeignKey` for independent entities
- Before relying on joins, transactions, `ManyToManyField` or a third-party app,
  check the backend's "Feature Compatibility" page for the installed version
- Raw aggregation pipelines: use the backend's raw-query support
  (`raw_aggregate()` on a `django_mongodb_backend.managers.MongoManager`; check the
  docs for your version) rather than opening a second `MongoClient`
- Create indexes in `Meta.indexes` and apply them with migrations
- Run `manage.py migrate` after `startproject` so the `mongo_migrations` apply

## Dependencies

```
django>=5.2,<5.3
django-mongodb-backend>=5.2,<5.3   # pulls in PyMongo 4.x
```
