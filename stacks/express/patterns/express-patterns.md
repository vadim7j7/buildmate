# Express.js Code Patterns

Reference patterns for Express.js API development. Agents should read this file
before writing code to ensure consistency across the codebase.

---

## 1. Router Pattern

Organize routes by resource in dedicated router modules.

```typescript
// src/routes/projects.ts
import { Router } from 'express';
import { ProjectController } from '@/controllers/project-controller';
import { validate } from '@/middleware/validate';
import { createProjectSchema, updateProjectSchema } from '@/schemas/project';
import { authenticate } from '@/middleware/auth';

const router = Router();
const controller = new ProjectController();

router.use(authenticate);

router.get('/', controller.list);
router.post('/', validate(createProjectSchema), controller.create);
router.get('/:id', controller.getById);
router.patch('/:id', validate(updateProjectSchema), controller.update);
router.delete('/:id', controller.delete);

export { router as projectRouter };
```

### Rules

- One router per resource
- Use `Router()` from express
- Apply middleware at router level when shared
- Delegate all logic to controllers
- Export named routers

---

## 2. Controller Pattern

Controllers handle HTTP request/response. Business logic lives in services.

```typescript
// src/controllers/project-controller.ts
import type { Request, Response, NextFunction } from 'express';
import { ProjectService } from '@/services/project-service';
import { NotFoundError } from '@/lib/errors';

export class ProjectController {
  private service = new ProjectService();

  list = async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { skip = '0', limit = '20' } = req.query;
      const projects = await this.service.list({
        skip: Number(skip),
        limit: Number(limit),
      });
      res.json(projects);
    } catch (error) {
      next(error);
    }
  };

  create = async (req: Request, res: Response, next: NextFunction) => {
    try {
      const project = await this.service.create(req.body);
      res.status(201).json(project);
    } catch (error) {
      next(error);
    }
  };

  getById = async (req: Request, res: Response, next: NextFunction) => {
    try {
      const project = await this.service.getById(req.params.id);
      if (!project) throw new NotFoundError('Project', req.params.id);
      res.json(project);
    } catch (error) {
      next(error);
    }
  };
}
```

### Rules

- Arrow function methods for proper `this` binding
- All handlers take `(req, res, next)`
- All errors passed to `next(error)`
- No business logic in controllers
- HTTP status codes set explicitly

---

## 3. Service Pattern

Services contain business logic and data access.

```typescript
// src/services/project-service.ts
import { prisma } from '@/lib/db';
import type { Project } from '@prisma/client';

export class ProjectService {
  async list(options: { skip?: number; limit?: number } = {}): Promise<Project[]> {
    const { skip = 0, limit = 20 } = options;
    return prisma.project.findMany({
      skip,
      take: limit,
      orderBy: { updatedAt: 'desc' },
    });
  }

  async getById(id: string): Promise<Project | null> {
    return prisma.project.findUnique({ where: { id } });
  }

  async create(data: { name: string; description?: string }): Promise<Project> {
    return prisma.project.create({ data });
  }
}
```

---

## 4. Middleware Pattern

### Validation Middleware

```typescript
// src/middleware/validate.ts
import type { Request, Response, NextFunction } from 'express';
import type { ZodSchema } from 'zod';

export function validate(schema: ZodSchema) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      res.status(422).json({ errors: result.error.flatten().fieldErrors });
      return;
    }
    req.body = result.data;
    next();
  };
}
```

### Auth Middleware

```typescript
// src/middleware/auth.ts
import type { Request, Response, NextFunction } from 'express';

export function authenticate(req: Request, res: Response, next: NextFunction) {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (!token) {
    res.status(401).json({ error: 'Unauthorized' });
    return;
  }
  // Verify token and attach user to request
  next();
}
```

### Error Handler

```typescript
// src/middleware/error-handler.ts
import type { Request, Response, NextFunction } from 'express';
import { AppError } from '@/lib/errors';

export function errorHandler(
  err: Error,
  _req: Request,
  res: Response,
  _next: NextFunction,
) {
  if (err instanceof AppError) {
    res.status(err.statusCode).json({ error: err.message, code: err.code });
    return;
  }
  res.status(500).json({ error: 'Internal server error' });
}
```

---

## 5. Schema Pattern (Zod)

```typescript
// src/schemas/project.ts
import { z } from 'zod';

export const createProjectSchema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().max(5000).optional(),
});

export const updateProjectSchema = z.object({
  name: z.string().min(1).max(255).optional(),
  description: z.string().max(5000).optional(),
});

export type CreateProjectInput = z.infer<typeof createProjectSchema>;
export type UpdateProjectInput = z.infer<typeof updateProjectSchema>;
```

---

## 6. App Setup Pattern

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
app.get('/health', (_req, res) => res.json({ status: 'ok' }));

// Routes
app.use('/projects', projectRouter);

// Error handler (must be last)
app.use(errorHandler);

export { app };
```
