# Container Examples

> **Note:** These examples use plain HTML/JSX. Replace with components from your
> project's configured UI library as specified in the style guides.

## Example 1: List Container

Fetches a list of items and renders a list component. Handles loading, error,
and empty states.

```typescript
// src/containers/ProjectListContainer.tsx
'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { fetchProjectsApi, deleteProjectApi } from '@/services/projects';
import { ProjectList } from '@/components/ProjectList';

type Project = {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'archived' | 'draft';
  updatedAt: string;
};

/** Fetches and manages the project list, delegates rendering to ProjectList */
export function ProjectListContainer() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await fetchProjectsApi();
        setProjects(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load projects');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleDelete = useCallback(async (id: string) => {
    try {
      await deleteProjectApi(id);
      setProjects((prev) => prev.filter((p) => p.id !== id));
      // Show success notification using your UI library
    } catch {
      // Show error notification using your UI library
    }
  }, []);

  const handleCreate = useCallback(() => {
    router.push('/projects/new');
  }, [router]);

  if (loading) {
    return <div className="loading-spinner" aria-label="Loading" />;
  }

  if (error) {
    return (
      <div role="alert" className="alert alert-error">
        <h3>Error</h3>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">Projects</h2>
        <button onClick={handleCreate} className="btn btn-primary">New Project</button>
      </div>
      <ProjectList projects={projects} onDelete={handleDelete} />
    </div>
  );
}
```

---

## Example 2: Detail Container

Fetches a single item by ID and renders a detail component.

```typescript
// src/containers/ProjectDetailContainer.tsx
'use client';

import { useState, useEffect } from 'react';
import { fetchProjectApi } from '@/services/projects';
import { ProjectDetail } from '@/components/ProjectDetail';

type Project = {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'archived' | 'draft';
  createdAt: string;
  updatedAt: string;
  members: { id: string; name: string; role: string }[];
};

type ProjectDetailContainerProps = {
  id: string;
};

/** Fetches a single project and renders the detail view */
export function ProjectDetailContainer({ id }: ProjectDetailContainerProps) {
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await fetchProjectApi(id);
        setProject(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load project');
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  if (loading) return <div className="loading-spinner" aria-label="Loading" />;
  if (error) return <div role="alert" className="alert alert-error">{error}</div>;
  if (!project) return <div role="alert" className="alert alert-warning">Project not found</div>;

  return <ProjectDetail project={project} />;
}
```

---

## Example 3: Create Form Container

Handles form submission for creating a new resource.

```typescript
// src/containers/CreateProjectContainer.tsx
'use client';

import { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { createProjectApi } from '@/services/projects';
import { ProjectForm } from '@/components/ProjectForm';

type CreateProjectPayload = {
  name: string;
  description: string;
};

/** Handles project creation flow: form submission, API call, navigation */
export function CreateProjectContainer() {
  const router = useRouter();

  const handleSubmit = useCallback(
    async (values: CreateProjectPayload) => {
      try {
        const project = await createProjectApi(values);
        // Show success notification using your UI library
        router.push(`/projects/${project.id}`);
      } catch {
        // Show error notification using your UI library
      }
    },
    [router]
  );

  const handleCancel = useCallback(() => {
    router.push('/projects');
  }, [router]);

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">New Project</h2>
      <ProjectForm onSubmit={handleSubmit} onCancel={handleCancel} />
    </div>
  );
}
```

---

## Example 4: Edit Form Container

Fetches existing data and handles form submission for editing.

```typescript
// src/containers/EditProjectContainer.tsx
'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { fetchProjectApi, updateProjectApi } from '@/services/projects';
import { ProjectForm } from '@/components/ProjectForm';

type Project = {
  id: string;
  name: string;
  description: string;
};

type EditProjectContainerProps = {
  id: string;
};

/** Fetches project data and handles the edit form submission */
export function EditProjectContainer({ id }: EditProjectContainerProps) {
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await fetchProjectApi(id);
        setProject(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load project');
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const handleSubmit = useCallback(
    async (values: { name: string; description: string }) => {
      try {
        await updateProjectApi(id, values);
        // Show success notification using your UI library
        router.push(`/projects/${id}`);
      } catch {
        // Show error notification using your UI library
      }
    },
    [id, router]
  );

  const handleCancel = useCallback(() => {
    router.push(`/projects/${id}`);
  }, [id, router]);

  if (loading) return <div className="loading-spinner" aria-label="Loading" />;
  if (error) return <div role="alert" className="alert alert-error">{error}</div>;
  if (!project) return <div role="alert" className="alert alert-warning">Project not found</div>;

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">Edit {project.name}</h2>
      <ProjectForm
        initialValues={{ name: project.name, description: project.description }}
        onSubmit={handleSubmit}
        onCancel={handleCancel}
        submitLabel="Save Changes"
      />
    </div>
  );
}
```

---

## Example 5: Container with Filters and Pagination

```typescript
// src/containers/ProjectSearchContainer.tsx
'use client';

import { useState, useEffect, useCallback } from 'react';
import { fetchProjectsApi } from '@/services/projects';
import { ProjectList } from '@/components/ProjectList';
import { SearchBar } from '@/components/SearchBar';

type Project = {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'archived' | 'draft';
  updatedAt: string;
};

/** Project list with search and pagination support */
export function ProjectSearchContainer() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const loadProjects = useCallback(async (searchQuery: string, pageNum: number) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchProjectsApi({ query: searchQuery, page: pageNum });
      setProjects(result.data);
      setTotalPages(result.totalPages);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    (async () => {
      await loadProjects(query, page);
    })();
  }, [query, page, loadProjects]);

  const handleSearch = useCallback((newQuery: string) => {
    setQuery(newQuery);
    setPage(1); // Reset to first page on new search
  }, []);

  if (error) {
    return <div role="alert" className="alert alert-error">{error}</div>;
  }

  return (
    <div className="space-y-4">
      <SearchBar onSearch={handleSearch} />
      <div className="relative min-h-[200px]">
        {loading && <div className="loading-overlay" />}
        <ProjectList projects={projects} />
      </div>
      {totalPages > 1 && (
        <nav className="flex justify-center gap-2">
          {Array.from({ length: totalPages }, (_, i) => (
            <button
              key={i + 1}
              onClick={() => setPage(i + 1)}
              className={`btn btn-sm ${page === i + 1 ? 'btn-primary' : 'btn-secondary'}`}
            >
              {i + 1}
            </button>
          ))}
        </nav>
      )}
    </div>
  );
}
```

---

## Container Test Pattern

```typescript
// src/containers/ProjectListContainer.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ProjectListContainer } from './ProjectListContainer';
import * as projectsService from '@/services/projects';

jest.mock('@/services/projects');
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
}));

const mockFetchProjects = projectsService.fetchProjectsApi as jest.MockedFunction<
  typeof projectsService.fetchProjectsApi
>;

describe('ProjectListContainer', () => {
  it('shows loading state initially', () => {
    mockFetchProjects.mockReturnValue(new Promise(() => {}));
    render(<ProjectListContainer />);
    expect(screen.getByLabelText('Loading')).toBeInTheDocument();
  });

  it('renders projects after fetch', async () => {
    mockFetchProjects.mockResolvedValue([
      { id: '1', name: 'Alpha', description: 'First', status: 'active', updatedAt: '' },
    ]);

    render(<ProjectListContainer />);

    await waitFor(() => {
      expect(screen.getByText('Alpha')).toBeInTheDocument();
    });
  });

  it('shows error on fetch failure', async () => {
    mockFetchProjects.mockRejectedValue(new Error('Network error'));

    render(<ProjectListContainer />);

    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });
});
```
