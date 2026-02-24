import { Metadata } from 'next';
import { getTodos } from '@/lib/data/todos';
import { TodoList } from '@/components/todos/TodoList';
import { AddTodoForm } from '@/components/todos/AddTodoForm';
import { TodoFilters } from '@/components/todos/TodoFilters';

export const metadata: Metadata = {
  title: 'Todo App',
  description: 'A simple todo application built with Next.js and Server Components',
};

type PageProps = {
  searchParams: Promise<{ filter?: string }>;
};

/**
 * Main page Server Component that fetches todos and renders the todo application.
 */
export default async function HomePage({ searchParams }: PageProps) {
  const { filter } = await searchParams;
  const { data: todos, meta } = await getTodos(filter);

  return (
    <main className="min-h-screen bg-gray-100 py-12">
      <div className="max-w-lg mx-auto">
        <h1 className="text-4xl font-thin text-center text-gray-800 mb-8">
          todos
        </h1>

        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <AddTodoForm />
          <TodoList todos={todos} meta={meta} />
          {todos.length > 0 && <TodoFilters hasCompleted={meta.completed > 0} />}
        </div>

        <footer className="mt-8 text-center text-sm text-gray-500">
          <p>Double-click to edit a todo</p>
        </footer>
      </div>
    </main>
  );
}
