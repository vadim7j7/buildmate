---
name: new-hook
description: Generate a custom React hook with TypeScript types and tests
---

# /new-hook

## What This Does

Creates a custom React hook following best practices: TypeScript types,
memoization where needed, cleanup handling, and comprehensive tests.

## Usage

```
/new-hook useDebounce            # Utility hook
/new-hook useLocalStorage        # Browser API wrapper
/new-hook useMediaQuery          # Responsive design hook
/new-hook useClickOutside        # Event handling hook
/new-hook useAsync               # Async operation hook
```

## How It Works

### 1. Determine Hook Category

Based on the hook name, identify the category:
- **State hooks**: Manage local or external state
- **Effect hooks**: Handle side effects, subscriptions
- **Utility hooks**: Debounce, throttle, memoization
- **Browser API hooks**: localStorage, mediaQuery, geolocation
- **Event hooks**: Click outside, keyboard, scroll

### 2. Read Existing Patterns

Before generating, read:
- `patterns/frontend-patterns.md` for conventions
- `skills/new-hook/references/hook-examples.md` for examples
- Existing hooks in `src/hooks/` for project patterns

### 3. Generate Files

#### Hook: `src/hooks/<hookName>.ts`

```typescript
import { useState, useEffect, useCallback, useRef } from 'react';

type Use<Name>Options = {
  // configuration options
};

type Use<Name>Return = {
  // return type
};

/**
 * <Description of what the hook does>
 *
 * @param options - Configuration options
 * @returns Hook return value
 *
 * @example
 * const { value, setValue } = use<Name>({ initialValue: '' });
 */
export function use<Name>(options: Use<Name>Options = {}): Use<Name>Return {
  // Implementation
}
```

#### Test: `src/hooks/<hookName>.test.ts`

```typescript
import { renderHook, act } from '@testing-library/react';
import { use<Name> } from './<hookName>';

describe('use<Name>', () => {
  it('should initialize with default value', () => {
    const { result } = renderHook(() => use<Name>());
    expect(result.current.value).toBe(defaultValue);
  });

  it('should handle updates', () => {
    const { result } = renderHook(() => use<Name>());
    act(() => {
      result.current.setValue('new value');
    });
    expect(result.current.value).toBe('new value');
  });

  it('should cleanup on unmount', () => {
    const { unmount } = renderHook(() => use<Name>());
    unmount();
    // Verify cleanup
  });
});
```

### 4. Verify

Run type checking and tests:
```bash
npx tsc --noEmit
npm test -- --testPathPattern=<hookName>
```

## Rules

- Hook names must start with `use`
- Use TypeScript for all hooks
- Export as named export (not default)
- Include JSDoc with `@example`
- Use `useCallback` for returned functions
- Use `useRef` for values that shouldn't trigger re-renders
- Clean up subscriptions/listeners in `useEffect` cleanup
- Handle SSR (check for `window`/`document` existence)
- Avoid returning new object/array references on every render

## Generated Files

```
src/hooks/<hookName>.ts
src/hooks/<hookName>.test.ts
```

## Example Output

For `/new-hook useDebounce`:

**Hook:** `src/hooks/useDebounce.ts`
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

For `/new-hook useLocalStorage`:

**Hook:** `src/hooks/useLocalStorage.ts`
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
 *
 * @example
 * const [theme, setTheme, removeTheme] = useLocalStorage('theme', 'light');
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T,
  options: UseLocalStorageOptions<T> = {}
): [T, (value: T | ((prev: T) => T)) => void, () => void] {
  const {
    serializer = JSON.stringify,
    deserializer = JSON.parse,
  } = options;

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

**Test:** `src/hooks/useLocalStorage.test.ts`
