import { TodoItem } from './TodoItem';
import type { Todo, TodoMeta } from '@/types/todo';

type TodoListProps = {
  todos: Todo[];
  meta: TodoMeta;
};

/**
 * Server Component that displays a list of todos with stats.
 */
export function TodoList({ todos, meta }: TodoListProps) {
  if (todos.length === 0) {
    return (
      <div className="py-12 text-center text-gray-500">
        <p className="text-lg">No todos yet</p>
        <p className="text-sm mt-1">Add a todo to get started</p>
      </div>
    );
  }

  return (
    <div>
      <ul className="divide-y divide-gray-200">
        {todos.map((todo) => (
          <TodoItem key={todo.id} todo={todo} />
        ))}
      </ul>
      <div className="px-4 py-3 text-sm text-gray-500 border-t border-gray-200 flex justify-between items-center">
        <span>
          {meta.active} {meta.active === 1 ? 'item' : 'items'} left
        </span>
        <span className="text-xs">
          {meta.completed} completed / {meta.total} total
        </span>
      </div>
    </div>
  );
}
