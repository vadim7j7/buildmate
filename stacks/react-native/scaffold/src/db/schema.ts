import { sql } from "drizzle-orm";
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

// Example offline-first table. Replace with your domain models, then run
// `npx drizzle-kit generate` to produce a migration in ./migrations.
export const items = sqliteTable("items", {
  id: text("id").primaryKey(),
  title: text("title").notNull(),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
});

export type Item = typeof items.$inferSelect;
export type NewItem = typeof items.$inferInsert;
