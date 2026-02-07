# React Native Push Notification Patterns

Push notification patterns using Expo Notifications.

---

## 1. Setup

### Installation

```bash
npx expo install expo-notifications expo-device expo-constants
```

### App Configuration

```json
// app.json
{
  "expo": {
    "plugins": [
      [
        "expo-notifications",
        {
          "icon": "./assets/notification-icon.png",
          "color": "#ffffff",
          "sounds": ["./assets/notification-sound.wav"]
        }
      ]
    ],
    "android": {
      "useNextNotificationsApi": true
    }
  }
}
```

---

## 2. Notification Service

```typescript
// services/notifications.ts
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Configure notification behavior
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export async function registerForPushNotifications(): Promise<string | null> {
  if (!Device.isDevice) {
    console.log('Push notifications require a physical device');
    return null;
  }

  // Check existing permissions
  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  // Request permissions if not granted
  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    console.log('Push notification permission not granted');
    return null;
  }

  // Get push token
  try {
    const projectId = Constants.expoConfig?.extra?.eas?.projectId;
    const token = await Notifications.getExpoPushTokenAsync({ projectId });
    return token.data;
  } catch (error) {
    console.error('Failed to get push token:', error);
    return null;
  }
}

export async function setupAndroidChannel(): Promise<void> {
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'Default',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#FF231F7C',
    });

    await Notifications.setNotificationChannelAsync('messages', {
      name: 'Messages',
      importance: Notifications.AndroidImportance.HIGH,
      sound: 'notification-sound.wav',
    });

    await Notifications.setNotificationChannelAsync('updates', {
      name: 'Updates',
      importance: Notifications.AndroidImportance.DEFAULT,
    });
  }
}
```

---

## 3. Notification Hook

```typescript
// hooks/useNotifications.ts
import { useEffect, useRef, useState, useCallback } from 'react';
import * as Notifications from 'expo-notifications';
import { useRouter } from 'expo-router';
import {
  registerForPushNotifications,
  setupAndroidChannel,
} from '@/services/notifications';
import { api } from '@/lib/api';

type NotificationData = {
  type: string;
  id?: string;
  url?: string;
};

export function useNotifications() {
  const [expoPushToken, setExpoPushToken] = useState<string | null>(null);
  const [notification, setNotification] =
    useState<Notifications.Notification | null>(null);
  const notificationListener = useRef<Notifications.Subscription>();
  const responseListener = useRef<Notifications.Subscription>();
  const router = useRouter();

  const handleNotificationResponse = useCallback(
    (response: Notifications.NotificationResponse) => {
      const data = response.notification.request.content.data as NotificationData;

      switch (data.type) {
        case 'message':
          router.push(`/messages/${data.id}`);
          break;
        case 'post':
          router.push(`/posts/${data.id}`);
          break;
        case 'url':
          if (data.url) {
            router.push(data.url);
          }
          break;
        default:
          console.log('Unknown notification type:', data.type);
      }
    },
    [router]
  );

  useEffect(() => {
    // Setup
    setupAndroidChannel();

    // Register for push notifications
    registerForPushNotifications().then((token) => {
      if (token) {
        setExpoPushToken(token);
        // Send token to backend
        api.user.updatePushToken(token);
      }
    });

    // Listen for incoming notifications
    notificationListener.current =
      Notifications.addNotificationReceivedListener((notification) => {
        setNotification(notification);
      });

    // Listen for notification taps
    responseListener.current =
      Notifications.addNotificationResponseReceivedListener(
        handleNotificationResponse
      );

    // Check if app was opened from notification
    Notifications.getLastNotificationResponseAsync().then((response) => {
      if (response) {
        handleNotificationResponse(response);
      }
    });

    return () => {
      if (notificationListener.current) {
        Notifications.removeNotificationSubscription(notificationListener.current);
      }
      if (responseListener.current) {
        Notifications.removeNotificationSubscription(responseListener.current);
      }
    };
  }, [handleNotificationResponse]);

  return {
    expoPushToken,
    notification,
  };
}
```

---

## 4. Local Notifications

```typescript
// services/localNotifications.ts
import * as Notifications from 'expo-notifications';

export async function scheduleLocalNotification({
  title,
  body,
  data,
  trigger,
}: {
  title: string;
  body: string;
  data?: Record<string, unknown>;
  trigger?: Notifications.NotificationTriggerInput;
}): Promise<string> {
  return Notifications.scheduleNotificationAsync({
    content: {
      title,
      body,
      data,
      sound: true,
    },
    trigger: trigger ?? null, // null = immediate
  });
}

export async function scheduleReminder({
  title,
  body,
  date,
  data,
}: {
  title: string;
  body: string;
  date: Date;
  data?: Record<string, unknown>;
}): Promise<string> {
  return scheduleLocalNotification({
    title,
    body,
    data,
    trigger: { date },
  });
}

export async function scheduleDailyReminder({
  title,
  body,
  hour,
  minute,
}: {
  title: string;
  body: string;
  hour: number;
  minute: number;
}): Promise<string> {
  return scheduleLocalNotification({
    title,
    body,
    trigger: {
      hour,
      minute,
      repeats: true,
    },
  });
}

export async function cancelNotification(id: string): Promise<void> {
  await Notifications.cancelScheduledNotificationAsync(id);
}

export async function cancelAllNotifications(): Promise<void> {
  await Notifications.cancelAllScheduledNotificationsAsync();
}

export async function getScheduledNotifications(): Promise<
  Notifications.NotificationRequest[]
> {
  return Notifications.getAllScheduledNotificationsAsync();
}
```

---

## 5. Badge Management

```typescript
// services/badge.ts
import * as Notifications from 'expo-notifications';

export async function setBadgeCount(count: number): Promise<void> {
  await Notifications.setBadgeCountAsync(count);
}

export async function getBadgeCount(): Promise<number> {
  return Notifications.getBadgeCountAsync();
}

export async function clearBadge(): Promise<void> {
  await Notifications.setBadgeCountAsync(0);
}

export async function incrementBadge(): Promise<void> {
  const current = await getBadgeCount();
  await setBadgeCount(current + 1);
}
```

---

## 6. Notification Preferences

```typescript
// hooks/useNotificationPreferences.ts
import { useState, useEffect, useCallback } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '@/lib/api';

type NotificationPreferences = {
  messages: boolean;
  mentions: boolean;
  likes: boolean;
  comments: boolean;
  follows: boolean;
  updates: boolean;
  marketing: boolean;
};

const DEFAULT_PREFERENCES: NotificationPreferences = {
  messages: true,
  mentions: true,
  likes: true,
  comments: true,
  follows: true,
  updates: true,
  marketing: false,
};

const STORAGE_KEY = 'notification_preferences';

export function useNotificationPreferences() {
  const [preferences, setPreferences] =
    useState<NotificationPreferences>(DEFAULT_PREFERENCES);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      const stored = await AsyncStorage.getItem(STORAGE_KEY);
      if (stored) {
        setPreferences(JSON.parse(stored));
      }
    } catch (error) {
      console.error('Failed to load notification preferences:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const updatePreference = useCallback(
    async (key: keyof NotificationPreferences, value: boolean) => {
      const updated = { ...preferences, [key]: value };
      setPreferences(updated);

      try {
        await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
        await api.user.updateNotificationPreferences(updated);
      } catch (error) {
        // Revert on failure
        setPreferences(preferences);
        throw error;
      }
    },
    [preferences]
  );

  return {
    preferences,
    isLoading,
    updatePreference,
  };
}
```

---

## 7. Notification Settings Screen

```typescript
// screens/NotificationSettingsScreen.tsx
import { View, Text, StyleSheet, Switch, ActivityIndicator } from 'react-native';
import { useNotificationPreferences } from '@/hooks/useNotificationPreferences';

const PREFERENCE_LABELS: Record<string, { title: string; description: string }> = {
  messages: {
    title: 'Direct Messages',
    description: 'New messages from other users',
  },
  mentions: {
    title: 'Mentions',
    description: 'When someone mentions you',
  },
  likes: {
    title: 'Likes',
    description: 'When someone likes your content',
  },
  comments: {
    title: 'Comments',
    description: 'New comments on your posts',
  },
  follows: {
    title: 'New Followers',
    description: 'When someone follows you',
  },
  updates: {
    title: 'App Updates',
    description: 'New features and improvements',
  },
  marketing: {
    title: 'Promotions',
    description: 'Special offers and promotions',
  },
};

export function NotificationSettingsScreen() {
  const { preferences, isLoading, updatePreference } = useNotificationPreferences();

  if (isLoading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {Object.entries(preferences).map(([key, value]) => {
        const label = PREFERENCE_LABELS[key];
        return (
          <View key={key} style={styles.row}>
            <View style={styles.labelContainer}>
              <Text style={styles.title}>{label.title}</Text>
              <Text style={styles.description}>{label.description}</Text>
            </View>
            <Switch
              value={value}
              onValueChange={(newValue) =>
                updatePreference(key as keyof typeof preferences, newValue)
              }
            />
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  loading: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  labelContainer: {
    flex: 1,
    marginRight: 16,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  description: {
    fontSize: 14,
    color: '#666',
  },
});
```

---

## 8. Backend Integration

```typescript
// services/api/notifications.ts
import { api } from '@/lib/api';

export const notificationsApi = {
  async registerToken(token: string): Promise<void> {
    await api.post('/notifications/register', { token });
  },

  async unregisterToken(token: string): Promise<void> {
    await api.post('/notifications/unregister', { token });
  },

  async updatePreferences(
    preferences: Record<string, boolean>
  ): Promise<void> {
    await api.put('/notifications/preferences', preferences);
  },

  async markAsRead(notificationId: string): Promise<void> {
    await api.post(`/notifications/${notificationId}/read`);
  },

  async markAllAsRead(): Promise<void> {
    await api.post('/notifications/read-all');
  },

  async getHistory(page: number = 1): Promise<Notification[]> {
    const response = await api.get('/notifications', { params: { page } });
    return response.data;
  },
};
```

---

## 9. Rich Notifications

```typescript
// services/richNotifications.ts
import * as Notifications from 'expo-notifications';

export async function sendRichNotification({
  title,
  body,
  imageUrl,
  actions,
  data,
}: {
  title: string;
  body: string;
  imageUrl?: string;
  actions?: Array<{ identifier: string; title: string }>;
  data?: Record<string, unknown>;
}): Promise<string> {
  // Define category with actions
  if (actions && actions.length > 0) {
    await Notifications.setNotificationCategoryAsync('interactive', actions);
  }

  return Notifications.scheduleNotificationAsync({
    content: {
      title,
      body,
      data,
      categoryIdentifier: actions ? 'interactive' : undefined,
      attachments: imageUrl
        ? [{ identifier: 'image', url: imageUrl, type: 'image' }]
        : undefined,
    },
    trigger: null,
  });
}

// Example: Message notification with reply action
export async function sendMessageNotification({
  senderName,
  message,
  avatarUrl,
  conversationId,
}: {
  senderName: string;
  message: string;
  avatarUrl: string;
  conversationId: string;
}): Promise<string> {
  return sendRichNotification({
    title: senderName,
    body: message,
    imageUrl: avatarUrl,
    actions: [
      { identifier: 'reply', title: 'Reply' },
      { identifier: 'mark-read', title: 'Mark as Read' },
    ],
    data: { type: 'message', conversationId },
  });
}
```

---

## 10. Testing Notifications

```typescript
// __tests__/notifications.test.ts
import * as Notifications from 'expo-notifications';
import { registerForPushNotifications } from '../services/notifications';

jest.mock('expo-notifications');
jest.mock('expo-device', () => ({
  isDevice: true,
}));

describe('Push Notifications', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('requests permissions and returns token', async () => {
    (Notifications.getPermissionsAsync as jest.Mock).mockResolvedValue({
      status: 'granted',
    });
    (Notifications.getExpoPushTokenAsync as jest.Mock).mockResolvedValue({
      data: 'ExponentPushToken[xxx]',
    });

    const token = await registerForPushNotifications();

    expect(token).toBe('ExponentPushToken[xxx]');
  });

  it('returns null when permission denied', async () => {
    (Notifications.getPermissionsAsync as jest.Mock).mockResolvedValue({
      status: 'denied',
    });
    (Notifications.requestPermissionsAsync as jest.Mock).mockResolvedValue({
      status: 'denied',
    });

    const token = await registerForPushNotifications();

    expect(token).toBeNull();
  });
});
```
