# Drizzle ORM Query Examples

## Schema Definition

First, define the table in the schema file.

```typescript
// db/schema.ts
import { sqliteTable, text, integer, real } from 'drizzle-orm/sqlite-core';
import { sql } from 'drizzle-orm';

export const budgets = sqliteTable('budgets', {
  id: text('id')
    .primaryKey()
    .$defaultFn(() => crypto.randomUUID()),
  name: text('name').notNull(),
  amount: real('amount').notNull(),
  spent: real('spent').notNull().default(0),
  category: text('category').notNull().default('other'),
  period: text('period', { enum: ['weekly', 'monthly', 'yearly'] })
    .notNull()
    .default('monthly'),
  createdAt: integer('created_at', { mode: 'timestamp' })
    .notNull()
    .default(sql`(unixepoch())`),
  updatedAt: integer('updated_at', { mode: 'timestamp' }),
});

export const transactions = sqliteTable('transactions', {
  id: text('id')
    .primaryKey()
    .$defaultFn(() => crypto.randomUUID()),
  description: text('description').notNull(),
  amount: real('amount').notNull(),
  category: text('category'),
  budgetId: text('budget_id').references(() => budgets.id),
  date: integer('date', { mode: 'timestamp' })
    .notNull()
    .default(sql`(unixepoch())`),
  createdAt: integer('created_at', { mode: 'timestamp' })
    .notNull()
    .default(sql`(unixepoch())`),
});

// Inferred types for insert operations
export type NewBudget = typeof budgets.$inferInsert;
export type Budget = typeof budgets.$inferSelect;
export type NewTransaction = typeof transactions.$inferInsert;
export type Transaction = typeof transactions.$inferSelect;
```

---

## Complete CRUD Query Module

```typescript
// db/queries/budgets.ts
import { eq, desc, and, like, sql } from 'drizzle-orm';
import { db } from '../client';
import { budgets, type NewBudget } from '../schema';

/**
 * Fetch all budgets, ordered by creation date descending.
 */
export async function getBudgets(filters?: { category?: string | null }) {
  const conditions = [];

  if (filters?.category) {
    conditions.push(eq(budgets.category, filters.category));
  }

  if (conditions.length > 0) {
    return db
      .select()
      .from(budgets)
      .where(and(...conditions))
      .orderBy(desc(budgets.createdAt));
  }

  return db.select().from(budgets).orderBy(desc(budgets.createdAt));
}

/**
 * Fetch a single budget by ID.
 * Returns null if not found.
 */
export async function getBudgetById(id: string) {
  const result = await db
    .select()
    .from(budgets)
    .where(eq(budgets.id, id))
    .limit(1);

  return result[0] ?? null;
}

/**
 * Create a new budget.
 * Returns the created record.
 */
export async function createBudget(data: NewBudget) {
  const result = await db.insert(budgets).values(data).returning();
  return result[0];
}

/**
 * Update an existing budget.
 * Returns the updated record.
 */
export async function updateBudget(
  data: { id: string } & Partial<NewBudget>
) {
  const { id, ...values } = data;

  const result = await db
    .update(budgets)
    .set({
      ...values,
      updatedAt: new Date(),
    })
    .where(eq(budgets.id, id))
    .returning();

  return result[0] ?? null;
}

/**
 * Delete a budget by ID.
 */
export async function deleteBudget(id: string) {
  return db.delete(budgets).where(eq(budgets.id, id));
}

/**
 * Search budgets by name.
 */
export async function searchBudgets(query: string) {
  return db
    .select()
    .from(budgets)
    .where(like(budgets.name, `%${query}%`))
    .orderBy(desc(budgets.createdAt));
}

/**
 * Get budget summary statistics.
 */
export async function getBudgetSummary() {
  const result = await db
    .select({
      totalBudgeted: sql<number>`sum(${budgets.amount})`,
      totalSpent: sql<number>`sum(${budgets.spent})`,
      count: sql<number>`count(*)`,
    })
    .from(budgets);

  return result[0];
}
```

---

## Transaction Queries with Joins

```typescript
// db/queries/transactions.ts
import { eq, desc, and, gte, lte, sql } from 'drizzle-orm';
import { db } from '../client';
import { transactions, budgets, type NewTransaction } from '../schema';

/**
 * Fetch all transactions with optional date range filter.
 */
export async function getTransactions(filters?: {
  startDate?: Date;
  endDate?: Date;
  category?: string;
}) {
  const conditions = [];

  if (filters?.startDate) {
    conditions.push(gte(transactions.date, filters.startDate));
  }
  if (filters?.endDate) {
    conditions.push(lte(transactions.date, filters.endDate));
  }
  if (filters?.category) {
    conditions.push(eq(transactions.category, filters.category));
  }

  if (conditions.length > 0) {
    return db
      .select()
      .from(transactions)
      .where(and(...conditions))
      .orderBy(desc(transactions.date));
  }

  return db.select().from(transactions).orderBy(desc(transactions.date));
}

/**
 * Fetch a single transaction by ID.
 */
export async function getTransactionById(id: string) {
  const result = await db
    .select()
    .from(transactions)
    .where(eq(transactions.id, id))
    .limit(1);

  return result[0] ?? null;
}

/**
 * Fetch transactions with their associated budget (JOIN).
 */
export async function getTransactionsWithBudget() {
  return db
    .select({
      transaction: transactions,
      budget: {
        id: budgets.id,
        name: budgets.name,
        category: budgets.category,
      },
    })
    .from(transactions)
    .leftJoin(budgets, eq(transactions.budgetId, budgets.id))
    .orderBy(desc(transactions.date));
}

/**
 * Create a new transaction.
 * Also updates the associated budget's spent amount.
 */
export async function createTransaction(data: NewTransaction) {
  const result = await db.insert(transactions).values(data).returning();
  const created = result[0];

  // Update budget spent amount if linked to a budget
  if (data.budgetId && data.amount < 0) {
    await db
      .update(budgets)
      .set({
        spent: sql`${budgets.spent} + ${Math.abs(data.amount)}`,
        updatedAt: new Date(),
      })
      .where(eq(budgets.id, data.budgetId));
  }

  return created;
}

/**
 * Update an existing transaction.
 */
export async function updateTransaction(
  data: { id: string } & Partial<NewTransaction>
) {
  const { id, ...values } = data;

  const result = await db
    .update(transactions)
    .set(values)
    .where(eq(transactions.id, id))
    .returning();

  return result[0] ?? null;
}

/**
 * Delete a transaction.
 */
export async function deleteTransaction(id: string) {
  return db.delete(transactions).where(eq(transactions.id, id));
}

/**
 * Fetch paginated transactions for infinite scrolling.
 */
export async function getTransactionsPaginated({
  offset,
  limit,
}: {
  offset: number;
  limit: number;
}) {
  return db
    .select()
    .from(transactions)
    .orderBy(desc(transactions.date))
    .limit(limit)
    .offset(offset);
}

/**
 * Get transactions grouped by category with totals.
 */
export async function getTransactionsByCategory() {
  return db
    .select({
      category: transactions.category,
      total: sql<number>`sum(${transactions.amount})`,
      count: sql<number>`count(*)`,
    })
    .from(transactions)
    .groupBy(transactions.category);
}
```

---

## Database Client Initialisation

```typescript
// db/client.ts
import { drizzle } from 'drizzle-orm/expo-sqlite';
import { openDatabaseSync } from 'expo-sqlite';
import * as schema from './schema';

const expo = openDatabaseSync('app.db');
export const db = drizzle(expo, { schema });

/**
 * Initialise the database and run migrations.
 * Call this once at app startup.
 */
export async function initDatabase() {
  // Run migrations
  // In development, you can use push for quick iteration
  // In production, use proper migrations
  await db.run(sql`PRAGMA journal_mode=WAL`);
  await db.run(sql`PRAGMA foreign_keys=ON`);
}
```

---

## Testing Database Queries

Mock the database module and Drizzle functions.

```typescript
// __tests__/db/budgets.test.ts
import { getBudgets, getBudgetById, createBudget } from '@/db/queries/budgets';

// Mock the entire db module
jest.mock('@/db/client', () => {
  const mockSelect = jest.fn().mockReturnThis();
  const mockFrom = jest.fn().mockReturnThis();
  const mockWhere = jest.fn().mockReturnThis();
  const mockOrderBy = jest.fn().mockReturnThis();
  const mockLimit = jest.fn().mockReturnThis();
  const mockInsert = jest.fn().mockReturnThis();
  const mockValues = jest.fn().mockReturnThis();
  const mockReturning = jest.fn();
  const mockUpdate = jest.fn().mockReturnThis();
  const mockSet = jest.fn().mockReturnThis();
  const mockDelete = jest.fn().mockReturnThis();

  return {
    db: {
      select: mockSelect,
      insert: mockInsert,
      update: mockUpdate,
      delete: mockDelete,
      // Chain methods return the db object for chaining
      from: mockFrom,
      where: mockWhere,
      orderBy: mockOrderBy,
      limit: mockLimit,
      values: mockValues,
      returning: mockReturning,
      set: mockSet,
    },
  };
});

// Note: For integration testing with a real database, use an in-memory
// SQLite database with proper migrations applied before each test suite.
```
