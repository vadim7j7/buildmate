'use server';

import { revalidatePath } from 'next/cache';
import type { Todo } from '@/types/todo';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const API_PREFIX = '/api/v1';

/**
 * Server action state for form feedback.
 */
export type ActionState = {
  success: boolean;
  message: string;
  errors?: Record<string, string[]>;
};

/**
 * Creates a new todo.
 */
export async function createTodo(
  prevState: ActionState | null,
  formData: FormData
): Promise<ActionState> {
  const title = formData.get('title');

  if (!title || typeof title !== 'string' || title.trim() === '') {
    return {
      success: false,
      message: 'Validation failed',
      errors: { title: ['Title is required'] },
    };
  }

  try {
    const response = await fetch(`${API_URL}${API_PREFIX}/todos/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: title.trim() }),
    });

    if (!response.ok) {
      return {
        success: false,
        message: 'Failed to create todo',
      };
    }

    revalidatePath('/');
    return { success: true, message: 'Todo created' };
  } catch {
    return {
      success: false,
      message: 'Failed to create todo',
    };
  }
}

/**
 * Updates an existing todo.
 */
export async function updateTodo(
  id: number,
  data: Partial<Pick<Todo, 'title' | 'completed'>>
): Promise<ActionState> {
  try {
    const response = await fetch(`${API_URL}${API_PREFIX}/todos/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      return {
        success: false,
        message: 'Failed to update todo',
      };
    }

    revalidatePath('/');
    return { success: true, message: 'Todo updated' };
  } catch {
    return {
      success: false,
      message: 'Failed to update todo',
    };
  }
}

/**
 * Deletes a todo by ID.
 */
export async function deleteTodo(id: number): Promise<ActionState> {
  try {
    const response = await fetch(`${API_URL}${API_PREFIX}/todos/${id}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      return {
        success: false,
        message: 'Failed to delete todo',
      };
    }

    revalidatePath('/');
    return { success: true, message: 'Todo deleted' };
  } catch {
    return {
      success: false,
      message: 'Failed to delete todo',
    };
  }
}

/**
 * Clears all completed todos.
 */
export async function clearCompleted(): Promise<ActionState> {
  try {
    const response = await fetch(`${API_URL}${API_PREFIX}/todos/completed`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      return {
        success: false,
        message: 'Failed to clear completed todos',
      };
    }

    revalidatePath('/');
    return { success: true, message: 'Completed todos cleared' };
  } catch {
    return {
      success: false,
      message: 'Failed to clear completed todos',
    };
  }
}

/**
 * Toggles the completed status of a todo.
 */
export async function toggleTodo(
  id: number,
  completed: boolean
): Promise<ActionState> {
  return updateTodo(id, { completed });
}
