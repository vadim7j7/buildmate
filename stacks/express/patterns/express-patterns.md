# Express.js Code Patterns

Reference patterns for Express 5 API development. Agents should read this file
before writing code to ensure consistency across the codebase.

> **Express 5:** a rejected promise / error thrown in an `async` handler or middleware
> is forwarded to the error handler automatically. Do **not** wrap handlers in
> `try { ... } catch (error) { next(error) }` or `asyncHandler()` helpers.
> `req.query` is a read-only getter: parse it into a new variable, never assign to it.

---

## 1. Router Pattern

Organize routes by resource in dedicated router modules.

```typescript
// src/routes/projects.ts
import { Router } from 'express';
import { ProjectController } from '@/controllers/project-controller';
import { validateBody } from '@/middleware/validate';
import { createProjectSchema, updateProjectSchema } from '@/schemas/project';
import { authenticate } from '@/middleware/auth';

const router = Router();
const controller = new ProjectController();

router.use(authenticate);

router.get('/', controller.list);
router.post('/', validateBody(createProjectSchema), controller.create);
router.get('/:id', controller.getById);
router.patch('/:id', validateBody(updateProjectSchema), controller.update);
router.delete('/:id', controller.delete);

export { router as projectRouter };
```

### Rules

- One router per resource
- Use `Router()` from express
- Apply middleware at router level when shared
- Delegate all logic to controllers
- Export named routers
- Express 5 path syntax: wildcards are named (`/*splat`), optional segments use braces (`/:file{.:ext}`)

---

## 2. Controller Pattern

Controllers handle HTTP request/response. Business logic lives in services.
Handlers are plain `async` functions: errors (including `ZodError` from `.parse`)
propagate to the error handler.

```typescript
// src/controllers/project-controller.ts
import type { Request, Response } from 'express';
import { ProjectService } from '@/services/project-service';
import { NotFoundError } from '@/lib/errors';
import { listProjectsQuerySchema, projectIdSchema } from '@/schemas/project';

export class ProjectController {
  private service = new ProjectService();

  list = async (req: Request, res: Response) => {
    // req.query is read-only in Express 5: parse into a new variable.
    const query = listProjectsQuerySchema.parse(req.query);
    const projects = await this.service.list(req.user.id, query);
    res.json(projects);
  };

  create = async (req: Request, res: Response) => {
    const project = await this.service.create(req.user.id, req.body);
    res.status(201).json(project);
  };

  getById = async (req: Request, res: Response) => {
    const id = projectIdSchema.parse(req.params.id);
    const project = await this.service.getById(req.user.id, id);
    if (!project) throw new NotFoundError('Project', id);
    res.json(project);
  };
}
```

### Rules

- Arrow function methods for proper `this` binding
- `async (req, res)` handlers; no `try/catch` + `next(error)` boilerplate (Express 5 forwards rejections)
- Catch only to translate a specific error into a specific response
- No business logic in controllers
- HTTP status codes set explicitly

---

## 3. Service Pattern

Services contain business logic and data access. Queries are scoped by the
current user so an ID from the client cannot reach someone else's data.

```typescript
// src/services/project-service.ts
import { prisma } from '@/lib/db';
import type { Project } from '@prisma/client';
import type { CreateProjectInput, ListProjectsQuery } from '@/schemas/project';

export class ProjectService {
  async list(ownerId: string, { skip, limit }: ListProjectsQuery): Promise<Project[]> {
    return prisma.project.findMany({
      where: { ownerId },
      skip,
      take: limit,
      orderBy: { updatedAt: 'desc' },
    });
  }

  async getById(ownerId: string, id: string): Promise<Project | null> {
    return prisma.project.findFirst({ where: { id, ownerId } });
  }

  async create(ownerId: string, data: CreateProjectInput): Promise<Project> {
    return prisma.project.create({ data: { ...data, ownerId } });
  }
}
```

---

## 4. Middleware Pattern

### Validation Middleware

`req.body` may be replaced with the parsed value. `req.query` may not (read-only
getter in Express 5) — parse query strings in the handler, or store the result in
`res.locals`.

```typescript
// src/middleware/validate.ts
import type { Request, Response, NextFunction } from 'express';
import { z } from 'zod';

export function validateBody(schema: z.ZodType) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      res.status(422).json({ errors: z.flattenError(result.error).fieldErrors });
      return;
    }
    req.body = result.data;
    next();
  };
}

export function validateQuery(schema: z.ZodType) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.query);
    if (!result.success) {
      res.status(422).json({ errors: z.flattenError(result.error).fieldErrors });
      return;
    }
    res.locals.query = result.data; // never `req.query = ...` in Express 5
    next();
  };
}
```

### Auth Middleware

```typescript
// src/middleware/auth.ts
import type { Request, Response, NextFunction } from 'express';
import { verifyToken } from '@/lib/auth';

export async function authenticate(req: Request, res: Response, next: NextFunction) {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (!token) {
    res.status(401).json({ error: 'Unauthorized' });
    return;
  }
  // A rejection here (invalid token) is forwarded to the error handler by Express 5.
  req.user = await verifyToken(token);
  next();
}
```

### Error Handler

```typescript
// src/middleware/error-handler.ts
import type { Request, Response, NextFunction } from 'express';
import { z } from 'zod';
import { AppError } from '@/lib/errors';

export function errorHandler(
  err: unknown,
  _req: Request,
  res: Response,
  _next: NextFunction,
) {
  if (err instanceof z.ZodError) {
    res.status(422).json({ errors: z.flattenError(err).fieldErrors });
    return;
  }
  if (err instanceof AppError) {
    res.status(err.statusCode).json({ error: err.message, code: err.code });
    return;
  }
  res.status(500).json({ error: 'Internal server error' });
}
```

---

## 5. Schema Pattern (Zod 4)

```typescript
// src/schemas/project.ts
import { z } from 'zod';

export const createProjectSchema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().max(5000).optional(),
});

export const updateProjectSchema = createProjectSchema.partial();

export const listProjectsQuerySchema = z.object({
  skip: z.coerce.number().int().min(0).default(0),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});

export const projectIdSchema = z.uuid();

export type CreateProjectInput = z.infer<typeof createProjectSchema>;
export type UpdateProjectInput = z.infer<typeof updateProjectSchema>;
export type ListProjectsQuery = z.infer<typeof listProjectsQuerySchema>;
```

Report validation errors with `z.flattenError(error).fieldErrors` (or `error.issues`);
`error.flatten()` / `error.format()` are deprecated in Zod 4.

---

## 6. App Setup Pattern

Keep the app (for Supertest) separate from the server entry that listens.

```typescript
// src/app.ts
import express from 'express';
import cors from 'cors';
import { projectRouter } from '@/routes/projects';
import { errorHandler } from '@/middleware/error-handler';

const app = express();

// Global middleware
app.use(cors());
app.use(express.json());

// Health check
app.get('/health', (_req, res) => {
  res.json({ status: 'ok' });
});

// Routes
app.use('/projects', projectRouter);

// Error handler (must be last)
app.use(errorHandler);

export { app };
```

```typescript
// src/server.ts
import { app } from '@/app';

// The dev server is started with PORT=4000 (frontends own 3000).
const port = Number(process.env.PORT ?? 4000);

app.listen(port, (error) => {
  if (error) throw error; // Express 5 passes listen errors (e.g. EADDRINUSE) here
  console.log(`API listening on http://localhost:${port}`);
});
```
