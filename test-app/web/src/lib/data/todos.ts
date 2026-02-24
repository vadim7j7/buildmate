import type { Todo, TodoListResponse } from '@/types/todo';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const API_PREFIX = '/api/v1';

/**
 * Fetches all todos from the API with optional filter.
 * @param filter - Optional filter: 'all', 'active', or 'completed'
 */
export async function getTodos(filter?: string): Promise<TodoListResponse> {
  const url = new URL(`${API_PREFIX}/todos/`, API_URL);

  if (filter && filter !== 'all') {
    url.searchParams.set('filter', filter);
  }

  const response = await fetch(url.toString(), {
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error('Failed to fetch todos');
  }

  return response.json() as Promise<TodoListResponse>;
}

/**
 * Fetches a single todo by ID.
 * @param id - The todo ID
 */
export async function getTodo(id: number): Promise<Todo | null> {
  const response = await fetch(`${API_URL}${API_PREFIX}/todos/${id}`, {
    cache: 'no-store',
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error('Failed to fetch todo');
  }

  return response.json() as Promise<Todo>;
}
