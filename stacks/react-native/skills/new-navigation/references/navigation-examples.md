# React Navigation Examples

Reference examples for generating navigation configurations.

## Type Definitions

```typescript
// navigation/types.ts
import type { BottomTabScreenProps } from '@react-navigation/bottom-tabs';
import type { DrawerScreenProps } from '@react-navigation/drawer';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { CompositeScreenProps, NavigatorScreenParams } from '@react-navigation/native';

// Root stack (handles auth state)
export type RootStackParamList = {
  Auth: NavigatorScreenParams<AuthStackParamList>;
  Main: NavigatorScreenParams<TabParamList>;
  Onboarding: undefined;
};

// Auth stack
export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
  ForgotPassword: undefined;
  ResetPassword: { token: string };
};

// Tab navigator
export type TabParamList = {
  HomeTab: NavigatorScreenParams<HomeStackParamList>;
  SearchTab: undefined;
  NotificationsTab: undefined;
  ProfileTab: NavigatorScreenParams<ProfileStackParamList>;
};

// Home stack (nested in tab)
export type HomeStackParamList = {
  Home: undefined;
  Details: { id: string; title?: string };
  Create: undefined;
};

// Profile stack (nested in tab)
export type ProfileStackParamList = {
  Profile: undefined;
  EditProfile: undefined;
  Settings: undefined;
};

// Screen props types
export type RootStackScreenProps<T extends keyof RootStackParamList> =
  NativeStackScreenProps<RootStackParamList, T>;

export type AuthStackScreenProps<T extends keyof AuthStackParamList> =
  CompositeScreenProps<
    NativeStackScreenProps<AuthStackParamList, T>,
    RootStackScreenProps<keyof RootStackParamList>
  >;

export type TabScreenProps<T extends keyof TabParamList> =
  CompositeScreenProps<
    BottomTabScreenProps<TabParamList, T>,
    RootStackScreenProps<keyof RootStackParamList>
  >;

export type HomeStackScreenProps<T extends keyof HomeStackParamList> =
  CompositeScreenProps<
    NativeStackScreenProps<HomeStackParamList, T>,
    TabScreenProps<'HomeTab'>
  >;

// Type for useNavigation hook
declare global {
  namespace ReactNavigation {
    interface RootParamList extends RootStackParamList {}
  }
}
```

## Root Navigator

```typescript
// navigation/RootNavigator.tsx
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useAuth } from '@/hooks/useAuth';
import { SplashScreen } from '@/screens/SplashScreen';
import { OnboardingScreen } from '@/screens/OnboardingScreen';
import { TabNavigator } from './TabNavigator';
import { AuthNavigator } from './AuthNavigator';
import { linking } from './linking';
import type { RootStackParamList } from './types';

const Stack = createNativeStackNavigator<RootStackParamList>();

export function RootNavigator() {
  const { isAuthenticated, isLoading, hasCompletedOnboarding } = useAuth();

  if (isLoading) {
    return <SplashScreen />;
  }

  return (
    <NavigationContainer linking={linking}>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {!isAuthenticated ? (
          <Stack.Screen name="Auth" component={AuthNavigator} />
        ) : !hasCompletedOnboarding ? (
          <Stack.Screen name="Onboarding" component={OnboardingScreen} />
        ) : (
          <Stack.Screen name="Main" component={TabNavigator} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
```

## Tab Navigator

```typescript
// navigation/TabNavigator.tsx
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Home, Search, Bell, User } from 'lucide-react-native';
import { HomeStack } from './HomeStack';
import { SearchScreen } from '@/screens/SearchScreen';
import { NotificationsScreen } from '@/screens/NotificationsScreen';
import { ProfileStack } from './ProfileStack';
import type { TabParamList } from './types';

const Tab = createBottomTabNavigator<TabParamList>();

export function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: '#007AFF',
        tabBarInactiveTintColor: '#8E8E93',
        tabBarStyle: {
          borderTopWidth: 1,
          borderTopColor: '#E5E5EA',
          paddingBottom: 8,
          paddingTop: 8,
          height: 60,
        },
        tabBarLabelStyle: {
          fontSize: 12,
        },
        headerShown: false,
      }}
    >
      <Tab.Screen
        name="HomeTab"
        component={HomeStack}
        options={{
          tabBarLabel: 'Home',
          tabBarIcon: ({ color, size }) => <Home color={color} size={size} />,
        }}
      />
      <Tab.Screen
        name="SearchTab"
        component={SearchScreen}
        options={{
          tabBarLabel: 'Search',
          tabBarIcon: ({ color, size }) => <Search color={color} size={size} />,
        }}
      />
      <Tab.Screen
        name="NotificationsTab"
        component={NotificationsScreen}
        options={{
          tabBarLabel: 'Notifications',
          tabBarIcon: ({ color, size }) => <Bell color={color} size={size} />,
          tabBarBadge: 3, // Dynamic badge count
        }}
      />
      <Tab.Screen
        name="ProfileTab"
        component={ProfileStack}
        options={{
          tabBarLabel: 'Profile',
          tabBarIcon: ({ color, size }) => <User color={color} size={size} />,
        }}
      />
    </Tab.Navigator>
  );
}
```

## Stack Navigator

```typescript
// navigation/HomeStack.tsx
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { HomeScreen } from '@/screens/HomeScreen';
import { DetailsScreen } from '@/screens/DetailsScreen';
import { CreateScreen } from '@/screens/CreateScreen';
import type { HomeStackParamList } from './types';

const Stack = createNativeStackNavigator<HomeStackParamList>();

export function HomeStack() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: true,
        headerBackTitleVisible: false,
        headerTintColor: '#007AFF',
        headerStyle: {
          backgroundColor: '#FFFFFF',
        },
        headerShadowVisible: false,
      }}
    >
      <Stack.Screen
        name="Home"
        component={HomeScreen}
        options={{
          title: 'Home',
          headerLargeTitle: true,
        }}
      />
      <Stack.Screen
        name="Details"
        component={DetailsScreen}
        options={({ route }) => ({
          title: route.params.title ?? 'Details',
        })}
      />
      <Stack.Screen
        name="Create"
        component={CreateScreen}
        options={{
          title: 'Create New',
          presentation: 'modal',
          headerLeft: () => null,
        }}
      />
    </Stack.Navigator>
  );
}
```

## Drawer Navigator

```typescript
// navigation/DrawerNavigator.tsx
import { createDrawerNavigator } from '@react-navigation/drawer';
import { Home, Settings, HelpCircle, LogOut } from 'lucide-react-native';
import { CustomDrawerContent } from '@/components/navigation/CustomDrawerContent';
import { HomeScreen } from '@/screens/HomeScreen';
import { SettingsScreen } from '@/screens/SettingsScreen';
import { HelpScreen } from '@/screens/HelpScreen';
import type { DrawerParamList } from './types';

const Drawer = createDrawerNavigator<DrawerParamList>();

export function DrawerNavigator() {
  return (
    <Drawer.Navigator
      drawerContent={(props) => <CustomDrawerContent {...props} />}
      screenOptions={{
        drawerActiveTintColor: '#007AFF',
        drawerInactiveTintColor: '#8E8E93',
        drawerLabelStyle: {
          marginLeft: -16,
          fontSize: 16,
        },
        headerShown: true,
      }}
    >
      <Drawer.Screen
        name="Home"
        component={HomeScreen}
        options={{
          title: 'Home',
          drawerIcon: ({ color, size }) => <Home color={color} size={size} />,
        }}
      />
      <Drawer.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          title: 'Settings',
          drawerIcon: ({ color, size }) => <Settings color={color} size={size} />,
        }}
      />
      <Drawer.Screen
        name="Help"
        component={HelpScreen}
        options={{
          title: 'Help & Support',
          drawerIcon: ({ color, size }) => <HelpCircle color={color} size={size} />,
        }}
      />
    </Drawer.Navigator>
  );
}
```

## Custom Drawer Content

```typescript
// components/navigation/CustomDrawerContent.tsx
import {
  DrawerContentScrollView,
  DrawerItemList,
  type DrawerContentComponentProps,
} from '@react-navigation/drawer';
import { View, Text, StyleSheet, Pressable, Image } from 'react-native';
import { LogOut } from 'lucide-react-native';
import { useAuth } from '@/hooks/useAuth';

export function CustomDrawerContent(props: DrawerContentComponentProps) {
  const { user, logout } = useAuth();

  return (
    <DrawerContentScrollView {...props}>
      {/* User profile section */}
      <View style={styles.profileSection}>
        <Image source={{ uri: user?.avatarUrl }} style={styles.avatar} />
        <Text style={styles.userName}>{user?.name}</Text>
        <Text style={styles.userEmail}>{user?.email}</Text>
      </View>

      {/* Navigation items */}
      <DrawerItemList {...props} />

      {/* Logout button */}
      <Pressable style={styles.logoutButton} onPress={logout}>
        <LogOut color="#FF3B30" size={20} />
        <Text style={styles.logoutText}>Logout</Text>
      </Pressable>
    </DrawerContentScrollView>
  );
}

const styles = StyleSheet.create({
  profileSection: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
    marginBottom: 8,
  },
  avatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    marginBottom: 8,
  },
  userName: {
    fontSize: 18,
    fontWeight: '600',
  },
  userEmail: {
    fontSize: 14,
    color: '#8E8E93',
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    marginTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  logoutText: {
    marginLeft: 16,
    fontSize: 16,
    color: '#FF3B30',
  },
});
```

## Deep Linking

```typescript
// navigation/linking.ts
import { type LinkingOptions } from '@react-navigation/native';
import * as Linking from 'expo-linking';
import type { RootStackParamList } from './types';

const prefix = Linking.createURL('/');

export const linking: LinkingOptions<RootStackParamList> = {
  prefixes: [prefix, 'myapp://', 'https://myapp.com'],
  config: {
    screens: {
      Auth: {
        screens: {
          Login: 'login',
          Register: 'register',
          ForgotPassword: 'forgot-password',
          ResetPassword: 'reset-password/:token',
        },
      },
      Main: {
        screens: {
          HomeTab: {
            screens: {
              Home: 'home',
              Details: 'details/:id',
            },
          },
          SearchTab: 'search',
          NotificationsTab: 'notifications',
          ProfileTab: {
            screens: {
              Profile: 'profile',
              EditProfile: 'profile/edit',
              Settings: 'settings',
            },
          },
        },
      },
    },
  },
};
```

## Navigation Utilities

```typescript
// navigation/utils.ts
import { createNavigationContainerRef } from '@react-navigation/native';
import type { RootStackParamList } from './types';

export const navigationRef = createNavigationContainerRef<RootStackParamList>();

/**
 * Navigate from outside React components.
 * Useful for push notifications, deep links, etc.
 */
export function navigate<RouteName extends keyof RootStackParamList>(
  name: RouteName,
  params?: RootStackParamList[RouteName]
) {
  if (navigationRef.isReady()) {
    navigationRef.navigate(name, params);
  }
}

/**
 * Reset navigation state.
 * Useful after logout.
 */
export function resetToAuth() {
  if (navigationRef.isReady()) {
    navigationRef.reset({
      index: 0,
      routes: [{ name: 'Auth' }],
    });
  }
}

/**
 * Get current route name.
 */
export function getCurrentRouteName(): string | undefined {
  if (navigationRef.isReady()) {
    return navigationRef.getCurrentRoute()?.name;
  }
  return undefined;
}
```

## Typed Screen Component

```typescript
// screens/DetailsScreen.tsx
import { View, Text, StyleSheet } from 'react-native';
import type { HomeStackScreenProps } from '@/navigation/types';

type Props = HomeStackScreenProps<'Details'>;

export function DetailsScreen({ route, navigation }: Props) {
  const { id, title } = route.params;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{title ?? 'Details'}</Text>
      <Text style={styles.id}>ID: {id}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  id: {
    fontSize: 16,
    color: '#666',
  },
});
```

## Using useNavigation Hook

```typescript
// components/ItemCard.tsx
import { Pressable, Text, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { HomeStackParamList } from '@/navigation/types';

type NavigationProp = NativeStackNavigationProp<HomeStackParamList>;

type ItemCardProps = {
  id: string;
  title: string;
};

export function ItemCard({ id, title }: ItemCardProps) {
  const navigation = useNavigation<NavigationProp>();

  const handlePress = () => {
    navigation.navigate('Details', { id, title });
  };

  return (
    <Pressable style={styles.card} onPress={handlePress}>
      <Text style={styles.title}>{title}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: 16,
    backgroundColor: '#fff',
    borderRadius: 8,
    marginBottom: 8,
  },
  title: {
    fontSize: 16,
    fontWeight: '500',
  },
});
```
