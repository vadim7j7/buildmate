# React Component Examples

## Example 1: Client Component with State and Events

A client component that uses hooks, manages state, and handles user events.

```typescript
// src/components/SearchBar.tsx
'use client';

import { useState, useCallback } from 'react';
import { TextInput, ActionIcon, Group } from '@mantine/core';
import { IconSearch, IconX } from '@tabler/icons-react';

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
    <Group gap="xs">
      <TextInput
        value={query}
        onChange={(e) => setQuery(e.currentTarget.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        leftSection={<IconSearch size={16} />}
        rightSection={
          query ? (
            <ActionIcon variant="subtle" size="sm" onClick={handleClear} aria-label="Clear search">
              <IconX size={14} />
            </ActionIcon>
          ) : null
        }
        disabled={loading}
        style={{ flex: 1 }}
      />
    </Group>
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
import { Card, Text, Badge, Group, Stack } from '@mantine/core';
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

const statusColorMap = {
  active: 'green',
  archived: 'gray',
  draft: 'yellow',
} as const;

/** Displays a project summary as a clickable card */
export function ProjectCard({ id, name, description, status, updatedAt }: ProjectCardProps) {
  const formattedDate = new Date(updatedAt).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <Card shadow="sm" padding="lg" radius="md" withBorder component={Link} href={`/projects/${id}`}>
      <Stack gap="sm">
        <Group justify="space-between">
          <Text fw={600} size="lg">
            {name}
          </Text>
          <Badge color={statusColorMap[status]} variant="light">
            {status}
          </Badge>
        </Group>

        <Text size="sm" c="dimmed" lineClamp={2}>
          {description}
        </Text>

        <Text size="xs" c="dimmed">
          Updated {formattedDate}
        </Text>
      </Stack>
    </Card>
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

  it('renders archived badge with correct styling', () => {
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
import { Stack, Text, SimpleGrid, Center, Loader } from '@mantine/core';
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
      <Center py="xl">
        <Loader size="lg" />
      </Center>
    );
  }

  if (projects.length === 0) {
    return (
      <Center py="xl">
        <Text c="dimmed" size="lg">
          No projects found. Create your first project to get started.
        </Text>
      </Center>
    );
  }

  return (
    <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }} spacing="lg">
      {projects.map((project) => (
        <ProjectCard key={project.id} {...project} />
      ))}
    </SimpleGrid>
  );
}
```

---

## Example 4: Component with Mantine Modal

```typescript
// src/components/ConfirmDialog.tsx
'use client';

import { Modal, Text, Group, Button, Stack } from '@mantine/core';

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
  return (
    <Modal opened={opened} onClose={onClose} title={title} centered>
      <Stack>
        <Text size="sm">{message}</Text>
        <Group justify="flex-end">
          <Button variant="default" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button color="red" onClick={onConfirm} loading={loading}>
            {confirmLabel}
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
```
