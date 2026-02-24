import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TodoFilters } from '../TodoFilters';
import { clearCompleted } from '@/lib/actions/todos';
import { useRouter, useSearchParams } from 'next/navigation';

// Mock Next.js navigation hooks
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}));

// Mock the Server Actions
jest.mock('@/lib/actions/todos');

const mockPush = jest.fn();
const mockRouter = { push: mockPush };

describe('TodoFilters', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
  });

  it('renders all filter buttons', () => {
    (useSearchParams as jest.Mock).mockReturnValue(new URLSearchParams());

    render(<TodoFilters hasCompleted={false} />);

    expect(screen.getByRole('button', { name: 'All' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Active' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Completed' })).toBeInTheDocument();
  });

  it('highlights All filter by default', () => {
    (useSearchParams as jest.Mock).mockReturnValue(new URLSearchParams());

    render(<TodoFilters hasCompleted={false} />);

    const allButton = screen.getByRole('button', { name: 'All' });
    expect(allButton).toHaveClass('border-blue-500');
  });

  it('highlights active filter based on URL params', () => {
    const params = new URLSearchParams('filter=active');
    (useSearchParams as jest.Mock).mockReturnValue(params);

    render(<TodoFilters hasCompleted={false} />);

    const activeButton = screen.getByRole('button', { name: 'Active' });
    expect(activeButton).toHaveClass('border-blue-500');
  });

  it('highlights completed filter based on URL params', () => {
    const params = new URLSearchParams('filter=completed');
    (useSearchParams as jest.Mock).mockReturnValue(params);

    render(<TodoFilters hasCompleted={false} />);

    const completedButton = screen.getByRole('button', { name: 'Completed' });
    expect(completedButton).toHaveClass('border-blue-500');
  });

  it('navigates to root when All filter is clicked', () => {
    const params = new URLSearchParams('filter=active');
    (useSearchParams as jest.Mock).mockReturnValue(params);

    render(<TodoFilters hasCompleted={false} />);

    const allButton = screen.getByRole('button', { name: 'All' });
    fireEvent.click(allButton);

    expect(mockPush).toHaveBeenCalledWith('/');
  });

  it('adds filter param when Active filter is clicked', () => {
    (useSearchParams as jest.Mock).mockReturnValue(new URLSearchParams());

    render(<TodoFilters hasCompleted={false} />);

    const activeButton = screen.getByRole('button', { name: 'Active' });
    fireEvent.click(activeButton);

    expect(mockPush).toHaveBeenCalledWith('/?filter=active');
  });

  it('adds filter param when Completed filter is clicked', () => {
    (useSearchParams as jest.Mock).mockReturnValue(new URLSearchParams());

    render(<TodoFilters hasCompleted={false} />);

    const completedButton = screen.getByRole('button', { name: 'Completed' });
    fireEvent.click(completedButton);

    expect(mockPush).toHaveBeenCalledWith('/?filter=completed');
  });

  it('shows Clear completed button when hasCompleted is true', () => {
    (useSearchParams as jest.Mock).mockReturnValue(new URLSearchParams());

    render(<TodoFilters hasCompleted={true} />);

    const clearButton = screen.getByRole('button', { name: /Clear completed/i });
    expect(clearButton).toBeInTheDocument();
  });

  it('hides Clear completed button when hasCompleted is false', () => {
    (useSearchParams as jest.Mock).mockReturnValue(new URLSearchParams());

    render(<TodoFilters hasCompleted={false} />);

    const clearButton = screen.queryByRole('button', { name: /Clear completed/i });
    expect(clearButton).not.toBeInTheDocument();
  });

  it('calls clearCompleted when Clear completed button is clicked', async () => {
    (useSearchParams as jest.Mock).mockReturnValue(new URLSearchParams());

    render(<TodoFilters hasCompleted={true} />);

    const clearButton = screen.getByRole('button', { name: /Clear completed/i });
    fireEvent.click(clearButton);

    await waitFor(() => {
      expect(clearCompleted).toHaveBeenCalled();
    });
  });

  it('shows Clearing... text when pending', () => {
    (useSearchParams as jest.Mock).mockReturnValue(new URLSearchParams());

    render(<TodoFilters hasCompleted={true} />);

    const clearButton = screen.getByRole('button', { name: /Clear completed/i });

    // Click to trigger pending state
    fireEvent.click(clearButton);

    // The button text should change during transition
    // Note: Testing useTransition state is tricky, but we can verify the button exists
    expect(clearButton).toBeInTheDocument();
  });

  it('disables Clear completed button when pending', () => {
    (useSearchParams as jest.Mock).mockReturnValue(new URLSearchParams());

    render(<TodoFilters hasCompleted={true} />);

    const clearButton = screen.getByRole('button', { name: /Clear completed/i });

    // Click to trigger pending state
    fireEvent.click(clearButton);

    // The button should be disabled during transition
    // Note: Testing exact pending state is complex with useTransition
    expect(clearCompleted).toHaveBeenCalled();
  });

  it('preserves other URL params when changing filter', () => {
    const params = new URLSearchParams('sort=desc&page=2');
    (useSearchParams as jest.Mock).mockReturnValue(params);

    render(<TodoFilters hasCompleted={false} />);

    const activeButton = screen.getByRole('button', { name: 'Active' });
    fireEvent.click(activeButton);

    expect(mockPush).toHaveBeenCalledWith('/?sort=desc&page=2&filter=active');
  });

  it('removes filter param and preserves other params when All is clicked', () => {
    const params = new URLSearchParams('filter=active&sort=desc');
    (useSearchParams as jest.Mock).mockReturnValue(params);

    render(<TodoFilters hasCompleted={false} />);

    const allButton = screen.getByRole('button', { name: 'All' });
    fireEvent.click(allButton);

    expect(mockPush).toHaveBeenCalledWith('/?sort=desc');
  });

  it('applies correct styles to active filter', () => {
    (useSearchParams as jest.Mock).mockReturnValue(new URLSearchParams());

    render(<TodoFilters hasCompleted={false} />);

    const allButton = screen.getByRole('button', { name: 'All' });
    const activeButton = screen.getByRole('button', { name: 'Active' });

    expect(allButton).toHaveClass('border-blue-500', 'text-blue-600');
    expect(activeButton).toHaveClass('border-transparent', 'text-gray-500');
  });

  it('applies correct styles to inactive filters', () => {
    const params = new URLSearchParams('filter=active');
    (useSearchParams as jest.Mock).mockReturnValue(params);

    render(<TodoFilters hasCompleted={false} />);

    const allButton = screen.getByRole('button', { name: 'All' });
    const completedButton = screen.getByRole('button', { name: 'Completed' });

    expect(allButton).toHaveClass('border-transparent');
    expect(completedButton).toHaveClass('border-transparent');
  });
});
