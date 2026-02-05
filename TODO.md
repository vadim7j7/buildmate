# Agents Bootstrap - Feature Roadmap

## Current State

### Stacks

| Stack | Status | Options |
|-------|--------|---------|
| `rails` | Done | `--jobs`, `--db` |
| `nextjs` | Done | `--ui`, `--state` |
| `react-native` | Done | `--state` |
| `fastapi` | Done | `--db` |

### Stack Options

#### Rails
| Option | Choices | Status |
|--------|---------|--------|
| `--jobs` | sidekiq, good_job, solid_queue, active_job | Done |
| `--db` | postgresql, mysql, sqlite, mongodb | Done |

#### Next.js
| Option | Choices | Status |
|--------|---------|--------|
| `--ui` | mantine, tailwind, shadcn, chakra, mui, antd | Done |
| `--state` | zustand, redux, mobx, jotai, context, none | Done |

#### React Native
| Option | Choices | Status |
|--------|---------|--------|
| `--state` | zustand, mobx, redux, jotai, none | Done |

#### FastAPI
| Option | Choices | Status |
|--------|---------|--------|
| `--db` | postgresql, mysql, sqlite, mongodb | Done |

### Profiles

| Profile | Stacks | Status |
|---------|--------|--------|
| `landing` | nextjs (tailwind, no state) | Done |
| `saas` | rails + nextjs (full config) | Done |
| `api-only` | rails | Done |
| `mobile-backend` | fastapi + react-native | Done |

---

## Planned Features

### Priority 1: Authentication Options

#### Rails `--auth`
- [ ] `devise` - Most popular Rails auth (default)
- [ ] `rodauth` - Modern, secure authentication
- [ ] `clearance` - Simple, opinionated auth
- [ ] `none` - No authentication

**Files needed:**
- `stacks/rails/patterns/devise.md`
- `stacks/rails/patterns/rodauth.md`
- `stacks/rails/patterns/clearance.md`
- `stacks/rails/skills/new-auth/` (optional)

#### Next.js `--auth`
- [ ] `next-auth` - NextAuth.js (default)
- [ ] `clerk` - Drop-in auth UI
- [ ] `auth0` - Auth0 integration
- [ ] `none` - No authentication

**Files needed:**
- `stacks/nextjs/patterns/next-auth.md`
- `stacks/nextjs/patterns/clerk.md`
- `stacks/nextjs/patterns/auth0.md`

#### React Native `--auth`
- [ ] `expo-auth-session` - Expo auth (default)
- [ ] `clerk` - Clerk React Native
- [ ] `none` - No authentication

**Files needed:**
- `stacks/react-native/patterns/expo-auth.md`
- `stacks/react-native/patterns/clerk-rn.md`

#### FastAPI `--auth`
- [ ] `jwt` - JWT tokens (default)
- [ ] `oauth2` - OAuth2 with fastapi-users
- [ ] `none` - No authentication

**Files needed:**
- `stacks/fastapi/patterns/jwt-auth.md`
- `stacks/fastapi/patterns/oauth2.md`

---

### Priority 2: Forms & Validation

#### Next.js `--forms`
- [ ] `react-hook-form` - Popular form library (default)
- [ ] `formik` - Alternative form library
- [ ] `none` - No form library

**Files needed:**
- `stacks/nextjs/patterns/react-hook-form.md`
- `stacks/nextjs/patterns/formik.md`
- `stacks/nextjs/skills/new-form/` - Update to use selected library

---

### Priority 3: Data Fetching

#### Next.js `--fetch`
- [ ] `tanstack-query` - TanStack Query (default, already used)
- [ ] `swr` - Stale-while-revalidate
- [ ] `none` - Plain fetch

**Files needed:**
- `stacks/nextjs/patterns/tanstack-query.md`
- `stacks/nextjs/patterns/swr.md`

---

### Priority 4: API Serialization

#### Rails `--api`
- [ ] `jbuilder` - Rails default JSON builder
- [ ] `alba` - Fast, flexible serializer
- [ ] `blueprinter` - Simple, fast serializer
- [ ] `jsonapi` - JSON:API spec serializer

**Files needed:**
- `stacks/rails/patterns/jbuilder.md`
- `stacks/rails/patterns/alba.md`
- `stacks/rails/patterns/blueprinter.md`
- `stacks/rails/patterns/jsonapi-serializer.md`

---

### Priority 5: Search

#### Rails `--search`
- [ ] `ransack` - Simple search/filtering (default)
- [ ] `pg_search` - PostgreSQL full-text search
- [ ] `meilisearch` - MeiliSearch integration
- [ ] `elasticsearch` - Elasticsearch integration
- [ ] `none` - No search

**Files needed:**
- `stacks/rails/patterns/ransack.md`
- `stacks/rails/patterns/pg_search.md`
- `stacks/rails/patterns/meilisearch.md`
- `stacks/rails/patterns/elasticsearch.md`

---

### Priority 6: Caching

#### Rails `--cache`
- [ ] `redis` - Redis cache (default)
- [ ] `memcached` - Memcached
- [ ] `solid_cache` - Database-backed cache (Rails 8+)

**Files needed:**
- `stacks/rails/patterns/redis-cache.md`
- `stacks/rails/patterns/solid_cache.md`

#### FastAPI `--cache`
- [ ] `redis` - Redis cache (default)
- [ ] `memcached` - Memcached
- [ ] `none` - No caching

**Files needed:**
- `stacks/fastapi/patterns/redis-cache.md`

---

### Priority 7: Background Tasks

#### FastAPI `--tasks`
- [ ] `celery` - Celery task queue (default)
- [ ] `arq` - Async Redis queue
- [ ] `taskiq` - Modern async task queue
- [ ] `none` - No background tasks

**Files needed:**
- `stacks/fastapi/patterns/celery.md`
- `stacks/fastapi/patterns/arq.md`
- `stacks/fastapi/patterns/taskiq.md`

---

### Priority 8: File Uploads

#### Rails `--uploads`
- [ ] `active_storage` - Rails built-in (default)
- [ ] `shrine` - Flexible file attachment
- [ ] `carrierwave` - Classic uploader

**Files needed:**
- `stacks/rails/patterns/active_storage.md`
- `stacks/rails/patterns/shrine.md`
- `stacks/rails/patterns/carrierwave.md`

---

### Priority 9: Mobile-Specific Options

#### React Native `--storage`
- [ ] `async-storage` - React Native Async Storage (default)
- [ ] `mmkv` - Fast key-value storage

**Files needed:**
- `stacks/react-native/patterns/async-storage.md`
- `stacks/react-native/patterns/mmkv.md`

#### React Native `--push`
- [ ] `expo-notifications` - Expo push (default)
- [ ] `onesignal` - OneSignal
- [ ] `none` - No push notifications

**Files needed:**
- `stacks/react-native/patterns/expo-notifications.md`
- `stacks/react-native/patterns/onesignal.md`

#### React Native `--analytics`
- [ ] `amplitude` - Amplitude analytics
- [ ] `mixpanel` - Mixpanel analytics
- [ ] `none` - No analytics (default)

**Files needed:**
- `stacks/react-native/patterns/amplitude.md`
- `stacks/react-native/patterns/mixpanel.md`

---

### Priority 10: Testing Options

#### Next.js `--testing`
- [ ] `jest` - Jest + RTL (default)
- [ ] `vitest` - Vitest + RTL
- [ ] `playwright` - Playwright E2E

**Files needed:**
- `stacks/nextjs/patterns/vitest.md`
- `stacks/nextjs/patterns/playwright.md`

---

## Planned Profiles

| Profile | Stacks | Options | Priority | Status |
|---------|--------|---------|----------|--------|
| `blog` | nextjs | ui=tailwind, state=none | High | [ ] |
| `startup` | rails + nextjs | auth=devise, ui=shadcn, jobs=sidekiq | High | [ ] |
| `ecommerce` | rails + nextjs | auth=devise, db=postgresql | Medium | [ ] |
| `admin` | rails + nextjs | auth=devise, ui=mantine | Medium | [ ] |
| `realtime` | rails + nextjs | cache=redis, jobs=sidekiq | Medium | [ ] |
| `microservice` | fastapi | db=postgresql, tasks=celery | Medium | [ ] |
| `mobile-only` | react-native | state=zustand, push=expo-notifications | Medium | [ ] |
| `enterprise` | rails + nextjs | auth=devise, ui=antd, search=meilisearch | Low | [ ] |

---

## Planned New Stacks

| Stack | Description | Priority | Status |
|-------|-------------|----------|--------|
| `django` | Python Django backend | Low | [ ] |
| `nestjs` | Node.js NestJS backend | Low | [ ] |
| `flutter` | Flutter/Dart mobile | Low | [ ] |
| `go-fiber` | Go Fiber backend | Low | [ ] |

---

## Infrastructure Improvements

### Testing
- [x] Basic tests for stack loading
- [x] Tests for options and profiles
- [x] Content validation tests
- [ ] Integration tests with actual bootstrap
- [ ] E2E tests that verify generated output works

### Documentation
- [x] README.md with usage
- [x] CLAUDE.md with architecture
- [ ] Contribution guide
- [ ] Stack authoring guide
- [ ] Option/profile authoring guide

### CLI
- [x] `--list` - List stacks
- [x] `--profiles` - List profiles
- [x] `--options <stack>` - Show stack options
- [x] `--validate <stack>` - Validate stack config
- [x] `--dry-run` - Preview without writing
- [ ] `--interactive` - Interactive mode with prompts
- [ ] `--upgrade` - Upgrade existing .claude/ directory

### Features
- [x] Stack composition (multi-stack)
- [x] Stack options
- [x] Profiles
- [ ] Custom variables via CLI (`--var key=value`)
- [ ] Local overrides (`~/.agents/overrides/`)
- [ ] Plugin system for custom stacks

---

## Changelog

### v2.0.0 (Current)
- Python + Jinja2 templating system
- YAML-driven stack configuration
- Stack options (ui, state, jobs, db)
- Profiles (landing, saas, api-only, mobile-backend)
- JSON Schema validation
- 137 tests with content validation

### v1.0.0 (Deprecated)
- Shell-based bootstrap
- Static file copying
- No options or profiles
