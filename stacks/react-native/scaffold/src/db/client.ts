import { drizzle } from "drizzle-orm/expo-sqlite";
import { openDatabaseSync } from "expo-sqlite";

// Single shared connection. `enableChangeListener` lets useLiveQuery react to writes.
const sqlite = openDatabaseSync("app.db", { enableChangeListener: true });
export const db = drizzle(sqlite);
export { sqlite };
