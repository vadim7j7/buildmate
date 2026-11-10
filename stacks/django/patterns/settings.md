# Django Settings and Production Checklist

Read when adding a setting, an environment variable, a new environment
(staging, test) or preparing a deploy. The base `config/settings.py` is in
`django-patterns.md` (section 5): secrets from the environment, no insecure
fallback.

## One File or Split Settings

Keep **one env-driven `config/settings.py`** while environments differ only in
values (hosts, database URL, debug). Split into a package only when they differ
in *code* (extra apps, middleware, logging handlers):

```
config/settings/
    __init__.py
    base.py         # everything shared
    local.py        # from .base import *; DEBUG tooling (debug-toolbar)
    production.py   # from .base import *; security settings below
    test.py         # from .base import *; fast hasher, in-memory email
```

`DJANGO_SETTINGS_MODULE=config.settings.production` in the deploy env;
`pyproject.toml` points pytest at `config.settings.test`. Never branch on
`if DEBUG:` to pick settings; that is what the modules are for.

## Reading the Environment

Plain `os.environ` is enough for a handful of values. With many typed values,
use `django-environ` (add the dep) for casting and `DATABASE_URL` parsing:

```python
# config/settings/base.py
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()
# Local only: read .env if present (never commit it; production sets real env vars)
environ.Env.read_env(BASE_DIR / ".env", overwrite=False)

SECRET_KEY = env("DJANGO_SECRET_KEY")  # ImproperlyConfigured when unset
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
CACHES = {"default": env.cache("CACHE_URL", default="locmemcache://")}
```

Rules:
- Every new variable is documented in `.env.example` (name, example value, no secret).
- No default for secrets; a safe default (off, empty) for flags.
- Settings are read once at import; code reads `django.conf.settings`, never `os.environ`.
- PostgreSQL with psycopg 3 can use Django's connection pool
  (`"OPTIONS": {"pool": True}`, Django 5.1+) instead of `CONN_MAX_AGE`; not both.

## Test Settings

```python
# config/settings/test.py
from .base import *  # noqa: F403

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # fast
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = True  # only if the project uses Celery
```

## Production Settings

```python
# config/settings/production.py
from .base import *  # noqa: F403
from .base import env

DEBUG = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # behind a TLS proxy
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS")
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365  # start low (300) on first rollout
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
    },
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
```

Set `SECURE_PROXY_SSL_HEADER` only when the proxy strips and sets that header,
otherwise clients can spoof HTTPS.

## Deploy Checklist

Run in CI against the production settings and fix every warning (or silence it
with a comment explaining why, via `SILENCED_SYSTEM_CHECKS`):

```bash
DJANGO_SETTINGS_MODULE=config.settings.production uv run python manage.py check --deploy --fail-level WARNING
uv run python manage.py makemigrations --check --dry-run   # no missing migrations
```

Also before the first deploy:
- [ ] `DEBUG` is off and `SECRET_KEY` is long, random and only in the secret store
- [ ] `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` list the real domains
- [ ] `collectstatic` runs in the build; static files are served by the proxy/CDN or WhiteNoise
- [ ] Media uploads go to object storage (`STORAGES["default"]`), not the container disk
- [ ] `ADMINS`/error tracking set up; logs go to stdout
- [ ] Admin is on a non-default URL or behind SSO/VPN when exposed publicly
- [ ] Migrations run once per deploy (release step), not on every container start
