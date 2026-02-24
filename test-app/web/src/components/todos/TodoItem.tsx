'use client';

import { useState, useTransition, useRef, useEffect } from 'react';
import { toggleTodo, deleteTodo, updateTodo } from '@/lib/actions/todos';
import type { Todo } from '@/types/todo';

type TodoItemProps = {
  todo: Todo;
};

/**
 * Client Component for rendering a single todo item with toggle, edit, and delete functionality.
 */
export function TodoItem({ todo }: TodoItemProps) {
  const [isPending, startTransition] = useTransition();
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(todo.title);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleToggle = () => {
    startTransition(async () => {
      await toggleTodo(todo.id, !todo.completed);
    });
  };

  const handleDelete = () => {
    startTransition(async () => {
      await deleteTodo(todo.id);
    });
  };

  const handleDoubleClick = () => {
    setIsEditing(true);
    setEditTitle(todo.title);
  };

  const handleEditSubmit = () => {
    if (editTitle.trim() === '') {
      setEditTitle(todo.title);
      setIsEditing(false);
      return;
    }

    if (editTitle.trim() !== todo.title) {
      startTransition(async () => {
        await updateTodo(todo.id, { title: editTitle.trim() });
      });
    }
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleEditSubmit();
    } else if (e.key === 'Escape') {
      setEditTitle(todo.title);
      setIsEditing(false);
    }
  };

  return (
    <li
      className={`group flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors ${
        isPending ? 'opacity-50' : ''
      }`}
    >
      <input
        type="checkbox"
        checked={todo.completed}
        onChange={handleToggle}
        disabled={isPending}
        className="h-5 w-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
        aria-label={`Mark "${todo.title}" as ${todo.completed ? 'incomplete' : 'complete'}`}
      />

      {isEditing ? (
        <input
          ref={inputRef}
          type="text"
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onBlur={handleEditSubmit}
          onKeyDown={handleKeyDown}
          className="flex-1 px-2 py-1 border border-blue-500 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Edit todo title"
        />
      ) : (
        <span
          onDoubleClick={handleDoubleClick}
          className={`flex-1 cursor-text ${
            todo.completed ? 'line-through text-gray-400' : 'text-gray-900'
          }`}
        >
          {todo.title}
        </span>
      )}

      <button
        onClick={handleDelete}
        disabled={isPending}
        className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-all focus:opacity-100"
        aria-label={`Delete "${todo.title}"`}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </li>
  );
}
