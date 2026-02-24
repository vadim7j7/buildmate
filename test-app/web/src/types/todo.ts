/**
 * Todo item matching the API response structure.
 */
export type Todo = {
  id: number;
  title: string;
  completed: boolean;
  created_at: string;
  updated_at: string;
};

/**
 * Metadata for pagination and filtering results.
 */
export type TodoMeta = {
  total: number;
  completed: number;
  active: number;
};

/**
 * Response structure from the API when fetching todos.
 */
export type TodoListResponse = {
  data: Todo[];
  meta: TodoMeta;
};
