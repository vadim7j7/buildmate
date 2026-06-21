# Offline-First Data: Drizzle ORM + expo-sqlite

The app is **offline-first**: all data lives in a local SQLite database accessed
through Drizzle ORM. There is no network read/write on the hot path.

## Scaffolded files (already in the project)

- `src/db/schema.ts` — table definitions (the source of truth).
- `src/db/client.ts` — the shared `db` connection (`openDatabaseSync("app.db")`).
- `drizzle.config.ts` — drizzle-kit config (dialect `sqlite`, driver `expo`).
- `src/db/migrations/` — generated migrations (created by `drizzle-kit generate`).

## Workflow

1. Edit `src/db/schema.ts` to add/change tables.
2. Run `npx drizzle-kit generate` → writes a migration + updated `migrations.js`.
3. Migrations are applied **on startup** — never ship an app that requires a manual
   migration step.

## Run migrations on startup

In the root layout (`app/_layout.tsx`), gate the UI on migrations completing:

```tsx
// app/_layout.tsx
import { useMigrations } from "drizzle-orm/expo-sqlite/migrator";
import migrations from "../src/db/migrations/migrations";
import { db } from "../src/db/client";

export default function RootLayout() {
  const { success, error } = useMigrations(db, migrations);
  if (error) return <MigrationError error={error} />;
  if (!success) return null; // splash stays up
  return <Stack />;
}
```

## Querying

```ts
import { db } from "@/db/client";
import { items } from "@/db/schema";
import { useLiveQuery } from "drizzle-orm/expo-sqlite";

// Reactive read — re-renders when the table changes (enableChangeListener is on).
const { data } = useLiveQuery(db.select().from(items));

// Write
await db.insert(items).values({ id, title });
```

## Rules

- Generate types from the schema (`$inferSelect`/`$inferInsert`) — don't hand-write row types.
- Keep all DB access behind a repository/service layer; UI imports `db` only through it.
- Never block the JS thread on large migrations; keep them small and incremental.
