---
name: new-navigation
description: Generate tab, stack, or drawer navigation with screens
---

# /new-navigation

## What This Does

Creates React Navigation configuration for tab, stack, or drawer navigation
patterns. Generates typed navigation components, screen definitions, and
navigation utilities.

## Usage

```
/new-navigation tabs                    # Bottom tab navigation
/new-navigation stack Home              # Stack navigator for Home
/new-navigation drawer                  # Drawer navigation
/new-navigation tabs --screens=Home,Profile,Settings
```

## How It Works

### 1. Determine Navigation Type

Based on the argument, create:
- **tabs**: Bottom tab navigation with icons
- **stack [name]**: Stack navigator for a section
- **drawer**: Side drawer navigation

### 2. Read Existing Patterns

Before generating, read:
- `patterns/mobile-patterns.md` for conventions
- `skills/new-navigation/references/navigation-examples.md` for examples
- Existing navigation in `navigation/` for project patterns

### 3. Generate Files

#### Root Navigator: `navigation/RootNavigator.tsx`

```typescript
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

const Stack = createNativeStackNavigator<RootStackParamList>();

export function RootNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        {/* Screens */}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
```

#### Types: `navigation/types.ts`

```typescript
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

export type RootStackParamList = {
  Home: undefined;
  Details: { id: string };
};

export type RootStackScreenProps<T extends keyof RootStackParamList> =
  NativeStackScreenProps<RootStackParamList, T>;
```

### 4. Verify

Run type checking:
```bash
npx tsc --noEmit
```

## Rules

- Always type navigation with ParamList
- Use native stack navigator for performance
- Keep navigation configuration centralized
- Use typed navigation props in screens
- Consider deep linking requirements
- Handle authentication state changes

## Generated Files

```
navigation/RootNavigator.tsx
navigation/types.ts
navigation/<NavigatorName>.tsx (for nested navigators)
```

## Example Output

For `/new-navigation tabs`:

**Tab Navigator:** `navigation/TabNavigator.tsx`
```typescript
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Home, User, Settings } from 'lucide-react-native';
import { HomeScreen } from '@/screens/HomeScreen';
import { ProfileScreen } from '@/screens/ProfileScreen';
import { SettingsScreen } from '@/screens/SettingsScreen';
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
        },
        headerShown: false,
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarLabel: 'Home',
          tabBarIcon: ({ color, size }) => <Home color={color} size={size} />,
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          tabBarLabel: 'Profile',
          tabBarIcon: ({ color, size }) => <User color={color} size={size} />,
        }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          tabBarLabel: 'Settings',
          tabBarIcon: ({ color, size }) => <Settings color={color} size={size} />,
        }}
      />
    </Tab.Navigator>
  );
}
```

**Types:** `navigation/types.ts`
```typescript
import type { BottomTabScreenProps } from '@react-navigation/bottom-tabs';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { CompositeScreenProps, NavigatorScreenParams } from '@react-navigation/native';

// Root stack (auth flow)
export type RootStackParamList = {
  Auth: undefined;
  Main: NavigatorScreenParams<TabParamList>;
};

// Tab navigator
export type TabParamList = {
  Home: undefined;
  Profile: undefined;
  Settings: undefined;
};

// Screen props
export type RootStackScreenProps<T extends keyof RootStackParamList> =
  NativeStackScreenProps<RootStackParamList, T>;

export type TabScreenProps<T extends keyof TabParamList> = CompositeScreenProps<
  BottomTabScreenProps<TabParamList, T>,
  RootStackScreenProps<keyof RootStackParamList>
>;

// Type for useNavigation hook
declare global {
  namespace ReactNavigation {
    interface RootParamList extends RootStackParamList {}
  }
}
```

For `/new-navigation stack Home`:

**Stack Navigator:** `navigation/HomeStack.tsx`
```typescript
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
      }}
    >
      <Stack.Screen
        name="HomeList"
        component={HomeScreen}
        options={{ title: 'Home' }}
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
        }}
      />
    </Stack.Navigator>
  );
}
```

**Root Navigator:** `navigation/RootNavigator.tsx`
```typescript
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useAuth } from '@/hooks/useAuth';
import { TabNavigator } from './TabNavigator';
import { AuthNavigator } from './AuthNavigator';
import type { RootStackParamList } from './types';

const Stack = createNativeStackNavigator<RootStackParamList>();

export function RootNavigator() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <SplashScreen />;
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {isAuthenticated ? (
          <Stack.Screen name="Main" component={TabNavigator} />
        ) : (
          <Stack.Screen name="Auth" component={AuthNavigator} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
```
