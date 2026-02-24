import type { ActionState } from '../todos';

/**
 * Mock for Server Actions - used in Jest tests.
 */
export const createTodo = jest.fn(
  async (_prevState: ActionState | null, _formData: FormData): Promise<ActionState> => {
    return { success: true, message: 'Todo created' };
  }
);

export const updateTodo = jest.fn(
  async (_id: number, _data: Record<string, unknown>): Promise<ActionState> => {
    return { success: true, message: 'Todo updated' };
  }
);

export const toggleTodo = jest.fn(
  async (_id: number, _completed: boolean): Promise<ActionState> => {
    return { success: true, message: 'Todo toggled' };
  }
);

export const deleteTodo = jest.fn(
  async (_id: number): Promise<ActionState> => {
    return { success: true, message: 'Todo deleted' };
  }
);

export const clearCompleted = jest.fn(
  async (): Promise<ActionState> => {
    return { success: true, message: 'Completed todos cleared' };
  }
);

export type { ActionState };
