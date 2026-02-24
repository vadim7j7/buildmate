# Feature: Todo App with Server-Side Rendering

## Status: COMPLETE

## Overview
Build a full-stack todo application with Server-Side Rendering. The frontend uses Next.js App Router with Server Components for SSR, while the backend uses Python FastAPI to provide the REST API. The app will allow users to create, read, update, and delete todo items with real-time UI updates.

## Requirements
- [ ] Display list of todos with SSR (Server-Side Rendering)
- [ ] Create new todos with form submission
- [ ] Toggle todo completion status
- [ ] Delete todos
- [ ] Edit todo title
- [ ] Filter todos by status (all, active, completed)
- [ ] Clear all completed todos
- [ ] Show todo count and completion stats

## Technical Approach

### Python FastAPI (Backend)
- **Models**: `Todo` SQLAlchemy model with id, title, completed, created_at, updated_at
- **Schemas**: TodoCreate, TodoUpdate, TodoRead Pydantic schemas
- **Service**: TodoService with CRUD operations
- **Router**: `/api/v1/todos` endpoints for CRUD operations
- **Database**: SQLite for development (async with aiosqlite)

**Endpoints:**
- `GET /api/v1/todos` - List all todos (with optional filter)
- `POST /api/v1/todos` - Create a todo
- `GET /api/v1/todos/{id}` - Get a single todo
- `PATCH /api/v1/todos/{id}` - Update a todo
- `DELETE /api/v1/todos/{id}` - Delete a todo
- `DELETE /api/v1/todos/completed` - Clear all completed todos

### React + Next.js (Frontend)
- **Pages**: Main todo page with SSR data fetching
- **Components**: TodoList, TodoItem, TodoForm, TodoFilters
- **Server Actions**: For mutations (create, update, delete)
- **Data Layer**: lib/data/todos.ts for fetching from FastAPI
- **Styling**: Tailwind CSS

**Structure:**
```
web/src/
├── app/
│   ├── page.tsx              # Main todo page (SSR)
│   ├── layout.tsx            # Root layout
│   ├── loading.tsx           # Loading state
│   └── error.tsx             # Error boundary
├── components/
│   └── todos/
│       ├── TodoList.tsx      # List container
│       ├── TodoItem.tsx      # Individual todo (client)
│       ├── AddTodoForm.tsx   # Form to add todos (client)
│       └── TodoFilters.tsx   # Filter controls (client)
├── lib/
│   ├── data/
│   │   └── todos.ts          # Server-side data fetching
│   └── actions/
│       └── todos.ts          # Server Actions for mutations
└── types/
    └── todo.ts               # TypeScript types
```

## API Contract

```
# List todos
GET /api/v1/todos?filter=all|active|completed
Response: { data: Todo[], meta: { total: number, active: number, completed: number } }

# Create todo
POST /api/v1/todos
Body: { title: string }
Response: Todo

# Get single todo
GET /api/v1/todos/{id}
Response: Todo

# Update todo
PATCH /api/v1/todos/{id}
Body: { title?: string, completed?: boolean }
Response: Todo

# Delete todo
DELETE /api/v1/todos/{id}
Response: 204 No Content

# Clear completed
DELETE /api/v1/todos/completed
Response: { deleted_count: number }

# Todo shape
Todo = {
  id: number,
  title: string,
  completed: boolean,
  created_at: string,  # ISO 8601
  updated_at: string   # ISO 8601
}
```

## Files to Create/Modify

### Backend (Python FastAPI)
- `backend/src/app/__init__.py` - Package init
- `backend/src/app/main.py` - FastAPI app entry point
- `backend/src/app/config.py` - Settings/configuration
- `backend/src/app/database.py` - Database setup
- `backend/src/app/models/__init__.py` - Models package
- `backend/src/app/models/todo.py` - Todo SQLAlchemy model
- `backend/src/app/schemas/__init__.py` - Schemas package
- `backend/src/app/schemas/todo.py` - Todo Pydantic schemas
- `backend/src/app/services/__init__.py` - Services package
- `backend/src/app/services/todo_service.py` - Todo business logic
- `backend/src/app/routers/__init__.py` - Routers package
- `backend/src/app/routers/todo_router.py` - Todo API endpoints
- `backend/pyproject.toml` - Python project config
- `backend/tests/` - Test files

### Frontend (Next.js)
- `web/package.json` - Node dependencies
- `web/tsconfig.json` - TypeScript config
- `web/next.config.js` - Next.js config
- `web/tailwind.config.js` - Tailwind config
- `web/src/app/page.tsx` - Main todo page
- `web/src/app/layout.tsx` - Root layout
- `web/src/app/loading.tsx` - Loading state
- `web/src/app/error.tsx` - Error boundary
- `web/src/components/todos/` - Todo components
- `web/src/lib/data/todos.ts` - Data fetching
- `web/src/lib/actions/todos.ts` - Server Actions
- `web/src/types/todo.ts` - TypeScript types

## Tasks
| # | Task | Agent | Status | Notes |
|---|------|-------|--------|-------|
| 1 | Set up FastAPI project structure | backend-developer | PENDING | Project scaffolding with uv |
| 2 | Implement Todo model, schemas, service | backend-developer | PENDING | Full CRUD |
| 3 | Implement Todo router with endpoints | backend-developer | PENDING | REST API |
| 4 | Set up Next.js project structure | frontend-developer | PENDING | App Router, Tailwind |
| 5 | Implement data fetching layer | frontend-developer | PENDING | SSR data layer |
| 6 | Implement todo page with SSR | frontend-developer | PENDING | Server Components |
| 7 | Implement interactive components | frontend-developer | PENDING | Client Components |
| 8 | Implement Server Actions | frontend-developer | PENDING | Mutations |
| 9 | Write backend tests | backend-tester | PENDING | pytest |
| 10 | Write frontend tests | frontend-tester | PENDING | Jest |
| 11 | Code review backend | backend-reviewer | PENDING | |
| 12 | Code review frontend | frontend-reviewer | PENDING | |

## Completion Criteria
- [ ] All CRUD operations work end-to-end
- [ ] SSR renders todo list on initial page load
- [ ] Form submission creates new todos
- [ ] Toggle and delete work with optimistic UI
- [ ] All tests passing
- [ ] Code review passed
- [ ] No lint errors
- [ ] No type errors
