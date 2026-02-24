# React Hook Examples

Reference examples for generating custom React hooks.

## useDebounce

```typescript
import { useState, useEffect } from 'react';

/**
 * Debounce a value, only updating after the specified delay.
 *
 * @param value - The value to debounce
 * @param delay - Delay in milliseconds (default: 500)
 * @returns The debounced value
 *
 * @example
 * const [searchTerm, setSearchTerm] = useState('');
 * const debouncedSearch = useDebounce(searchTerm, 300);
 *
 * useEffect(() => {
 *   // API call with debouncedSearch
 * }, [debouncedSearch]);
 */
export function useDebounce<T>(value: T, delay = 500): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}
```

## useLocalStorage

```typescript
import { useState, useCallback, useEffect } from 'react';

type UseLocalStorageOptions<T> = {
  serializer?: (value: T) => string;
  deserializer?: (value: string) => T;
};

/**
 * Persist state to localStorage with automatic serialization.
 *
 * @param key - The localStorage key
 * @param initialValue - Initial value if key doesn't exist
 * @param options - Serialization options
 * @returns Tuple of [value, setValue, removeValue]
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T,
  options: UseLocalStorageOptions<T> = {}
): [T, (value: T | ((prev: T) => T)) => void, () => void] {
  const { serializer = JSON.stringify, deserializer = JSON.parse } = options;

  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') {
      return initialValue;
    }

    try {
      const item = window.localStorage.getItem(key);
      return item ? deserializer(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      try {
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);
        if (typeof window !== 'undefined') {
          window.localStorage.setItem(key, serializer(valueToStore));
        }
      } catch (error) {
        console.warn(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key, serializer, storedValue]
  );

  const removeValue = useCallback(() => {
    try {
      setStoredValue(initialValue);
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem(key);
      }
    } catch (error) {
      console.warn(`Error removing localStorage key "${key}":`, error);
    }
  }, [key, initialValue]);

  // Sync with other tabs/windows
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === key && e.newValue !== null) {
        setStoredValue(deserializer(e.newValue));
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [key, deserializer]);

  return [storedValue, setValue, removeValue];
}
```

## useMediaQuery

```typescript
import { useState, useEffect } from 'react';

/**
 * Track a CSS media query.
 *
 * @param query - The media query string
 * @returns Whether the media query matches
 *
 * @example
 * const isMobile = useMediaQuery('(max-width: 768px)');
 * const prefersDark = useMediaQuery('(prefers-color-scheme: dark)');
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window === 'undefined') {
      return false;
    }
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const mediaQuery = window.matchMedia(query);
    setMatches(mediaQuery.matches);

    const handler = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, [query]);

  return matches;
}
```

## useClickOutside

```typescript
import { useEffect, useRef, type RefObject } from 'react';

/**
 * Detect clicks outside of an element.
 *
 * @param handler - Callback when click outside occurs
 * @returns Ref to attach to the element
 *
 * @example
 * function Dropdown() {
 *   const [isOpen, setIsOpen] = useState(false);
 *   const ref = useClickOutside(() => setIsOpen(false));
 *
 *   return <div ref={ref}>{isOpen && <Menu />}</div>;
 * }
 */
export function useClickOutside<T extends HTMLElement = HTMLElement>(
  handler: () => void
): RefObject<T> {
  const ref = useRef<T>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent | TouchEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        handler();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('touchstart', handleClickOutside);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [handler]);

  return ref;
}
```

## useAsync

```typescript
import { useState, useCallback, useEffect, useRef } from 'react';

type UseAsyncState<T> = {
  data: T | null;
  isLoading: boolean;
  error: Error | null;
};

type UseAsyncReturn<T, Args extends unknown[]> = UseAsyncState<T> & {
  execute: (...args: Args) => Promise<T>;
  reset: () => void;
};

/**
 * Handle async operations with loading and error states.
 *
 * @param asyncFn - The async function to execute
 * @param immediate - Whether to execute immediately (default: false)
 * @returns State object with data, isLoading, error, and execute function
 *
 * @example
 * const { data, isLoading, error, execute } = useAsync(
 *   (id: string) => fetchUser(id),
 *   false
 * );
 *
 * useEffect(() => {
 *   execute(userId);
 * }, [userId, execute]);
 */
export function useAsync<T, Args extends unknown[] = []>(
  asyncFn: (...args: Args) => Promise<T>,
  immediate = false
): UseAsyncReturn<T, Args> {
  const [state, setState] = useState<UseAsyncState<T>>({
    data: null,
    isLoading: immediate,
    error: null,
  });

  const mountedRef = useRef(true);

  const execute = useCallback(
    async (...args: Args): Promise<T> => {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        const result = await asyncFn(...args);
        if (mountedRef.current) {
          setState({ data: result, isLoading: false, error: null });
        }
        return result;
      } catch (error) {
        if (mountedRef.current) {
          setState({
            data: null,
            isLoading: false,
            error: error instanceof Error ? error : new Error(String(error)),
          });
        }
        throw error;
      }
    },
    [asyncFn]
  );

  const reset = useCallback(() => {
    setState({ data: null, isLoading: false, error: null });
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  return { ...state, execute, reset };
}
```

## usePrevious

```typescript
import { useRef, useEffect } from 'react';

/**
 * Track the previous value of a variable.
 *
 * @param value - The current value
 * @returns The previous value
 *
 * @example
 * const [count, setCount] = useState(0);
 * const prevCount = usePrevious(count);
 *
 * // Show change direction
 * const direction = count > (prevCount ?? 0) ? '↑' : '↓';
 */
export function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T | undefined>(undefined);

  useEffect(() => {
    ref.current = value;
  }, [value]);

  return ref.current;
}
```

## useToggle

```typescript
import { useState, useCallback } from 'react';

/**
 * Boolean state with toggle function.
 *
 * @param initialValue - Initial boolean value (default: false)
 * @returns Tuple of [value, toggle, setValue]
 *
 * @example
 * const [isOpen, toggle, setIsOpen] = useToggle(false);
 *
 * <button onClick={toggle}>Toggle</button>
 * <button onClick={() => setIsOpen(true)}>Open</button>
 */
export function useToggle(
  initialValue = false
): [boolean, () => void, (value: boolean) => void] {
  const [value, setValue] = useState(initialValue);

  const toggle = useCallback(() => {
    setValue((prev) => !prev);
  }, []);

  return [value, toggle, setValue];
}
```

## Test Examples

```typescript
import { renderHook, act, waitFor } from '@testing-library/react';
import { useDebounce } from './useDebounce';
import { useLocalStorage } from './useLocalStorage';
import { useAsync } from './useAsync';

describe('useDebounce', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('should debounce value updates', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      { initialProps: { value: 'initial' } }
    );

    expect(result.current).toBe('initial');

    rerender({ value: 'updated' });
    expect(result.current).toBe('initial');

    act(() => {
      jest.advanceTimersByTime(500);
    });

    expect(result.current).toBe('updated');
  });
});

describe('useLocalStorage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should initialize with stored value', () => {
    localStorage.setItem('test-key', JSON.stringify('stored'));

    const { result } = renderHook(() => useLocalStorage('test-key', 'default'));

    expect(result.current[0]).toBe('stored');
  });

  it('should update localStorage on setValue', () => {
    const { result } = renderHook(() => useLocalStorage('test-key', 'default'));

    act(() => {
      result.current[1]('new value');
    });

    expect(localStorage.getItem('test-key')).toBe('"new value"');
    expect(result.current[0]).toBe('new value');
  });
});

describe('useAsync', () => {
  it('should handle successful async operation', async () => {
    const mockFn = jest.fn().mockResolvedValue('success');
    const { result } = renderHook(() => useAsync(mockFn));

    expect(result.current.isLoading).toBe(false);
    expect(result.current.data).toBe(null);

    act(() => {
      result.current.execute();
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toBe('success');
    expect(result.current.error).toBe(null);
  });

  it('should handle errors', async () => {
    const mockFn = jest.fn().mockRejectedValue(new Error('failed'));
    const { result } = renderHook(() => useAsync(mockFn));

    await act(async () => {
      try {
        await result.current.execute();
      } catch {
        // Expected
      }
    });

    expect(result.current.error?.message).toBe('failed');
    expect(result.current.data).toBe(null);
  });
});
```
