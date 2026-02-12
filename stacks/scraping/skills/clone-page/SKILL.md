# /clone-page

Analyze a webpage and generate full-stack code (frontend + backend) with user confirmation.

## Overview

This skill orchestrates a complete page cloning workflow:
1. **Analyze** - Deep analysis of the target page
2. **Plan** - Create detailed generation plan
3. **Confirm** - Get user approval before generating
4. **Generate** - Create frontend and backend code

## Arguments

| Argument | Description | Required | Default |
|----------|-------------|----------|---------|
| `url` | URL to clone | Yes | - |
| `--frontend` | Frontend framework | No | nextjs |
| `--backend` | Backend framework | No | fastapi |
| `--output` | Output directory | No | ./cloned/ |
| `--ui` | UI library | No | tailwind |
| `--no-backend` | Skip backend generation | No | false |
| `--analyze-only` | Only analyze, don't generate | No | false |

## Examples

```bash
# Full-stack clone with defaults (Next.js + FastAPI)
/clone-page https://example.com/products

# Frontend only (no backend)
/clone-page https://example.com/landing --no-backend

# Custom frameworks
/clone-page https://example.com/products --frontend react --backend express

# Analysis only
/clone-page https://example.com/products --analyze-only

# Custom output directory
/clone-page https://example.com/products --output ./my-clone/

# With specific UI library
/clone-page https://example.com/products --ui mantine
```

## Workflow

### Phase 1: Analysis

The **site-analyzer** agent performs deep analysis:

```
┌─────────────────────────────────────────────────────────────────┐
│                         SITE ANALYSIS                           │
├─────────────────────────────────────────────────────────────────┤
│ • Page structure (header, main, sidebar, footer)                │
│ • Components (cards, forms, modals, tables)                     │
│ • Data models (Product, User, Category, etc.)                   │
│ • API endpoints (GET /products, POST /cart, etc.)               │
│ • Authentication (OAuth providers, login forms)                 │
│ • Design system (colors, typography, spacing)                   │
│ • Interactions (hover states, animations)                       │
└─────────────────────────────────────────────────────────────────┘
```

Output saved to:
- `.agent-pipeline/site-analysis.json` - Structured data
- `.agent-pipeline/site-analysis.md` - Human-readable summary

### Phase 2: Planning

Present findings and create generation plan:

```markdown
## Analysis Complete

**URL:** https://example.com/products
**Page Type:** Product Listing

### Components Found
| Component | Count | Purpose |
|-----------|-------|---------|
| ProductCard | 12 | Product display |
| FilterPanel | 1 | Category/price filters |
| SearchBar | 1 | Product search |
| Pagination | 1 | Page navigation |

### Data Models
- **Product**: id, name, price, image, rating, inStock, category
- **Category**: id, name, slug, count
- **User**: id, email, name, avatar

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/products | List with filters |
| GET | /api/products/:id | Single product |
| GET | /api/categories | All categories |
| POST | /api/cart | Add to cart |

### Authentication
- **Detected:** Google OAuth + Email/Password
- **Protected Routes:** /account, /checkout, /orders

### Design System
- Primary: #3b82f6
- Font: Inter
- Spacing: 4px base

## Generation Plan

### Frontend (Next.js + Tailwind)
- 4 UI components (Button, Card, Input, Badge)
- 5 section components (Header, ProductGrid, FilterPanel, Footer, Hero)
- 2 pages (Home, Products)
- Types and API hooks

### Backend (FastAPI)
- 5 models (Product, Category, User, Cart, Order)
- 12 API endpoints
- JWT authentication
- Database migrations
```

### Phase 3: Confirmation

Ask user to confirm before generating:

```markdown
## Confirmation Required

Ready to generate:

**Frontend:**
- Framework: Next.js 14 with Tailwind CSS
- Components: 12 files
- Pages: 2 routes
- Output: ./cloned/frontend/

**Backend:**
- Framework: FastAPI (Python)
- Models: 5 database models
- Endpoints: 12 API routes
- Output: ./cloned/backend/

**Authentication:**
- Include NextAuth.js setup? (Google + Email)
- Include backend JWT auth? (Yes)

**Options:**
1. Proceed with full generation
2. Generate frontend only
3. Generate backend only
4. Modify plan
5. Cancel

Your choice:
```

### Phase 4: Generation

After confirmation, generate code:

```
./cloned/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   └── sections/
│   │   ├── app/
│   │   ├── types/
│   │   ├── hooks/
│   │   └── lib/
│   ├── tailwind.config.ts
│   └── package.json
│
└── backend/
    ├── app/
    │   ├── api/routes/
    │   ├── models/
    │   ├── schemas/
    │   └── core/
    ├── alembic/
    └── pyproject.toml
```

### Phase 5: Report

After generation, provide summary:

```markdown
## Clone Complete

**Generated:** 2024-01-15 10:30:00
**Source:** https://example.com/products

### Frontend (./cloned/frontend/)
- 12 components
- 2 pages
- Full TypeScript types
- API hooks ready

### Backend (./cloned/backend/)
- 5 models with migrations
- 12 API endpoints
- JWT authentication
- OpenAPI documentation

### Next Steps

**Frontend:**
```bash
cd cloned/frontend
npm install
npm run dev
```

**Backend:**
```bash
cd cloned/backend
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

### Manual Adjustments Needed

1. Replace placeholder images
2. Update copy/text content
3. Configure OAuth credentials
4. Add actual database seed data
```

## Framework Combinations

| Frontend | Backend | Use Case |
|----------|---------|----------|
| Next.js | FastAPI | Full-stack Python backend |
| Next.js | Rails | Ruby on Rails API |
| Next.js | Express | Node.js TypeScript |
| React | FastAPI | SPA with Python API |
| React Native | FastAPI | Mobile app |

## Output Structure

### Frontend Output
```
cloned/frontend/
├── src/
│   ├── components/
│   │   ├── ui/           # Button, Card, Input, Badge
│   │   ├── sections/     # Header, ProductGrid, Footer
│   │   └── layout/       # PageLayout
│   ├── app/              # Next.js routes
│   ├── types/            # TypeScript definitions
│   ├── hooks/            # Data fetching hooks
│   └── lib/              # Utilities
├── public/
├── tailwind.config.ts
├── package.json
└── README.md
```

### Backend Output
```
cloned/backend/
├── app/
│   ├── api/
│   │   ├── routes/       # Endpoint handlers
│   │   └── deps.py       # Dependencies
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   └── core/             # Config, security, db
├── alembic/
│   └── versions/         # Migrations
├── tests/
├── pyproject.toml
├── .env.example
└── README.md
```

## Agents Used

| Agent | Role |
|-------|------|
| **site-analyzer** | Deep page analysis |
| **ui-cloner** | Frontend code generation |
| **api-generator** | Backend code generation |

## Configuration

Override defaults in `.claude/settings.json`:

```json
{
  "clone": {
    "defaultFrontend": "nextjs",
    "defaultBackend": "fastapi",
    "defaultOutput": "./cloned",
    "defaultUi": "tailwind",
    "generateMockData": true,
    "includeTests": true
  }
}
```

## Self-Verification

After cloning, verify:

- [ ] Analysis matches page structure
- [ ] Components render correctly
- [ ] Types match data models
- [ ] API endpoints work
- [ ] Authentication flows complete
- [ ] Database migrations run
- [ ] All quality gates pass

## Related Skills

- `/clone-site` - Clone entire multi-page site
- `/analyze-site` - Analysis only (no generation)
- `/new-component` - Generate single component
