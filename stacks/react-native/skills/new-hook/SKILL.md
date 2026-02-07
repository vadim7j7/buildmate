---
name: new-hook
description: Generate a custom React Native hook with TypeScript types and tests
---

# /new-hook

## What This Does

Creates a custom React Native hook following best practices: TypeScript types,
platform-specific handling, cleanup, and comprehensive tests. Handles mobile-
specific concerns like app state, keyboard, and device APIs.

## Usage

```
/new-hook useAppState              # App foreground/background state
/new-hook useKeyboard              # Keyboard visibility and height
/new-hook useNetworkStatus         # Network connectivity
/new-hook useBackHandler           # Android back button
/new-hook useOrientation           # Screen orientation
/new-hook useAsyncStorage          # Persistent storage
```

## How It Works

### 1. Determine Hook Category

Based on the hook name, identify the category:
- **Platform hooks**: App state, back handler, permissions
- **Device hooks**: Network, keyboard, orientation, dimensions
- **Storage hooks**: AsyncStorage, SecureStore, MMKV
- **UI hooks**: Animation, gestures, haptics
- **Utility hooks**: Debounce, throttle, previous value

### 2. Read Existing Patterns

Before generating, read:
- `patterns/mobile-patterns.md` for conventions
- `skills/new-hook/references/hook-examples.md` for examples
- Existing hooks in `hooks/` for project patterns

### 3. Generate Files

#### Hook: `hooks/<hookName>.ts`

```typescript
import { useState, useEffect, useCallback, useRef } from 'react';
import { Platform, AppState, Keyboard } from 'react-native';

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
 * const { isActive } = use<Name>();
 */
export function use<Name>(options: Use<Name>Options = {}): Use<Name>Return {
  // Implementation
}
```

#### Test: `__tests__/hooks/<hookName>.test.ts`

```typescript
import { renderHook, act } from '@testing-library/react-native';
import { use<Name> } from '../../hooks/<hookName>';

describe('use<Name>', () => {
  it('should initialize correctly', () => {
    const { result } = renderHook(() => use<Name>());
    expect(result.current).toBeDefined();
  });

  it('should handle platform differences', () => {
    // Platform-specific tests
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
- Handle both iOS and Android with `Platform.select` or `Platform.OS`
- Clean up subscriptions/listeners in `useEffect` cleanup
- Use `useRef` for event subscriptions to avoid stale closures
- Consider Expo vs bare React Native compatibility

## Generated Files

```
hooks/<hookName>.ts
__tests__/hooks/<hookName>.test.ts
```

## Example Output

For `/new-hook useAppState`:

**Hook:** `hooks/useAppState.ts`
```typescript
import { useState, useEffect, useRef, useCallback } from 'react';
import { AppState, type AppStateStatus } from 'react-native';

type AppStateType = 'active' | 'background' | 'inactive';

type UseAppStateOptions = {
  /**
   * Callback when app comes to foreground
   */
  onForeground?: () => void;
  /**
   * Callback when app goes to background
   */
  onBackground?: () => void;
  /**
   * Whether to trigger callbacks on mount
   */
  triggerOnMount?: boolean;
};

type UseAppStateReturn = {
  /**
   * Current app state
   */
  appState: AppStateType;
  /**
   * Whether the app is in the foreground
   */
  isActive: boolean;
  /**
   * Whether the app is in the background
   */
  isBackground: boolean;
};

/**
 * Track React Native app state (foreground/background).
 *
 * @param options - Configuration options
 * @returns Current app state and boolean flags
 *
 * @example
 * const { isActive, isBackground } = useAppState({
 *   onForeground: () => refetch(),
 *   onBackground: () => pauseVideo(),
 * });
 */
export function useAppState(options: UseAppStateOptions = {}): UseAppStateReturn {
  const { onForeground, onBackground, triggerOnMount = false } = options;

  const [appState, setAppState] = useState<AppStateType>(
    AppState.currentState as AppStateType
  );

  const previousStateRef = useRef<AppStateStatus>(AppState.currentState);
  const onForegroundRef = useRef(onForeground);
  const onBackgroundRef = useRef(onBackground);

  // Keep refs updated
  useEffect(() => {
    onForegroundRef.current = onForeground;
    onBackgroundRef.current = onBackground;
  }, [onForeground, onBackground]);

  useEffect(() => {
    // Trigger on mount if requested
    if (triggerOnMount && AppState.currentState === 'active') {
      onForegroundRef.current?.();
    }

    const subscription = AppState.addEventListener(
      'change',
      (nextAppState: AppStateStatus) => {
        const previousState = previousStateRef.current;

        // Detect foreground transition
        if (
          (previousState === 'background' || previousState === 'inactive') &&
          nextAppState === 'active'
        ) {
          onForegroundRef.current?.();
        }

        // Detect background transition
        if (
          previousState === 'active' &&
          (nextAppState === 'background' || nextAppState === 'inactive')
        ) {
          onBackgroundRef.current?.();
        }

        previousStateRef.current = nextAppState;
        setAppState(nextAppState as AppStateType);
      }
    );

    return () => {
      subscription.remove();
    };
  }, [triggerOnMount]);

  return {
    appState,
    isActive: appState === 'active',
    isBackground: appState === 'background',
  };
}
```

For `/new-hook useKeyboard`:

**Hook:** `hooks/useKeyboard.ts`
```typescript
import { useState, useEffect } from 'react';
import { Keyboard, Platform, type KeyboardEvent } from 'react-native';

type UseKeyboardReturn = {
  /**
   * Whether the keyboard is visible
   */
  isVisible: boolean;
  /**
   * Height of the keyboard in pixels
   */
  keyboardHeight: number;
  /**
   * Dismiss the keyboard
   */
  dismiss: () => void;
};

/**
 * Track keyboard visibility and height.
 *
 * @returns Keyboard state and dismiss function
 *
 * @example
 * const { isVisible, keyboardHeight, dismiss } = useKeyboard();
 *
 * return (
 *   <View style={{ paddingBottom: keyboardHeight }}>
 *     <TextInput />
 *     {isVisible && <Button onPress={dismiss} title="Done" />}
 *   </View>
 * );
 */
export function useKeyboard(): UseKeyboardReturn {
  const [isVisible, setIsVisible] = useState(false);
  const [keyboardHeight, setKeyboardHeight] = useState(0);

  useEffect(() => {
    const showEvent = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const hideEvent = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';

    const handleKeyboardShow = (event: KeyboardEvent) => {
      setIsVisible(true);
      setKeyboardHeight(event.endCoordinates.height);
    };

    const handleKeyboardHide = () => {
      setIsVisible(false);
      setKeyboardHeight(0);
    };

    const showSubscription = Keyboard.addListener(showEvent, handleKeyboardShow);
    const hideSubscription = Keyboard.addListener(hideEvent, handleKeyboardHide);

    return () => {
      showSubscription.remove();
      hideSubscription.remove();
    };
  }, []);

  return {
    isVisible,
    keyboardHeight,
    dismiss: Keyboard.dismiss,
  };
}
```

**Test:** `__tests__/hooks/useKeyboard.test.ts`
