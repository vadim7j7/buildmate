'use client';

import { useActionState, useRef, useEffect } from 'react';
import { createTodo, type ActionState } from '@/lib/actions/todos';

const initialState: ActionState = {
  success: false,
  message: '',
};

/**
 * Client Component for adding new todos using Server Actions.
 */
export function AddTodoForm() {
  const [state, formAction, isPending] = useActionState(createTodo, initialState);
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    if (state.success && formRef.current) {
      formRef.current.reset();
    }
  }, [state]);

  return (
    <form ref={formRef} action={formAction} className="relative">
      <input
        type="text"
        name="title"
        placeholder="What needs to be done?"
        disabled={isPending}
        className="w-full px-4 py-4 text-lg border-b border-gray-200 focus:outline-none focus:border-blue-500 placeholder:text-gray-400 placeholder:italic"
        aria-label="New todo title"
        autoComplete="off"
      />
      {isPending && (
        <div className="absolute right-4 top-1/2 -translate-y-1/2">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
        </div>
      )}
      {state.errors?.title && (
        <p className="px-4 py-2 text-sm text-red-500">{state.errors.title[0]}</p>
      )}
    </form>
  );
}
