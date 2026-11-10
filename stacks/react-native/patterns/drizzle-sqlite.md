# Offline-First Data: Drizzle ORM + expo-sqlite

The app is **offline-first**: all data lives in a local SQLite database accessed
through Drizzle ORM. There is no network read/write on the hot path.

## Scaffolded files (already in the project)

- `src/db/schema.ts` — table definitions (the source of truth).
- `src/db/client.ts` — the shared `db` connection (`openDatabaseSync("app.db")`).
- `drizzle.config.ts` — drizzle-kit config (dialect `sqlite`, driver `expo`).
- `src/db/migrations/` — generated migrations (created by `drizzle-kit generate`).
- `babel.config.js` — `["inline-import", { extensions: [".sql"] }]` so the generated
  `.sql` files are bundled as strings.
- `metro.config.js` — `config.resolver.sourceExts.push("sql")` so Metro resolves them.
- `tsconfig.json` — `@/*` → `./src/*`.

If the project already had its own `babel.config.js` / `metro.config.js` (buildmate
never overwrites existing files), merge those two lines in by hand. Without them the
app fails at startup with "Unable to resolve module ./0000_xxx.sql".

## Packages

```bash
npx expo install expo-sqlite
npm i drizzle-orm
npm i -D drizzle-kit babel-plugin-inline-import
```

## Workflow

1. Edit `src/db/schema.ts` to add/change tables.
2. Run `npx drizzle-kit generate` → writes a migration + updated `migrations.js`.
3. Migrations are applied **on startup** — never ship an app that requires a manual
   migration step.

## Run migrations on startup

In the root layout (`src/app/_layout.tsx`), gate the UI on migrations completing:

```tsx
// src/app/_layout.tsx
import { useMigrations } from "drizzle-orm/expo-sqlite/migrator";
import { Stack } from "expo-router";
import migrations from "@/db/migrations/migrations";
import { db } from "@/db/client";

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
- Keep all DB access in `src/db/queries/<entity>.ts` (plain async functions called from
  React Query hooks in `src/queries/`); screens and components never import `db` directly.
- Never block the JS thread on large migrations; keep them small and incremental.
