# React Native Offline Patterns

Offline-first patterns with synchronization.

---

## 1. Network Status Hook

```typescript
// hooks/useNetworkStatus.ts
import { useState, useEffect } from 'react';
import NetInfo, { type NetInfoState } from '@react-native-community/netinfo';

type NetworkStatus = {
  isConnected: boolean;
  isInternetReachable: boolean | null;
  type: string;
};

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

    return () => unsubscribe();
  }, []);

  return status;
}
```

---

## 2. Offline Storage with MMKV

```typescript
// lib/storage.ts
import { MMKV } from 'react-native-mmkv';

const storage = new MMKV();

export const offlineStorage = {
  get<T>(key: string): T | null {
    const value = storage.getString(key);
    if (!value) return null;
    try {
      return JSON.parse(value) as T;
    } catch {
      return null;
    }
  },

  set<T>(key: string, value: T): void {
    storage.set(key, JSON.stringify(value));
  },

  delete(key: string): void {
    storage.delete(key);
  },

  clear(): void {
    storage.clearAll();
  },

  getAllKeys(): string[] {
    return storage.getAllKeys();
  },
};
```

---

## 3. Pending Actions Queue

```typescript
// lib/syncQueue.ts
import { offlineStorage } from './storage';

type PendingAction = {
  id: string;
  type: string;
  payload: unknown;
  createdAt: string;
  retryCount: number;
};

const QUEUE_KEY = 'sync_queue';

export const syncQueue = {
  getAll(): PendingAction[] {
    return offlineStorage.get<PendingAction[]>(QUEUE_KEY) ?? [];
  },

  add(action: Omit<PendingAction, 'id' | 'createdAt' | 'retryCount'>): void {
    const queue = this.getAll();
    queue.push({
      ...action,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      createdAt: new Date().toISOString(),
      retryCount: 0,
    });
    offlineStorage.set(QUEUE_KEY, queue);
  },

  remove(id: string): void {
    const queue = this.getAll().filter((action) => action.id !== id);
    offlineStorage.set(QUEUE_KEY, queue);
  },

  incrementRetry(id: string): void {
    const queue = this.getAll().map((action) =>
      action.id === id
        ? { ...action, retryCount: action.retryCount + 1 }
        : action
    );
    offlineStorage.set(QUEUE_KEY, queue);
  },

  clear(): void {
    offlineStorage.delete(QUEUE_KEY);
  },
};
```

---

## 4. Sync Service

```typescript
// services/syncService.ts
import { syncQueue } from '@/lib/syncQueue';
import { api } from '@/lib/api';

type SyncResult = {
  synced: number;
  failed: number;
  errors: Array<{ id: string; error: string }>;
};

const MAX_RETRIES = 3;

export async function processQueue(): Promise<SyncResult> {
  const actions = syncQueue.getAll();
  const results: SyncResult = { synced: 0, failed: 0, errors: [] };

  for (const action of actions) {
    if (action.retryCount >= MAX_RETRIES) {
      results.failed++;
      results.errors.push({ id: action.id, error: 'Max retries exceeded' });
      continue;
    }

    try {
      await processAction(action);
      syncQueue.remove(action.id);
      results.synced++;
    } catch (error) {
      syncQueue.incrementRetry(action.id);
      results.errors.push({
        id: action.id,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  }

  return results;
}

async function processAction(action: PendingAction): Promise<void> {
  switch (action.type) {
    case 'CREATE_POST':
      await api.posts.create(action.payload);
      break;
    case 'UPDATE_POST':
      await api.posts.update(action.payload);
      break;
    case 'DELETE_POST':
      await api.posts.delete(action.payload);
      break;
    default:
      throw new Error(`Unknown action type: ${action.type}`);
  }
}
```

---

## 5. Sync Manager Hook

```typescript
// hooks/useSyncManager.ts
import { useEffect, useCallback, useState } from 'react';
import { AppState, type AppStateStatus } from 'react-native';
import { useNetworkStatus } from './useNetworkStatus';
import { processQueue } from '@/services/syncService';
import { syncQueue } from '@/lib/syncQueue';

type SyncState = {
  isSyncing: boolean;
  pendingCount: number;
  lastSyncAt: Date | null;
  error: string | null;
};

export function useSyncManager() {
  const { isConnected } = useNetworkStatus();
  const [state, setState] = useState<SyncState>({
    isSyncing: false,
    pendingCount: syncQueue.getAll().length,
    lastSyncAt: null,
    error: null,
  });

  const sync = useCallback(async () => {
    if (!isConnected || state.isSyncing) return;

    setState((prev) => ({ ...prev, isSyncing: true, error: null }));

    try {
      const result = await processQueue();
      setState((prev) => ({
        ...prev,
        isSyncing: false,
        pendingCount: syncQueue.getAll().length,
        lastSyncAt: new Date(),
        error: result.failed > 0 ? `${result.failed} actions failed` : null,
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        isSyncing: false,
        error: error instanceof Error ? error.message : 'Sync failed',
      }));
    }
  }, [isConnected, state.isSyncing]);

  // Sync when coming online
  useEffect(() => {
    if (isConnected && state.pendingCount > 0) {
      sync();
    }
  }, [isConnected]);

  // Sync when app becomes active
  useEffect(() => {
    const handleAppStateChange = (nextState: AppStateStatus) => {
      if (nextState === 'active' && isConnected && state.pendingCount > 0) {
        sync();
      }
    };

    const subscription = AppState.addEventListener('change', handleAppStateChange);
    return () => subscription.remove();
  }, [isConnected, state.pendingCount, sync]);

  return {
    ...state,
    sync,
  };
}
```

---

## 6. Offline-First Data Hook

```typescript
// hooks/useOfflineData.ts
import { useState, useEffect, useCallback } from 'react';
import { useNetworkStatus } from './useNetworkStatus';
import { offlineStorage } from '@/lib/storage';

type UseOfflineDataOptions<T> = {
  key: string;
  fetchFn: () => Promise<T>;
  staleTime?: number; // milliseconds
};

type UseOfflineDataReturn<T> = {
  data: T | null;
  isLoading: boolean;
  isStale: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
};

export function useOfflineData<T>({
  key,
  fetchFn,
  staleTime = 5 * 60 * 1000, // 5 minutes
}: UseOfflineDataOptions<T>): UseOfflineDataReturn<T> {
  const { isConnected } = useNetworkStatus();
  const [data, setData] = useState<T | null>(() => offlineStorage.get<T>(key));
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const getCachedTimestamp = (): number | null => {
    return offlineStorage.get<number>(`${key}_timestamp`);
  };

  const isStale = useCallback(() => {
    const timestamp = getCachedTimestamp();
    if (!timestamp) return true;
    return Date.now() - timestamp > staleTime;
  }, [key, staleTime]);

  const refresh = useCallback(async () => {
    if (!isConnected) return;

    setIsLoading(true);
    setError(null);

    try {
      const freshData = await fetchFn();
      setData(freshData);
      offlineStorage.set(key, freshData);
      offlineStorage.set(`${key}_timestamp`, Date.now());
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Fetch failed'));
    } finally {
      setIsLoading(false);
    }
  }, [key, fetchFn, isConnected]);

  // Auto-refresh when stale and online
  useEffect(() => {
    if (isConnected && isStale()) {
      refresh();
    }
  }, [isConnected]);

  return {
    data,
    isLoading,
    isStale: isStale(),
    error,
    refresh,
  };
}
```

---

## 7. Optimistic Updates

```typescript
// hooks/useOptimisticMutation.ts
import { useState, useCallback } from 'react';
import { useNetworkStatus } from './useNetworkStatus';
import { syncQueue } from '@/lib/syncQueue';
import { offlineStorage } from '@/lib/storage';

type UseOptimisticMutationOptions<T, P> = {
  cacheKey: string;
  mutationFn: (payload: P) => Promise<T>;
  optimisticUpdate: (current: T[], payload: P) => T[];
  actionType: string;
};

export function useOptimisticMutation<T, P>({
  cacheKey,
  mutationFn,
  optimisticUpdate,
  actionType,
}: UseOptimisticMutationOptions<T, P>) {
  const { isConnected } = useNetworkStatus();
  const [isPending, setIsPending] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const mutate = useCallback(
    async (payload: P) => {
      // Apply optimistic update
      const currentData = offlineStorage.get<T[]>(cacheKey) ?? [];
      const optimisticData = optimisticUpdate(currentData, payload);
      offlineStorage.set(cacheKey, optimisticData);

      if (!isConnected) {
        // Queue for later sync
        syncQueue.add({ type: actionType, payload });
        return;
      }

      setIsPending(true);
      setError(null);

      try {
        await mutationFn(payload);
      } catch (err) {
        // Revert on failure
        offlineStorage.set(cacheKey, currentData);
        setError(err instanceof Error ? err : new Error('Mutation failed'));
        throw err;
      } finally {
        setIsPending(false);
      }
    },
    [cacheKey, mutationFn, optimisticUpdate, actionType, isConnected]
  );

  return { mutate, isPending, error };
}

// Usage
function useCreatePost() {
  return useOptimisticMutation({
    cacheKey: 'posts',
    actionType: 'CREATE_POST',
    mutationFn: (payload: CreatePostPayload) => api.posts.create(payload),
    optimisticUpdate: (posts, payload) => [
      { ...payload, id: `temp-${Date.now()}`, createdAt: new Date().toISOString() },
      ...posts,
    ],
  });
}
```

---

## 8. Conflict Resolution

```typescript
// lib/conflictResolver.ts
type ConflictStrategy = 'client-wins' | 'server-wins' | 'merge' | 'manual';

type ConflictResult<T> = {
  resolved: T;
  hadConflict: boolean;
  strategy: ConflictStrategy;
};

export function resolveConflict<T extends { updatedAt: string }>(
  clientData: T,
  serverData: T,
  strategy: ConflictStrategy = 'server-wins'
): ConflictResult<T> {
  const clientTime = new Date(clientData.updatedAt).getTime();
  const serverTime = new Date(serverData.updatedAt).getTime();

  const hadConflict = clientTime !== serverTime;

  if (!hadConflict) {
    return { resolved: serverData, hadConflict: false, strategy };
  }

  switch (strategy) {
    case 'client-wins':
      return { resolved: clientData, hadConflict: true, strategy };

    case 'server-wins':
      return { resolved: serverData, hadConflict: true, strategy };

    case 'merge':
      // Simple merge: server data with client modifications
      const merged = {
        ...serverData,
        ...clientData,
        updatedAt: new Date().toISOString(),
      };
      return { resolved: merged, hadConflict: true, strategy };

    case 'manual':
      throw new Error('Manual conflict resolution required');

    default:
      return { resolved: serverData, hadConflict: true, strategy };
  }
}
```

---

## 9. Offline Indicator Component

```typescript
// components/OfflineIndicator.tsx
import { View, Text, StyleSheet, Animated } from 'react-native';
import { useNetworkStatus } from '@/hooks/useNetworkStatus';
import { useSyncManager } from '@/hooks/useSyncManager';
import { useEffect, useRef } from 'react';

export function OfflineIndicator() {
  const { isConnected } = useNetworkStatus();
  const { pendingCount, isSyncing } = useSyncManager();
  const slideAnim = useRef(new Animated.Value(-50)).current;

  const showBanner = !isConnected || pendingCount > 0;

  useEffect(() => {
    Animated.timing(slideAnim, {
      toValue: showBanner ? 0 : -50,
      duration: 300,
      useNativeDriver: true,
    }).start();
  }, [showBanner]);

  const getMessage = () => {
    if (!isConnected) {
      return 'You are offline';
    }
    if (isSyncing) {
      return `Syncing ${pendingCount} changes...`;
    }
    if (pendingCount > 0) {
      return `${pendingCount} changes pending`;
    }
    return '';
  };

  return (
    <Animated.View
      style={[
        styles.container,
        {
          transform: [{ translateY: slideAnim }],
          backgroundColor: isConnected ? '#FFA500' : '#FF4444',
        },
      ]}
    >
      <Text style={styles.text}>{getMessage()}</Text>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    padding: 8,
    alignItems: 'center',
    zIndex: 1000,
  },
  text: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
});
```

---

## 10. Testing Offline

```typescript
// __tests__/offline.test.ts
import { renderHook, act } from '@testing-library/react-native';
import { useOfflineData } from '../hooks/useOfflineData';
import { offlineStorage } from '../lib/storage';

// Mock NetInfo
jest.mock('@react-native-community/netinfo', () => ({
  addEventListener: jest.fn(() => jest.fn()),
}));

describe('useOfflineData', () => {
  beforeEach(() => {
    offlineStorage.clear();
  });

  it('returns cached data when offline', async () => {
    // Pre-cache data
    offlineStorage.set('posts', [{ id: 1, title: 'Cached Post' }]);
    offlineStorage.set('posts_timestamp', Date.now());

    const fetchFn = jest.fn();
    const { result } = renderHook(() =>
      useOfflineData({
        key: 'posts',
        fetchFn,
      })
    );

    expect(result.current.data).toEqual([{ id: 1, title: 'Cached Post' }]);
    expect(fetchFn).not.toHaveBeenCalled();
  });

  it('queues action when offline', () => {
    // ... test sync queue behavior
  });
});
```
