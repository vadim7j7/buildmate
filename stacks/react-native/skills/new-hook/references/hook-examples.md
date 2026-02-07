# React Native Hook Examples

Reference examples for generating custom React Native hooks.

## useAppState

```typescript
import { useState, useEffect, useRef, useCallback } from 'react';
import { AppState, type AppStateStatus } from 'react-native';

type AppStateType = 'active' | 'background' | 'inactive';

type UseAppStateOptions = {
  onForeground?: () => void;
  onBackground?: () => void;
  triggerOnMount?: boolean;
};

type UseAppStateReturn = {
  appState: AppStateType;
  isActive: boolean;
  isBackground: boolean;
};

/**
 * Track React Native app state (foreground/background).
 *
 * @param options - Configuration options
 * @returns Current app state and boolean flags
 *
 * @example
 * const { isActive } = useAppState({
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

  useEffect(() => {
    onForegroundRef.current = onForeground;
    onBackgroundRef.current = onBackground;
  }, [onForeground, onBackground]);

  useEffect(() => {
    if (triggerOnMount && AppState.currentState === 'active') {
      onForegroundRef.current?.();
    }

    const subscription = AppState.addEventListener(
      'change',
      (nextAppState: AppStateStatus) => {
        const previousState = previousStateRef.current;

        if (
          (previousState === 'background' || previousState === 'inactive') &&
          nextAppState === 'active'
        ) {
          onForegroundRef.current?.();
        }

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

## useKeyboard

```typescript
import { useState, useEffect } from 'react';
import { Keyboard, Platform, type KeyboardEvent } from 'react-native';

type UseKeyboardReturn = {
  isVisible: boolean;
  keyboardHeight: number;
  dismiss: () => void;
};

/**
 * Track keyboard visibility and height.
 *
 * @returns Keyboard state and dismiss function
 *
 * @example
 * const { isVisible, keyboardHeight } = useKeyboard();
 *
 * return (
 *   <View style={{ paddingBottom: keyboardHeight }}>
 *     <TextInput />
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

## useBackHandler

```typescript
import { useEffect, useCallback } from 'react';
import { BackHandler, Platform } from 'react-native';

/**
 * Handle Android back button presses.
 *
 * @param handler - Return true to prevent default back behavior
 *
 * @example
 * useBackHandler(() => {
 *   if (hasUnsavedChanges) {
 *     showConfirmDialog();
 *     return true; // Prevent back
 *   }
 *   return false; // Allow back
 * });
 */
export function useBackHandler(handler: () => boolean): void {
  const stableHandler = useCallback(handler, [handler]);

  useEffect(() => {
    if (Platform.OS !== 'android') {
      return;
    }

    const subscription = BackHandler.addEventListener(
      'hardwareBackPress',
      stableHandler
    );

    return () => {
      subscription.remove();
    };
  }, [stableHandler]);
}
```

## useNetworkStatus

```typescript
import { useState, useEffect } from 'react';
import NetInfo, { type NetInfoState } from '@react-native-community/netinfo';

type NetworkStatus = {
  isConnected: boolean;
  isInternetReachable: boolean | null;
  type: string;
};

/**
 * Track network connectivity status.
 *
 * @returns Current network status
 *
 * @example
 * const { isConnected, type } = useNetworkStatus();
 *
 * if (!isConnected) {
 *   return <OfflineScreen />;
 * }
 */
export function useNetworkStatus(): NetworkStatus {
  const [status, setStatus] = useState<NetworkStatus>({
    isConnected: true,
    isInternetReachable: null,
    type: 'unknown',
  });

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state: NetInfoState) => {
      setStatus({
        isConnected: state.isConnected ?? false,
        isInternetReachable: state.isInternetReachable,
        type: state.type,
      });
    });

    return () => {
      unsubscribe();
    };
  }, []);

  return status;
}
```

## useAsyncStorage

```typescript
import { useState, useEffect, useCallback } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

type UseAsyncStorageReturn<T> = [
  T,
  (value: T | ((prev: T) => T)) => Promise<void>,
  () => Promise<void>,
  boolean,
];

/**
 * Persist state to AsyncStorage.
 *
 * @param key - The storage key
 * @param initialValue - Initial value if key doesn't exist
 * @returns Tuple of [value, setValue, removeValue, isLoading]
 *
 * @example
 * const [user, setUser, removeUser, isLoading] = useAsyncStorage<User | null>(
 *   'user',
 *   null
 * );
 */
export function useAsyncStorage<T>(
  key: string,
  initialValue: T
): UseAsyncStorageReturn<T> {
  const [storedValue, setStoredValue] = useState<T>(initialValue);
  const [isLoading, setIsLoading] = useState(true);

  // Load initial value
  useEffect(() => {
    const loadValue = async () => {
      try {
        const item = await AsyncStorage.getItem(key);
        if (item !== null) {
          setStoredValue(JSON.parse(item));
        }
      } catch (error) {
        console.warn(`Error reading AsyncStorage key "${key}":`, error);
      } finally {
        setIsLoading(false);
      }
    };

    loadValue();
  }, [key]);

  const setValue = useCallback(
    async (value: T | ((prev: T) => T)) => {
      try {
        const valueToStore =
          value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);
        await AsyncStorage.setItem(key, JSON.stringify(valueToStore));
      } catch (error) {
        console.warn(`Error setting AsyncStorage key "${key}":`, error);
      }
    },
    [key, storedValue]
  );

  const removeValue = useCallback(async () => {
    try {
      setStoredValue(initialValue);
      await AsyncStorage.removeItem(key);
    } catch (error) {
      console.warn(`Error removing AsyncStorage key "${key}":`, error);
    }
  }, [key, initialValue]);

  return [storedValue, setValue, removeValue, isLoading];
}
```

## useOrientation

```typescript
import { useState, useEffect } from 'react';
import { Dimensions, type ScaledSize } from 'react-native';

type Orientation = 'portrait' | 'landscape';

type UseOrientationReturn = {
  orientation: Orientation;
  isPortrait: boolean;
  isLandscape: boolean;
  width: number;
  height: number;
};

/**
 * Track screen orientation.
 *
 * @returns Current orientation and dimensions
 *
 * @example
 * const { isLandscape, width } = useOrientation();
 *
 * return (
 *   <View style={{ flexDirection: isLandscape ? 'row' : 'column' }}>
 *     ...
 *   </View>
 * );
 */
export function useOrientation(): UseOrientationReturn {
  const getOrientation = (screen: ScaledSize): Orientation =>
    screen.width > screen.height ? 'landscape' : 'portrait';

  const [state, setState] = useState(() => {
    const screen = Dimensions.get('screen');
    return {
      orientation: getOrientation(screen),
      width: screen.width,
      height: screen.height,
    };
  });

  useEffect(() => {
    const subscription = Dimensions.addEventListener(
      'change',
      ({ screen }: { screen: ScaledSize }) => {
        setState({
          orientation: getOrientation(screen),
          width: screen.width,
          height: screen.height,
        });
      }
    );

    return () => {
      subscription.remove();
    };
  }, []);

  return {
    ...state,
    isPortrait: state.orientation === 'portrait',
    isLandscape: state.orientation === 'landscape',
  };
}
```

## useDebounce

```typescript
import { useState, useEffect } from 'react';

/**
 * Debounce a value.
 *
 * @param value - The value to debounce
 * @param delay - Delay in milliseconds
 * @returns The debounced value
 *
 * @example
 * const [search, setSearch] = useState('');
 * const debouncedSearch = useDebounce(search, 300);
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

## Test Examples

```typescript
import { renderHook, act } from '@testing-library/react-native';
import { AppState, Keyboard, BackHandler } from 'react-native';

import { useAppState } from '../hooks/useAppState';
import { useKeyboard } from '../hooks/useKeyboard';
import { useBackHandler } from '../hooks/useBackHandler';

// Mock React Native modules
jest.mock('react-native', () => ({
  AppState: {
    currentState: 'active',
    addEventListener: jest.fn(() => ({ remove: jest.fn() })),
  },
  Keyboard: {
    addListener: jest.fn(() => ({ remove: jest.fn() })),
    dismiss: jest.fn(),
  },
  BackHandler: {
    addEventListener: jest.fn(() => ({ remove: jest.fn() })),
  },
  Platform: {
    OS: 'ios',
  },
  Dimensions: {
    get: jest.fn(() => ({ width: 375, height: 812 })),
    addEventListener: jest.fn(() => ({ remove: jest.fn() })),
  },
}));

describe('useAppState', () => {
  it('should return initial state', () => {
    const { result } = renderHook(() => useAppState());

    expect(result.current.appState).toBe('active');
    expect(result.current.isActive).toBe(true);
    expect(result.current.isBackground).toBe(false);
  });

  it('should subscribe to app state changes', () => {
    renderHook(() => useAppState());

    expect(AppState.addEventListener).toHaveBeenCalledWith(
      'change',
      expect.any(Function)
    );
  });

  it('should call onForeground when app becomes active', () => {
    const onForeground = jest.fn();
    const listeners: ((state: string) => void)[] = [];

    (AppState.addEventListener as jest.Mock).mockImplementation(
      (event, callback) => {
        listeners.push(callback);
        return { remove: jest.fn() };
      }
    );

    renderHook(() =>
      useAppState({ onForeground, triggerOnMount: false })
    );

    // Simulate background to active transition
    act(() => {
      listeners.forEach((listener) => listener('active'));
    });

    // Note: Full test would need to track previous state
  });
});

describe('useKeyboard', () => {
  it('should return initial state', () => {
    const { result } = renderHook(() => useKeyboard());

    expect(result.current.isVisible).toBe(false);
    expect(result.current.keyboardHeight).toBe(0);
    expect(result.current.dismiss).toBe(Keyboard.dismiss);
  });

  it('should subscribe to keyboard events', () => {
    renderHook(() => useKeyboard());

    expect(Keyboard.addListener).toHaveBeenCalledWith(
      'keyboardWillShow',
      expect.any(Function)
    );
    expect(Keyboard.addListener).toHaveBeenCalledWith(
      'keyboardWillHide',
      expect.any(Function)
    );
  });
});

describe('useBackHandler', () => {
  it('should register back handler', () => {
    const handler = jest.fn(() => false);

    renderHook(() => useBackHandler(handler));

    // Would check if BackHandler.addEventListener was called on Android
  });

  it('should cleanup on unmount', () => {
    const handler = jest.fn(() => false);
    const remove = jest.fn();

    (BackHandler.addEventListener as jest.Mock).mockReturnValue({ remove });

    const { unmount } = renderHook(() => useBackHandler(handler));
    unmount();

    // Note: Cleanup tested based on Platform.OS
  });
});
```
