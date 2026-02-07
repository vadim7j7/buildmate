# React Native Structured Logging Patterns

Structured logging patterns for React Native applications.

---

## 1. Logger Setup

```typescript
// lib/logger.ts
type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: Record<string, unknown>;
  error?: {
    name: string;
    message: string;
    stack?: string;
  };
}

const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

class Logger {
  private minLevel: LogLevel = __DEV__ ? 'debug' : 'info';
  private context: Record<string, unknown> = {};
  private transports: LogTransport[] = [];

  constructor() {
    // Add console transport in development
    if (__DEV__) {
      this.addTransport(new ConsoleTransport());
    }

    // Add remote transport in production
    if (!__DEV__) {
      this.addTransport(new RemoteTransport());
    }
  }

  setMinLevel(level: LogLevel) {
    this.minLevel = level;
  }

  setContext(context: Record<string, unknown>) {
    this.context = { ...this.context, ...context };
  }

  clearContext() {
    this.context = {};
  }

  addTransport(transport: LogTransport) {
    this.transports.push(transport);
  }

  private shouldLog(level: LogLevel): boolean {
    return LOG_LEVELS[level] >= LOG_LEVELS[this.minLevel];
  }

  private log(level: LogLevel, message: string, context?: Record<string, unknown>) {
    if (!this.shouldLog(level)) return;

    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      context: { ...this.context, ...context },
    };

    this.transports.forEach((transport) => transport.log(entry));
  }

  debug(message: string, context?: Record<string, unknown>) {
    this.log('debug', message, context);
  }

  info(message: string, context?: Record<string, unknown>) {
    this.log('info', message, context);
  }

  warn(message: string, context?: Record<string, unknown>) {
    this.log('warn', message, context);
  }

  error(message: string, error?: Error, context?: Record<string, unknown>) {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level: 'error',
      message,
      context: { ...this.context, ...context },
      error: error ? {
        name: error.name,
        message: error.message,
        stack: error.stack,
      } : undefined,
    };

    this.transports.forEach((transport) => transport.log(entry));
  }

  child(context: Record<string, unknown>): ChildLogger {
    return new ChildLogger(this, context);
  }
}

class ChildLogger {
  constructor(
    private parent: Logger,
    private context: Record<string, unknown>
  ) {}

  debug(message: string, context?: Record<string, unknown>) {
    this.parent.debug(message, { ...this.context, ...context });
  }

  info(message: string, context?: Record<string, unknown>) {
    this.parent.info(message, { ...this.context, ...context });
  }

  warn(message: string, context?: Record<string, unknown>) {
    this.parent.warn(message, { ...this.context, ...context });
  }

  error(message: string, error?: Error, context?: Record<string, unknown>) {
    this.parent.error(message, error, { ...this.context, ...context });
  }
}

export const logger = new Logger();
```

---

## 2. Log Transports

```typescript
// lib/logger/transports.ts
import { LogEntry } from './types';

export interface LogTransport {
  log(entry: LogEntry): void;
}

// Console transport for development
export class ConsoleTransport implements LogTransport {
  private colors = {
    debug: '\x1b[36m', // cyan
    info: '\x1b[32m',  // green
    warn: '\x1b[33m',  // yellow
    error: '\x1b[31m', // red
    reset: '\x1b[0m',
  };

  log(entry: LogEntry) {
    const color = this.colors[entry.level];
    const reset = this.colors.reset;
    const prefix = `${color}[${entry.level.toUpperCase()}]${reset}`;

    const contextStr = entry.context && Object.keys(entry.context).length
      ? ` ${JSON.stringify(entry.context)}`
      : '';

    console.log(`${prefix} ${entry.message}${contextStr}`);

    if (entry.error?.stack) {
      console.log(entry.error.stack);
    }
  }
}

// Remote transport for production
export class RemoteTransport implements LogTransport {
  private queue: LogEntry[] = [];
  private flushInterval = 5000;
  private maxQueueSize = 100;
  private endpoint = process.env.EXPO_PUBLIC_LOG_ENDPOINT;

  constructor() {
    setInterval(() => this.flush(), this.flushInterval);
  }

  log(entry: LogEntry) {
    this.queue.push(entry);

    if (this.queue.length >= this.maxQueueSize) {
      this.flush();
    }
  }

  private async flush() {
    if (!this.queue.length || !this.endpoint) return;

    const entries = [...this.queue];
    this.queue = [];

    try {
      await fetch(this.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ logs: entries }),
      });
    } catch (error) {
      // Re-queue on failure (with limit)
      if (this.queue.length < this.maxQueueSize) {
        this.queue.unshift(...entries.slice(-50));
      }
    }
  }
}

// File transport for offline storage
export class FileTransport implements LogTransport {
  private buffer: LogEntry[] = [];
  private bufferSize = 50;

  async log(entry: LogEntry) {
    this.buffer.push(entry);

    if (this.buffer.length >= this.bufferSize) {
      await this.persist();
    }
  }

  private async persist() {
    // Use AsyncStorage or file system
    const { default: AsyncStorage } = await import('@react-native-async-storage/async-storage');
    const existing = await AsyncStorage.getItem('logs');
    const logs = existing ? JSON.parse(existing) : [];
    logs.push(...this.buffer);

    // Keep last 1000 logs
    const trimmed = logs.slice(-1000);
    await AsyncStorage.setItem('logs', JSON.stringify(trimmed));
    this.buffer = [];
  }
}
```

---

## 3. Navigation Logging

```typescript
// lib/logger/navigation.ts
import { logger } from './logger';

export function createNavigationLogger() {
  const navLogger = logger.child({ component: 'navigation' });

  return {
    onStateChange: (state: any) => {
      const currentRoute = getCurrentRoute(state);

      navLogger.info('Screen changed', {
        screen: currentRoute.name,
        params: sanitizeParams(currentRoute.params),
      });
    },

    onReady: () => {
      navLogger.info('Navigation ready');
    },
  };
}

function getCurrentRoute(state: any): { name: string; params?: object } {
  if (!state) return { name: 'unknown' };

  const route = state.routes[state.index];
  if (route.state) {
    return getCurrentRoute(route.state);
  }
  return { name: route.name, params: route.params };
}

function sanitizeParams(params?: object): object | undefined {
  if (!params) return undefined;

  const sanitized = { ...params } as Record<string, unknown>;
  delete sanitized.password;
  delete sanitized.token;
  return sanitized;
}

// Usage in App.tsx
import { NavigationContainer } from '@react-navigation/native';
import { createNavigationLogger } from '@/lib/logger/navigation';

const navigationLogger = createNavigationLogger();

export function App() {
  return (
    <NavigationContainer
      onStateChange={navigationLogger.onStateChange}
      onReady={navigationLogger.onReady}
    >
      {/* ... */}
    </NavigationContainer>
  );
}
```

---

## 4. API Request Logging

```typescript
// lib/api/logging.ts
import { logger } from '@/lib/logger';

const apiLogger = logger.child({ component: 'api' });

export function createLoggingFetch(baseFetch: typeof fetch = fetch) {
  return async function loggingFetch(
    input: RequestInfo | URL,
    init?: RequestInit
  ): Promise<Response> {
    const url = typeof input === 'string' ? input : input.toString();
    const method = init?.method || 'GET';
    const requestId = generateRequestId();
    const startTime = Date.now();

    apiLogger.info('Request started', {
      requestId,
      method,
      url: sanitizeUrl(url),
    });

    try {
      const response = await baseFetch(input, init);
      const duration = Date.now() - startTime;

      apiLogger.info('Request completed', {
        requestId,
        method,
        url: sanitizeUrl(url),
        status: response.status,
        duration,
      });

      return response;
    } catch (error) {
      const duration = Date.now() - startTime;

      apiLogger.error('Request failed', error as Error, {
        requestId,
        method,
        url: sanitizeUrl(url),
        duration,
      });

      throw error;
    }
  };
}

function generateRequestId(): string {
  return Math.random().toString(36).substring(2, 10);
}

function sanitizeUrl(url: string): string {
  try {
    const parsed = new URL(url);
    parsed.searchParams.delete('token');
    parsed.searchParams.delete('api_key');
    return parsed.toString();
  } catch {
    return url;
  }
}
```

---

## 5. Performance Logging

```typescript
// lib/logger/performance.ts
import { logger } from './logger';

const perfLogger = logger.child({ component: 'performance' });

export function measureRender(componentName: string) {
  const startTime = Date.now();

  return () => {
    const duration = Date.now() - startTime;

    if (duration > 16) { // More than one frame (60fps)
      perfLogger.warn('Slow render', {
        component: componentName,
        duration,
      });
    } else if (__DEV__) {
      perfLogger.debug('Render completed', {
        component: componentName,
        duration,
      });
    }
  };
}

export async function measureAsync<T>(
  operationName: string,
  operation: () => Promise<T>,
  metadata?: Record<string, unknown>
): Promise<T> {
  const startTime = Date.now();

  try {
    const result = await operation();
    const duration = Date.now() - startTime;

    perfLogger.info('Operation completed', {
      operation: operationName,
      duration,
      ...metadata,
    });

    return result;
  } catch (error) {
    const duration = Date.now() - startTime;

    perfLogger.error('Operation failed', error as Error, {
      operation: operationName,
      duration,
      ...metadata,
    });

    throw error;
  }
}

// Usage
const user = await measureAsync(
  'fetchUserProfile',
  () => api.users.getProfile(userId),
  { userId }
);
```

---

## 6. User Action Logging

```typescript
// lib/logger/analytics.ts
import { logger } from './logger';

const analyticsLogger = logger.child({ component: 'analytics' });

type ActionType =
  | 'tap'
  | 'swipe'
  | 'submit'
  | 'view'
  | 'share'
  | 'purchase';

export function logUserAction(
  action: ActionType,
  target: string,
  metadata?: Record<string, unknown>
) {
  analyticsLogger.info('User action', {
    action,
    target,
    ...metadata,
    timestamp: Date.now(),
  });
}

// React hook for component tracking
export function useScreenTracking(screenName: string) {
  useEffect(() => {
    const startTime = Date.now();

    logUserAction('view', screenName, { type: 'screen_enter' });

    return () => {
      const duration = Date.now() - startTime;
      logUserAction('view', screenName, {
        type: 'screen_exit',
        viewDuration: duration,
      });
    };
  }, [screenName]);
}

// Usage
function ProductScreen() {
  useScreenTracking('ProductScreen');

  const handleAddToCart = () => {
    logUserAction('tap', 'add_to_cart_button', { productId: product.id });
    // ...
  };
}
```

---

## 7. Error Boundary Logging

```typescript
// components/LoggingErrorBoundary.tsx
import React, { Component, ReactNode } from 'react';
import { View, Text, Button } from 'react-native';
import { logger } from '@/lib/logger';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class LoggingErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    logger.error('React error boundary caught error', error, {
      componentStack: errorInfo.componentStack,
    });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <Text style={{ fontSize: 18, marginBottom: 16 }}>
            Something went wrong
          </Text>
          <Button title="Try Again" onPress={this.handleRetry} />
        </View>
      );
    }

    return this.props.children;
  }
}
```

---

## 8. Network Status Logging

```typescript
// hooks/useNetworkLogging.ts
import { useEffect } from 'react';
import NetInfo from '@react-native-community/netinfo';
import { logger } from '@/lib/logger';

const networkLogger = logger.child({ component: 'network' });

export function useNetworkLogging() {
  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state) => {
      networkLogger.info('Network status changed', {
        isConnected: state.isConnected,
        type: state.type,
        isInternetReachable: state.isInternetReachable,
      });
    });

    return () => unsubscribe();
  }, []);
}
```

---

## 9. Storage Logging

```typescript
// lib/storage/logged-storage.ts
import AsyncStorage from '@react-native-async-storage/async-storage';
import { logger } from '@/lib/logger';

const storageLogger = logger.child({ component: 'storage' });

export const loggedStorage = {
  async getItem(key: string): Promise<string | null> {
    try {
      const value = await AsyncStorage.getItem(key);
      storageLogger.debug('Storage read', { key, found: value !== null });
      return value;
    } catch (error) {
      storageLogger.error('Storage read failed', error as Error, { key });
      throw error;
    }
  },

  async setItem(key: string, value: string): Promise<void> {
    try {
      await AsyncStorage.setItem(key, value);
      storageLogger.debug('Storage write', { key, size: value.length });
    } catch (error) {
      storageLogger.error('Storage write failed', error as Error, { key });
      throw error;
    }
  },

  async removeItem(key: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(key);
      storageLogger.debug('Storage remove', { key });
    } catch (error) {
      storageLogger.error('Storage remove failed', error as Error, { key });
      throw error;
    }
  },
};
```

---

## 10. Debug Tools

```typescript
// lib/logger/debug.ts
import { logger } from './logger';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as FileSystem from 'expo-file-system';
import * as Sharing from 'expo-sharing';

export async function exportLogs(): Promise<string> {
  const logs = await AsyncStorage.getItem('logs');
  const parsedLogs = logs ? JSON.parse(logs) : [];

  const content = parsedLogs
    .map((log: any) => JSON.stringify(log))
    .join('\n');

  const filename = `logs-${Date.now()}.json`;
  const path = `${FileSystem.documentDirectory}${filename}`;

  await FileSystem.writeAsStringAsync(path, content);

  if (await Sharing.isAvailableAsync()) {
    await Sharing.shareAsync(path);
  }

  return path;
}

export async function clearLogs(): Promise<void> {
  await AsyncStorage.removeItem('logs');
  logger.info('Logs cleared');
}

// Dev menu component
export function DevMenu() {
  if (!__DEV__) return null;

  return (
    <View>
      <Button title="Export Logs" onPress={exportLogs} />
      <Button title="Clear Logs" onPress={clearLogs} />
    </View>
  );
}
```
