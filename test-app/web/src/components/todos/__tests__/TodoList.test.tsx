import { render, screen } from '@testing-library/react';
import { TodoList } from '../TodoList';
import type { Todo, TodoMeta } from '@/types/todo';

// Mock the TodoItem component to isolate TodoList tests
jest.mock('../TodoItem', () => ({
  TodoItem: ({ todo }: { todo: Todo }) => (
    <li data-testid={`todo-item-${todo.id}`}>{todo.title}</li>
  ),
}));

const mockTodos: Todo[] = [
  {
    id: 1,
    title: 'Buy groceries',
    completed: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    title: 'Write tests',
    completed: true,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
  {
    id: 3,
    title: 'Deploy app',
    completed: false,
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-03T00:00:00Z',
  },
];

const mockMeta: TodoMeta = {
  total: 3,
  completed: 1,
  active: 2,
};

describe('TodoList', () => {
  it('renders empty state when no todos', () => {
    const emptyMeta: TodoMeta = {
      total: 0,
      completed: 0,
      active: 0,
    };

    render(<TodoList todos={[]} meta={emptyMeta} />);

    expect(screen.getByText('No todos yet')).toBeInTheDocument();
    expect(screen.getByText('Add a todo to get started')).toBeInTheDocument();
  });

  it('renders list of todos', () => {
    render(<TodoList todos={mockTodos} meta={mockMeta} />);

    expect(screen.getByTestId('todo-item-1')).toBeInTheDocument();
    expect(screen.getByTestId('todo-item-2')).toBeInTheDocument();
    expect(screen.getByTestId('todo-item-3')).toBeInTheDocument();
  });

  it('displays correct stats with singular item', () => {
    const singleTodo: Todo[] = [mockTodos[0]];
    const singleMeta: TodoMeta = {
      total: 1,
      completed: 0,
      active: 1,
    };

    render(<TodoList todos={singleTodo} meta={singleMeta} />);

    expect(screen.getByText('1 item left')).toBeInTheDocument();
    expect(screen.getByText('0 completed / 1 total')).toBeInTheDocument();
  });

  it('displays correct stats with plural items', () => {
    render(<TodoList todos={mockTodos} meta={mockMeta} />);

    expect(screen.getByText('2 items left')).toBeInTheDocument();
    expect(screen.getByText('1 completed / 3 total')).toBeInTheDocument();
  });

  it('displays all todos in order', () => {
    render(<TodoList todos={mockTodos} meta={mockMeta} />);

    const todoItems = screen.getAllByTestId(/^todo-item-/);
    expect(todoItems).toHaveLength(3);
  });

  it('handles zero active items correctly', () => {
    const allCompletedTodos: Todo[] = [
      { ...mockTodos[0], completed: true },
      { ...mockTodos[1], completed: true },
    ];
    const allCompletedMeta: TodoMeta = {
      total: 2,
      completed: 2,
      active: 0,
    };

    render(<TodoList todos={allCompletedTodos} meta={allCompletedMeta} />);

    expect(screen.getByText('0 items left')).toBeInTheDocument();
    expect(screen.getByText('2 completed / 2 total')).toBeInTheDocument();
  });
});
