# /clone-site

Analyze an entire website and generate a full-stack application with all pages, shared components, and complete backend.

## Overview

This skill extends `/clone-page` to handle multi-page sites:
1. **Crawl** - Discover all pages within the site
2. **Analyze** - Deep analysis of each page type
3. **Deduplicate** - Identify shared components and layouts
4. **Plan** - Create comprehensive generation plan
5. **Confirm** - Get user approval
6. **Generate** - Create complete frontend and backend

## Arguments

| Argument | Description | Required | Default |
|----------|-------------|----------|---------|
| `url` | Root URL to clone | Yes | - |
| `--depth` | Crawl depth (1-5) | No | 2 |
| `--max-pages` | Maximum pages to analyze | No | 20 |
| `--frontend` | Frontend framework | No | nextjs |
| `--backend` | Backend framework | No | fastapi |
| `--output` | Output directory | No | ./cloned/ |
| `--include` | URL patterns to include | No | * |
| `--exclude` | URL patterns to exclude | No | - |

## Examples

```bash
# Clone entire site with defaults
/clone-site https://example.com

# Limit depth and pages
/clone-site https://example.com --depth 3 --max-pages 30

# Only certain sections
/clone-site https://example.com --include "/products/*,/categories/*"

# Exclude specific paths
/clone-site https://example.com --exclude "/admin/*,/api/*"

# Custom output
/clone-site https://example.com --output ./my-ecommerce-clone/
```

## Workflow

### Phase 1: Discovery

Crawl the site to discover pages:

```
┌─────────────────────────────────────────────────────────────────┐
│                       SITE DISCOVERY                            │
├─────────────────────────────────────────────────────────────────┤
│ Starting URL: https://example.com                               │
│ Crawl Depth: 2                                                  │
│ Max Pages: 20                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Pages Found:                                                    │
│ ├── / (landing)                                                │
│ ├── /products (listing)                                        │
│ ├── /products/:id (detail)                                     │
│ ├── /categories (listing)                                      │
│ ├── /categories/:slug (filtered listing)                       │
│ ├── /cart (form)                                               │
│ ├── /checkout (multi-step form)                                │
│ ├── /login (auth)                                              │
│ ├── /register (auth)                                           │
│ ├── /account (dashboard)                                       │
│ ├── /account/orders (listing)                                  │
│ ├── /account/orders/:id (detail)                               │
│ └── /about (static)                                            │
│                                                                 │
│ Total: 13 unique page types                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 2: Analysis

Analyze each page type:

```
┌─────────────────────────────────────────────────────────────────┐
│                       PAGE ANALYSIS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Page Types:                                                     │
│                                                                 │
│ LANDING (/)                                                     │
│ ├── Hero Section                                               │
│ ├── Features Grid                                              │
│ ├── Testimonials                                               │
│ └── CTA Section                                                │
│                                                                 │
│ LISTING (/products, /categories/:slug)                         │
│ ├── Filter Panel                                               │
│ ├── Product Grid                                               │
│ ├── Pagination                                                 │
│ └── Sort Dropdown                                              │
│                                                                 │
│ DETAIL (/products/:id)                                         │
│ ├── Image Gallery                                              │
│ ├── Product Info                                               │
│ ├── Add to Cart                                                │
│ └── Related Products                                           │
│                                                                 │
│ AUTH (/login, /register)                                        │
│ ├── Auth Form                                                  │
│ └── OAuth Buttons                                              │
│                                                                 │
│ DASHBOARD (/account/*)                                          │
│ ├── Sidebar Nav                                                │
│ └── Content Area                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 3: Component Deduplication

Identify shared components:

```markdown
## Shared Components

### Layout
- `Header` - Used on all pages
- `Footer` - Used on all pages
- `Sidebar` - Used on account pages
- `PageLayout` - Wraps all page content

### UI Components
- `Button` - 47 instances across site
- `Card` - 23 instances
- `Input` - 18 instances
- `Badge` - 12 instances
- `Modal` - 5 instances

### Section Components
- `ProductCard` - Used in grids, carousels, related
- `FilterPanel` - Products, categories
- `Pagination` - All listing pages
- `AuthForm` - Login, register
- `SearchBar` - Header, products

### Data Models (Unified)
| Model | Pages Using |
|-------|-------------|
| Product | 5 pages |
| Category | 3 pages |
| User | 4 pages |
| Cart | 2 pages |
| Order | 3 pages |
```

### Phase 4: Generation Plan

```markdown
## Site Clone Plan

### Source
- **URL:** https://example.com
- **Pages:** 13 unique types
- **Depth:** 2 levels

### Frontend (Next.js + Tailwind)

**Layouts:**
| Layout | Pages |
|--------|-------|
| MainLayout | All public pages |
| AccountLayout | /account/* |
| AuthLayout | /login, /register |

**Pages:**
| Route | Page Type | Components |
|-------|-----------|------------|
| / | Landing | Hero, Features, Testimonials, CTA |
| /products | Listing | FilterPanel, ProductGrid, Pagination |
| /products/[id] | Detail | ImageGallery, ProductInfo, RelatedProducts |
| /categories | Listing | CategoryGrid |
| /categories/[slug] | Listing | FilterPanel, ProductGrid |
| /cart | Form | CartItems, CartSummary |
| /checkout | Multi-step | CheckoutStepper, AddressForm, PaymentForm |
| /login | Auth | AuthForm, OAuthButtons |
| /register | Auth | AuthForm, OAuthButtons |
| /account | Dashboard | AccountNav, DashboardContent |
| /account/orders | Listing | OrderTable |
| /account/orders/[id] | Detail | OrderDetails |
| /about | Static | AboutContent |

**Components:**
- 8 UI components
- 15 section components
- 3 layout components

### Backend (FastAPI)

**Models:**
| Model | Fields | Relationships |
|-------|--------|---------------|
| Product | 10 | Category, CartItems, OrderItems |
| Category | 4 | Products |
| User | 8 | Cart, Orders |
| Cart | 3 | User, CartItems |
| CartItem | 4 | Cart, Product |
| Order | 8 | User, OrderItems |
| OrderItem | 5 | Order, Product |

**Endpoints:**
| Group | Endpoints |
|-------|-----------|
| Products | 4 (list, detail, search, featured) |
| Categories | 2 (list, detail) |
| Auth | 5 (register, login, logout, me, oauth) |
| Cart | 4 (get, add, update, remove) |
| Orders | 3 (list, create, detail) |
| Account | 2 (update, delete) |

**Total:** 20 API endpoints

### File Count
- Frontend: ~45 files
- Backend: ~35 files
- Total: ~80 files
```

### Phase 5: Confirmation

```markdown
## Confirmation Required

Ready to generate full site clone:

**Site:** https://example.com
**Pages:** 13 unique page types
**Components:** 26 total (8 UI, 15 sections, 3 layouts)

### Frontend
- Framework: Next.js 14 with Tailwind CSS
- Routes: 13
- Components: 26
- Output: ./cloned/frontend/

### Backend
- Framework: FastAPI (Python)
- Models: 7 database models
- Endpoints: 20 API routes
- Output: ./cloned/backend/

### Authentication
- NextAuth.js (Google OAuth + Email)
- JWT tokens (access + refresh)
- Protected routes: /account/*, /cart, /checkout

### Options
1. ✅ Proceed with full generation
2. Generate frontend only
3. Generate backend only
4. Exclude certain pages
5. Modify plan
6. Cancel

Your choice:
```

### Phase 6: Generation

After confirmation, generate all code:

```
./cloned/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx                # Landing
│   │   │   ├── products/
│   │   │   │   ├── page.tsx            # Listing
│   │   │   │   └── [id]/page.tsx       # Detail
│   │   │   ├── categories/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [slug]/page.tsx
│   │   │   ├── cart/page.tsx
│   │   │   ├── checkout/page.tsx
│   │   │   ├── (auth)/
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── register/page.tsx
│   │   │   └── account/
│   │   │       ├── layout.tsx
│   │   │       ├── page.tsx
│   │   │       └── orders/
│   │   │           ├── page.tsx
│   │   │           └── [id]/page.tsx
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   ├── sections/
│   │   │   └── layout/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── types/
│   └── package.json
│
└── backend/
    ├── app/
    │   ├── api/routes/
    │   │   ├── products.py
    │   │   ├── categories.py
    │   │   ├── auth.py
    │   │   ├── cart.py
    │   │   ├── orders.py
    │   │   └── account.py
    │   ├── models/
    │   ├── schemas/
    │   └── core/
    ├── alembic/
    └── pyproject.toml
```

### Phase 7: Report

```markdown
## Site Clone Complete

**Generated:** 2024-01-15 10:30:00
**Source:** https://example.com

### Summary
| Category | Count |
|----------|-------|
| Pages | 13 |
| Components | 26 |
| Models | 7 |
| Endpoints | 20 |
| Files | ~80 |

### Frontend Structure
```
src/app/
├── (public)/           # Public pages
├── (auth)/             # Auth pages with layout
├── account/            # Protected account pages
└── api/                # API route handlers
```

### Backend Structure
```
app/
├── api/routes/         # 6 route modules
├── models/             # 7 SQLAlchemy models
├── schemas/            # Request/response schemas
└── core/               # Config, auth, db
```

### Routing

| Frontend Route | Backend Endpoint |
|----------------|------------------|
| /products | GET /api/products |
| /products/[id] | GET /api/products/{id} |
| /cart | GET/POST /api/cart |
| /checkout | POST /api/orders |
| /account | GET /api/auth/me |
| /account/orders | GET /api/orders |

### Next Steps

1. Frontend setup:
```bash
cd cloned/frontend
npm install
cp .env.example .env.local
npm run dev
```

2. Backend setup:
```bash
cd cloned/backend
pip install -e ".[dev]"
cp .env.example .env
docker-compose up -d db
alembic upgrade head
uvicorn app.main:app --reload
```

3. Seed data:
```bash
cd cloned/backend
python scripts/seed.py
```

4. Access:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
```

## Crawl Configuration

### Include Patterns
```bash
# Only product pages
--include "/products/*"

# Multiple patterns
--include "/products/*,/categories/*,/about"

# Regex patterns
--include "^/products/[0-9]+$"
```

### Exclude Patterns
```bash
# Skip admin
--exclude "/admin/*"

# Multiple exclusions
--exclude "/admin/*,/api/*,/internal/*"

# Common exclusions
--exclude "/cdn-cgi/*,/*.pdf,/*.xml"
```

### Depth Control
- `--depth 1`: Only linked from homepage
- `--depth 2`: 2 clicks from homepage (default)
- `--depth 3`: 3 clicks deep
- `--depth 5`: Maximum depth

## Output Customization

### Split Frontend/Backend
```bash
/clone-site https://example.com \
  --output-frontend ./frontend \
  --output-backend ./backend
```

### Monorepo Structure
```bash
/clone-site https://example.com --monorepo
```

Creates:
```
./cloned/
├── packages/
│   ├── frontend/
│   ├── backend/
│   └── shared/         # Shared types
├── package.json        # Workspace config
└── turbo.json          # Turborepo config
```

## Agents Used

| Agent | Role |
|-------|------|
| **site-analyzer** | Crawls and analyzes each page |
| **ui-cloner** | Generates frontend components |
| **api-generator** | Generates backend API |

## Related Skills

- `/clone-page` - Clone single page
- `/analyze-site` - Crawl and analyze only
- `/new-page` - Generate single page
