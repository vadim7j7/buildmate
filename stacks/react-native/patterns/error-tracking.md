# React Native Error Tracking Patterns

Error tracking patterns using Sentry for React Native applications.

---

## 1. Sentry Setup

### Installation

```bash
npx expo install @sentry/react-native
```

### Configuration

```typescript
// lib/sentry.ts
import * as Sentry from '@sentry/react-native';
import Constants from 'expo-constants';

export function initSentry() {
  Sentry.init({
    dsn: process.env.EXPO_PUBLIC_SENTRY_DSN,
    environment: __DEV__ ? 'development' : 'production',
    release: Constants.expoConfig?.version,
    dist: Constants.expoConfig?.ios?.buildNumber || Constants.expoConfig?.android?.versionCode?.toString(),

    // Performance monitoring
    tracesSampleRate: __DEV__ ? 1.0 : 0.2,

    // Enable native crash reporting
    enableNative: true,
    enableNativeCrashHandling: true,

    // Attach screenshots on errors
    attachScreenshot: true,

    // Filter events
    beforeSend(event, hint) {
      // Don't send in development
      if (__DEV__) {
        console.log('Sentry event (dev):', event);
        return null;
      }

      return event;
    },

    // Filter breadcrumbs
    beforeBreadcrumb(breadcrumb) {
      // Filter out noisy console breadcrumbs
      if (breadcrumb.category === 'console' && breadcrumb.level === 'debug') {
        return null;
      }
      return breadcrumb;
    },
  });
}

// App.tsx
import { initSentry } from '@/lib/sentry';

initSentry();

export default function App() {
  return (
    <Sentry.ErrorBoundary fallback={<ErrorScreen />}>
      <AppContent />
    </Sentry.ErrorBoundary>
  );
}
```

---

## 2. App Configuration

```javascript
// app.config.js
export default {
  expo: {
    plugins: [
      [
        '@sentry/react-native/expo',
        {
          organization: process.env.SENTRY_ORG,
          project: process.env.SENTRY_PROJECT,
          url: 'https://sentry.io/',
        },
      ],
    ],
    hooks: {
      postPublish: [
        {
          file: 'sentry-expo/upload-sourcemaps',
          config: {
            organization: process.env.SENTRY_ORG,
            project: process.env.SENTRY_PROJECT,
            authToken: process.env.SENTRY_AUTH_TOKEN,
          },
        },
      ],
    },
  },
};
```

---

## 3. Error Boundary Component

```typescript
// components/ErrorBoundary.tsx
import React from 'react';
import { View, Text, Button, StyleSheet } from 'react-native';
import * as Sentry from '@sentry/react-native';

interface FallbackProps {
  error: Error;
  resetError: () => void;
  eventId?: string;
}

function ErrorFallback({ error, resetError, eventId }: FallbackProps) {
  const handleReportFeedback = () => {
    if (eventId) {
      Sentry.showReportDialog({
        eventId,
        title: 'Tell us what happened',
        subtitle: "We're sorry for the inconvenience",
      });
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Oops! Something went wrong</Text>
      <Text style={styles.message}>{error.message}</Text>

      <View style={styles.buttons}>
        <Button title="Try Again" onPress={resetError} />
        {eventId && (
          <Button title="Report Issue" onPress={handleReportFeedback} />
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  message: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
  },
  buttons: {
    gap: 10,
  },
});

// Usage with Sentry
export function AppErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <Sentry.ErrorBoundary
      fallback={({ error, resetError, eventId }) => (
        <ErrorFallback
          error={error}
          resetError={resetError}
          eventId={eventId}
        />
      )}
      beforeCapture={(scope) => {
        scope.setTag('boundary', 'app');
      }}
    >
      {children}
    </Sentry.ErrorBoundary>
  );
}
```

---

## 4. Navigation Integration

```typescript
// lib/sentry-navigation.ts
import * as Sentry from '@sentry/react-native';
import { NavigationContainerRef } from '@react-navigation/native';
import { useRef } from 'react';

export function useSentryNavigationIntegration() {
  const navigationRef = useRef<NavigationContainerRef<any>>(null);
  const routingInstrumentation = Sentry.reactNavigationIntegration({
    routeChangeTimeoutMs: 1000,
    enableTimeToInitialDisplay: true,
  });

  const onReady = () => {
    if (navigationRef.current) {
      routingInstrumentation.registerNavigationContainer(navigationRef);
    }
  };

  return {
    navigationRef,
    onReady,
    routingInstrumentation,
  };
}

// Update Sentry init
Sentry.init({
  // ... other config
  integrations: [
    Sentry.reactNativeTracingIntegration({
      routingInstrumentation,
      enableNativeFramesTracking: true,
    }),
  ],
});

// App.tsx
function App() {
  const { navigationRef, onReady } = useSentryNavigationIntegration();

  return (
    <NavigationContainer ref={navigationRef} onReady={onReady}>
      <Stack.Navigator>
        {/* screens */}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
```

---

## 5. User Context

```typescript
// lib/sentry-user.ts
import * as Sentry from '@sentry/react-native';

interface User {
  id: string;
  email?: string;
  name?: string;
  plan?: string;
}

export function setSentryUser(user: User | null) {
  if (user) {
    Sentry.setUser({
      id: user.id,
      email: user.email,
      username: user.name,
    });

    Sentry.setTag('user_plan', user.plan || 'free');
  } else {
    Sentry.setUser(null);
  }
}

export function addSentryBreadcrumb(
  category: string,
  message: string,
  data?: Record<string, unknown>
) {
  Sentry.addBreadcrumb({
    category,
    message,
    data,
    level: 'info',
  });
}

// Usage in auth flow
function useAuth() {
  const login = async (credentials: LoginCredentials) => {
    const user = await authService.login(credentials);
    setSentryUser(user);
    addSentryBreadcrumb('auth', 'User logged in', { userId: user.id });
    return user;
  };

  const logout = async () => {
    await authService.logout();
    setSentryUser(null);
    addSentryBreadcrumb('auth', 'User logged out');
  };

  return { login, logout };
}
```

---

## 6. Custom Error Classes

```typescript
// lib/errors.ts
import * as Sentry from '@sentry/react-native';

export class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public context?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'AppError';
  }

  report(extra?: Record<string, unknown>) {
    Sentry.withScope((scope) => {
      scope.setTag('error_code', this.code);
      scope.setExtras({ ...this.context, ...extra });
      Sentry.captureException(this);
    });
  }
}

export class NetworkError extends AppError {
  constructor(
    message: string,
    public statusCode?: number,
    public response?: unknown
  ) {
    super(message, 'NETWORK_ERROR', { statusCode, response });
    this.name = 'NetworkError';
  }
}

export class ValidationError extends AppError {
  constructor(message: string, public errors: Record<string, string[]>) {
    super(message, 'VALIDATION_ERROR', { errors });
    this.name = 'ValidationError';
  }
}

export class AuthError extends AppError {
  constructor(message: string = 'Authentication required') {
    super(message, 'AUTH_ERROR');
    this.name = 'AuthError';
  }
}

// Usage
try {
  await api.createOrder(data);
} catch (error) {
  if (error instanceof NetworkError) {
    error.report({ orderId: data.id });
    showToast('Network error. Please try again.');
  }
}
```

---

## 7. API Error Handling

```typescript
// lib/api/error-handler.ts
import * as Sentry from '@sentry/react-native';
import { NetworkError, AuthError } from '@/lib/errors';

export async function handleApiError(
  response: Response,
  requestInfo: { url: string; method: string }
): Promise<never> {
  let errorBody: unknown;

  try {
    errorBody = await response.json();
  } catch {
    errorBody = await response.text();
  }

  const error = new NetworkError(
    `API Error: ${response.status}`,
    response.status,
    errorBody
  );

  // Add breadcrumb
  Sentry.addBreadcrumb({
    category: 'api',
    message: `${requestInfo.method} ${requestInfo.url} failed`,
    data: {
      status: response.status,
      response: errorBody,
    },
    level: 'error',
  });

  // Report server errors
  if (response.status >= 500) {
    Sentry.captureException(error, {
      extra: {
        url: requestInfo.url,
        method: requestInfo.method,
        status: response.status,
        response: errorBody,
      },
    });
  }

  // Handle auth errors
  if (response.status === 401) {
    throw new AuthError('Session expired');
  }

  throw error;
}
```

---

## 8. Performance Monitoring

```typescript
// lib/sentry-performance.ts
import * as Sentry from '@sentry/react-native';

export function measureOperation<T>(
  name: string,
  operation: string,
  fn: () => Promise<T>,
  data?: Record<string, unknown>
): Promise<T> {
  return Sentry.startSpan(
    {
      name,
      op: operation,
      attributes: data,
    },
    async (span) => {
      try {
        const result = await fn();
        span.setStatus({ code: 1 }); // OK
        return result;
      } catch (error) {
        span.setStatus({ code: 2, message: 'Error' });
        throw error;
      }
    }
  );
}

// Usage
const order = await measureOperation(
  'Create Order',
  'order.create',
  () => api.orders.create(data),
  { productCount: data.items.length }
);
```

---

## 9. Screen Tracking

```typescript
// hooks/useSentryScreenTracking.ts
import { useEffect } from 'react';
import * as Sentry from '@sentry/react-native';

export function useSentryScreenTracking(screenName: string) {
  useEffect(() => {
    // Set the current screen as a tag
    Sentry.setTag('current_screen', screenName);

    // Add breadcrumb
    Sentry.addBreadcrumb({
      category: 'navigation',
      message: `Viewed ${screenName}`,
      level: 'info',
    });

    return () => {
      Sentry.addBreadcrumb({
        category: 'navigation',
        message: `Left ${screenName}`,
        level: 'info',
      });
    };
  }, [screenName]);
}

// Usage
function ProductScreen() {
  useSentryScreenTracking('ProductScreen');

  return <View>...</View>;
}
```

---

## 10. Testing Error Tracking

```typescript
// lib/sentry-test.ts
import * as Sentry from '@sentry/react-native';

export function testSentryError() {
  try {
    throw new Error('Test Sentry error - please ignore');
  } catch (error) {
    Sentry.captureException(error);
  }
}

export function testSentryMessage() {
  Sentry.captureMessage('Test Sentry message - please ignore', 'info');
}

// Dev menu button
if (__DEV__) {
  DevMenu.registerItem({
    name: 'Test Sentry',
    onPress: () => {
      testSentryError();
      Alert.alert('Sentry Test', 'Test error sent to Sentry');
    },
  });
}
```

---

## 11. Offline Error Handling

```typescript
// lib/sentry-offline.ts
import * as Sentry from '@sentry/react-native';
import NetInfo from '@react-native-community/netinfo';
import AsyncStorage from '@react-native-async-storage/async-storage';

const OFFLINE_ERRORS_KEY = 'sentry_offline_errors';

export async function captureOfflineError(error: Error, context?: Record<string, unknown>) {
  const netState = await NetInfo.fetch();

  if (netState.isConnected) {
    // Online - send directly
    Sentry.captureException(error, { extra: context });
  } else {
    // Offline - queue for later
    const offlineErrors = await getOfflineErrors();
    offlineErrors.push({
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack,
      },
      context,
      timestamp: Date.now(),
    });
    await AsyncStorage.setItem(OFFLINE_ERRORS_KEY, JSON.stringify(offlineErrors));
  }
}

async function getOfflineErrors(): Promise<any[]> {
  const stored = await AsyncStorage.getItem(OFFLINE_ERRORS_KEY);
  return stored ? JSON.parse(stored) : [];
}

export async function flushOfflineErrors() {
  const errors = await getOfflineErrors();

  if (errors.length === 0) return;

  for (const item of errors) {
    const error = new Error(item.error.message);
    error.name = item.error.name;
    error.stack = item.error.stack;

    Sentry.captureException(error, {
      extra: {
        ...item.context,
        offlineTimestamp: item.timestamp,
      },
    });
  }

  await AsyncStorage.removeItem(OFFLINE_ERRORS_KEY);
}

// Flush when app comes online
NetInfo.addEventListener((state) => {
  if (state.isConnected) {
    flushOfflineErrors();
  }
});
```

---

## 12. Release Health

```typescript
// lib/sentry-release.ts
import * as Sentry from '@sentry/react-native';
import * as Application from 'expo-application';
import * as Device from 'expo-device';

export function configureSentryRelease() {
  // Set release and dist
  Sentry.setTag('app_version', Application.nativeApplicationVersion || 'unknown');
  Sentry.setTag('build_number', Application.nativeBuildVersion || 'unknown');

  // Set device info
  Sentry.setContext('device', {
    brand: Device.brand,
    modelName: Device.modelName,
    osName: Device.osName,
    osVersion: Device.osVersion,
    isDevice: Device.isDevice,
  });

  // Track session
  Sentry.startSession();
}

// Call on app start
configureSentryRelease();
```
