'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import { useTransition } from 'react';
import { clearCompleted } from '@/lib/actions/todos';

type FilterOption = 'all' | 'active' | 'completed';

const FILTERS: { value: FilterOption; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'active', label: 'Active' },
  { value: 'completed', label: 'Completed' },
];

type TodoFiltersProps = {
  hasCompleted: boolean;
};

/**
 * Client Component for filtering todos and clearing completed items.
 */
export function TodoFilters({ hasCompleted }: TodoFiltersProps) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  const currentFilter = (searchParams.get('filter') as FilterOption) ?? 'all';

  const handleFilterChange = (filter: FilterOption) => {
    const params = new URLSearchParams(searchParams);

    if (filter === 'all') {
      params.delete('filter');
    } else {
      params.set('filter', filter);
    }

    const query = params.toString();
    router.push(query ? `/?${query}` : '/');
  };

  const handleClearCompleted = () => {
    startTransition(async () => {
      await clearCompleted();
    });
  };

  return (
    <div className="px-4 py-2 border-t border-gray-200 flex justify-between items-center">
      <div className="flex gap-1">
        {FILTERS.map(({ value, label }) => (
          <button
            key={value}
            onClick={() => handleFilterChange(value)}
            className={`px-3 py-1 text-sm rounded border transition-colors ${
              currentFilter === value
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:border-gray-300'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {hasCompleted && (
        <button
          onClick={handleClearCompleted}
          disabled={isPending}
          className="text-sm text-gray-500 hover:text-red-500 hover:underline transition-colors disabled:opacity-50"
        >
          {isPending ? 'Clearing...' : 'Clear completed'}
        </button>
      )}
    </div>
  );
}
