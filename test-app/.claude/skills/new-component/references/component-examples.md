# React Component Examples

> **Note:** These examples use plain HTML/JSX. Replace with components from your
> project's configured UI library as specified in the style guides.

## Example 1: Client Component with State and Events

A client component that uses hooks, manages state, and handles user events.

```typescript
// src/components/SearchBar.tsx
'use client';

import { useState, useCallback } from 'react';

type SearchBarProps = {
  /** Callback fired when user submits a search query */
  onSearch: (query: string) => void;
  /** Placeholder text for the search input */
  placeholder?: string;
  /** Whether the search is currently loading */
  loading?: boolean;
};

/** Search input with submit and clear functionality */
export function SearchBar({
  onSearch,
  placeholder = 'Search...',
  loading = false,
}: SearchBarProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = useCallback(() => {
    if (query.trim()) {
      onSearch(query.trim());
    }
  }, [query, onSearch]);

  const handleClear = useCallback(() => {
    setQuery('');
    onSearch('');
  }, [onSearch]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  return (
    <div className="flex items-center gap-2">
      <div className="relative flex-1">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={loading}
          className="w-full pl-8 pr-8 py-2 border rounded-lg"
        />
        {query && (
          <button
            onClick={handleClear}
            aria-label="Clear search"
            className="absolute right-2 top-1/2 -translate-y-1/2"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
}
```

```typescript
// src/components/SearchBar.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SearchBar } from './SearchBar';

describe('SearchBar', () => {
  const defaultProps = {
    onSearch: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the search input', () => {
    render(<SearchBar {...defaultProps} />);
    expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument();
  });

  it('uses custom placeholder', () => {
    render(<SearchBar {...defaultProps} placeholder="Find projects..." />);
    expect(screen.getByPlaceholderText('Find projects...')).toBeInTheDocument();
  });

  it('calls onSearch when Enter is pressed', async () => {
    const user = userEvent.setup();
    render(<SearchBar {...defaultProps} />);

    await user.type(screen.getByPlaceholderText('Search...'), 'react');
    await user.keyboard('{Enter}');

    expect(defaultProps.onSearch).toHaveBeenCalledWith('react');
  });

  it('clears input and calls onSearch with empty string on clear', async () => {
    const user = userEvent.setup();
    render(<SearchBar {...defaultProps} />);

    await user.type(screen.getByPlaceholderText('Search...'), 'test');
    await user.click(screen.getByLabelText('Clear search'));

    expect(screen.getByPlaceholderText('Search...')).toHaveValue('');
    expect(defaultProps.onSearch).toHaveBeenCalledWith('');
  });

  it('disables input when loading', () => {
    render(<SearchBar {...defaultProps} loading />);
    expect(screen.getByPlaceholderText('Search...')).toBeDisabled();
  });
});
```

---

## Example 2: Server Component (Presentational)

A server component that only displays data -- no hooks, events, or browser APIs.

```typescript
// src/components/ProjectCard.tsx
import Link from 'next/link';

type ProjectCardProps = {
  /** Unique project identifier */
  id: string;
  /** Project display name */
  name: string;
  /** Brief project description */
  description: string;
  /** Current project status */
  status: 'active' | 'archived' | 'draft';
  /** ISO date string of last update */
  updatedAt: string;
};

const statusClassMap = {
  active: 'bg-green-100 text-green-800',
  archived: 'bg-gray-100 text-gray-800',
  draft: 'bg-yellow-100 text-yellow-800',
} as const;

/** Displays a project summary as a clickable card */
export function ProjectCard({ id, name, description, status, updatedAt }: ProjectCardProps) {
  const formattedDate = new Date(updatedAt).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <Link href={`/projects/${id}`} className="block p-4 rounded-lg border shadow-sm hover:shadow-md transition-shadow">
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <h3 className="font-semibold text-lg">{name}</h3>
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusClassMap[status]}`}>
            {status}
          </span>
        </div>

        <p className="text-sm text-gray-600 line-clamp-2">{description}</p>

        <p className="text-xs text-gray-400">Updated {formattedDate}</p>
      </div>
    </Link>
  );
}
```

```typescript
// src/components/ProjectCard.test.tsx
import { render, screen } from '@testing-library/react';
import { ProjectCard } from './ProjectCard';

describe('ProjectCard', () => {
  const defaultProps = {
    id: 'proj-1',
    name: 'My Project',
    description: 'A test project for unit testing',
    status: 'active' as const,
    updatedAt: '2024-06-15T10:00:00Z',
  };

  it('renders the project name', () => {
    render(<ProjectCard {...defaultProps} />);
    expect(screen.getByText('My Project')).toBeInTheDocument();
  });

  it('renders the description', () => {
    render(<ProjectCard {...defaultProps} />);
    expect(screen.getByText('A test project for unit testing')).toBeInTheDocument();
  });

  it('renders the status badge', () => {
    render(<ProjectCard {...defaultProps} />);
    expect(screen.getByText('active')).toBeInTheDocument();
  });

  it('renders archived badge', () => {
    render(<ProjectCard {...defaultProps} status="archived" />);
    expect(screen.getByText('archived')).toBeInTheDocument();
  });

  it('links to the project detail page', () => {
    render(<ProjectCard {...defaultProps} />);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/projects/proj-1');
  });

  it('displays formatted date', () => {
    render(<ProjectCard {...defaultProps} />);
    expect(screen.getByText(/Jun 15, 2024/)).toBeInTheDocument();
  });
});
```

---

## Example 3: Component with Loading States

A component that handles loading, empty, and error states.

```typescript
// src/components/ProjectList.tsx
import { ProjectCard } from './ProjectCard';

type Project = {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'archived' | 'draft';
  updatedAt: string;
};

type ProjectListProps = {
  /** Array of projects to display */
  projects: Project[];
  /** Whether data is still loading */
  loading?: boolean;
  /** Optional callback when a project delete is requested */
  onDelete?: (id: string) => void;
};

/** Renders a grid of project cards with loading and empty states */
export function ProjectList({ projects, loading = false, onDelete }: ProjectListProps) {
  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="spinner" aria-label="Loading" />
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="flex justify-center py-12">
        <p className="text-gray-500 text-lg">
          No projects found. Create your first project to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {projects.map((project) => (
        <ProjectCard key={project.id} {...project} />
      ))}
    </div>
  );
}
```

---

## Example 4: Component with Dialog/Modal

```typescript
// src/components/ConfirmDialog.tsx
'use client';

type ConfirmDialogProps = {
  /** Whether the dialog is open */
  opened: boolean;
  /** Callback when the dialog is closed */
  onClose: () => void;
  /** Callback when the user confirms the action */
  onConfirm: () => void;
  /** Dialog title */
  title: string;
  /** Confirmation message */
  message: string;
  /** Label for the confirm button */
  confirmLabel?: string;
  /** Whether the confirm action is in progress */
  loading?: boolean;
};

/** Reusable confirmation dialog for destructive actions */
export function ConfirmDialog({
  opened,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Confirm',
  loading = false,
}: ConfirmDialogProps) {
  if (!opened) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div className="bg-white rounded-lg p-6 max-w-md w-full shadow-xl" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-lg font-semibold mb-2">{title}</h2>
        <p className="text-sm text-gray-600 mb-4">{message}</p>
        <div className="flex justify-end gap-2">
          <button onClick={onClose} disabled={loading} className="btn btn-secondary">
            Cancel
          </button>
          <button onClick={onConfirm} disabled={loading} className="btn btn-danger">
            {loading ? 'Loading...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
```
