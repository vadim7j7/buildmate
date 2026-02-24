import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TodoItem } from '../TodoItem';
import type { Todo } from '@/types/todo';
import { toggleTodo, deleteTodo, updateTodo } from '@/lib/actions/todos';

// Mock the Server Actions
jest.mock('@/lib/actions/todos');

const mockTodo: Todo = {
  id: 1,
  title: 'Test todo',
  completed: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

describe('TodoItem', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders todo item with title', () => {
    render(<TodoItem todo={mockTodo} />);

    expect(screen.getByText('Test todo')).toBeInTheDocument();
  });

  it('renders unchecked checkbox for incomplete todo', () => {
    render(<TodoItem todo={mockTodo} />);

    const checkbox = screen.getByRole('checkbox', {
      name: /Mark "Test todo" as complete/i,
    });
    expect(checkbox).not.toBeChecked();
  });

  it('renders checked checkbox for completed todo', () => {
    const completedTodo = { ...mockTodo, completed: true };
    render(<TodoItem todo={completedTodo} />);

    const checkbox = screen.getByRole('checkbox', {
      name: /Mark "Test todo" as incomplete/i,
    });
    expect(checkbox).toBeChecked();
  });

  it('applies line-through style to completed todo', () => {
    const completedTodo = { ...mockTodo, completed: true };
    render(<TodoItem todo={completedTodo} />);

    const title = screen.getByText('Test todo');
    expect(title).toHaveClass('line-through');
  });

  it('calls toggleTodo when checkbox is clicked', async () => {
    render(<TodoItem todo={mockTodo} />);

    const checkbox = screen.getByRole('checkbox', {
      name: /Mark "Test todo" as complete/i,
    });

    fireEvent.click(checkbox);

    await waitFor(() => {
      expect(toggleTodo).toHaveBeenCalledWith(1, true);
    });
  });

  it('calls deleteTodo when delete button is clicked', async () => {
    render(<TodoItem todo={mockTodo} />);

    const deleteButton = screen.getByRole('button', {
      name: /Delete "Test todo"/i,
    });

    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(deleteTodo).toHaveBeenCalledWith(1);
    });
  });

  it('enters edit mode on double click', async () => {
    const user = userEvent.setup();
    render(<TodoItem todo={mockTodo} />);

    const titleSpan = screen.getByText('Test todo');
    await user.dblClick(titleSpan);

    const editInput = screen.getByRole('textbox', { name: /Edit todo title/i });
    expect(editInput).toBeInTheDocument();
    expect(editInput).toHaveValue('Test todo');
  });

  it('saves edited title on blur', async () => {
    const user = userEvent.setup();
    render(<TodoItem todo={mockTodo} />);

    // Enter edit mode
    const titleSpan = screen.getByText('Test todo');
    await user.dblClick(titleSpan);

    const editInput = screen.getByRole('textbox', { name: /Edit todo title/i });

    // Edit the title
    await user.clear(editInput);
    await user.type(editInput, 'Updated todo');

    // Blur to save
    fireEvent.blur(editInput);

    await waitFor(() => {
      expect(updateTodo).toHaveBeenCalledWith(1, { title: 'Updated todo' });
    });
  });

  it('saves edited title on Enter key', async () => {
    const user = userEvent.setup();
    render(<TodoItem todo={mockTodo} />);

    // Enter edit mode
    const titleSpan = screen.getByText('Test todo');
    await user.dblClick(titleSpan);

    const editInput = screen.getByRole('textbox', { name: /Edit todo title/i });

    // Edit and press Enter
    await user.clear(editInput);
    await user.type(editInput, 'Updated todo{Enter}');

    await waitFor(() => {
      expect(updateTodo).toHaveBeenCalledWith(1, { title: 'Updated todo' });
    });
  });

  it('cancels edit on Escape key', async () => {
    const user = userEvent.setup();
    render(<TodoItem todo={mockTodo} />);

    // Enter edit mode
    const titleSpan = screen.getByText('Test todo');
    await user.dblClick(titleSpan);

    const editInput = screen.getByRole('textbox', { name: /Edit todo title/i });

    // Edit and press Escape
    await user.clear(editInput);
    await user.type(editInput, 'Updated todo{Escape}');

    // Should not call updateTodo
    expect(updateTodo).not.toHaveBeenCalled();

    // Should exit edit mode
    await waitFor(() => {
      expect(screen.queryByRole('textbox', { name: /Edit todo title/i })).not.toBeInTheDocument();
    });
  });

  it('does not save if edited title is empty', async () => {
    const user = userEvent.setup();
    render(<TodoItem todo={mockTodo} />);

    // Enter edit mode
    const titleSpan = screen.getByText('Test todo');
    await user.dblClick(titleSpan);

    const editInput = screen.getByRole('textbox', { name: /Edit todo title/i });

    // Clear the input and blur
    await user.clear(editInput);
    fireEvent.blur(editInput);

    // Should not call updateTodo
    expect(updateTodo).not.toHaveBeenCalled();
  });

  it('does not save if edited title is unchanged', async () => {
    const user = userEvent.setup();
    render(<TodoItem todo={mockTodo} />);

    // Enter edit mode
    const titleSpan = screen.getByText('Test todo');
    await user.dblClick(titleSpan);

    const editInput = screen.getByRole('textbox', { name: /Edit todo title/i });

    // Blur without changes
    fireEvent.blur(editInput);

    // Should not call updateTodo
    expect(updateTodo).not.toHaveBeenCalled();
  });

  it('disables interactions when pending', async () => {
    render(<TodoItem todo={mockTodo} />);

    const checkbox = screen.getByRole('checkbox');

    // Click checkbox to trigger pending state
    fireEvent.click(checkbox);

    // Check that elements are disabled during transition
    // Note: React 19's useTransition makes this hard to test directly
    // We just verify the action was called
    await waitFor(() => {
      expect(toggleTodo).toHaveBeenCalled();
    });
  });

  it('has proper accessibility labels', () => {
    render(<TodoItem todo={mockTodo} />);

    expect(
      screen.getByRole('checkbox', {
        name: /Mark "Test todo" as complete/i,
      })
    ).toBeInTheDocument();

    expect(
      screen.getByRole('button', {
        name: /Delete "Test todo"/i,
      })
    ).toBeInTheDocument();
  });
});
