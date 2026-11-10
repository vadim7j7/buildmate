---
name: new-navigation
description: Generate expo-router tab, stack, or drawer layouts with typed routes
---

# /new-navigation

## What This Does

Creates expo-router file-based navigation: `_layout.tsx` files that render a
`Stack`, `Tabs`, or `Drawer` navigator, the route files inside them, route groups,
and dynamic routes. Navigation is **always** expo-router — never render a
`NavigationContainer` or call `createXNavigator()` from React Navigation directly
(the reviewer treats that as a BLOCKER).

## Usage

```
/new-navigation tabs                          # (tabs) group with a Tabs layout
/new-navigation stack items                   # src/app/items/ stack with list + [id]
/new-navigation drawer                        # (drawer) group with a Drawer layout
/new-navigation tabs --screens=index,profile,settings
```

## How It Works

### 1. Determine Navigation Type

- **tabs**: `src/app/(tabs)/_layout.tsx` with `<Tabs>` + one file per tab
- **stack [name]**: `src/app/<name>/_layout.tsx` with `<Stack>`, `index.tsx`, `[id].tsx`
- **drawer**: `src/app/(drawer)/_layout.tsx` with `<Drawer>` from `expo-router/drawer`
  (needs `npx expo install @react-navigation/drawer react-native-gesture-handler react-native-reanimated`)

Parenthesised folders such as `(tabs)` are **route groups**: they organise layouts
without adding a URL segment (`src/app/(tabs)/profile.tsx` is `/profile`).

### 2. Read Existing Patterns

Before generating, read:
- `patterns/mobile-patterns.md` for conventions
- `skills/new-navigation/references/navigation-examples.md` for examples
- The existing `src/app/` tree (especially `src/app/_layout.tsx`) — never add a
  second root layout

### 3. Generate Files

#### Root layout: `src/app/_layout.tsx`

```tsx
import { Stack } from 'expo-router';

export default function RootLayout() {
  return (
    <Stack>
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen name="(modals)" options={{ presentation: 'modal' }} />
    </Stack>
  );
}
```

#### Tabs layout: `src/app/(tabs)/_layout.tsx`

```tsx
import { Tabs } from 'expo-router';
import { Home, User } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

export default function TabsLayout() {
  const { t } = useTranslation();
  return (
    <Tabs screenOptions={{ headerShown: false }}>
      <Tabs.Screen
        name="index"
        options={{
          title: t('tabs.home'),
          tabBarIcon: ({ color, size }) => <Home color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: t('tabs.profile'),
          tabBarIcon: ({ color, size }) => <User color={color} size={size} />,
        }}
      />
    </Tabs>
  );
}
```

#### Dynamic route: `src/app/items/[id].tsx`

```tsx
import { Stack, useLocalSearchParams } from 'expo-router';

export default function ItemDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  // load with a React Query hook, e.g. useItem(id)
  return <Stack.Screen options={{ title: `#${id}` }} />;
}
```

#### Navigating

```tsx
import { Link, router } from 'expo-router';

<Link href={{ pathname: '/items/[id]', params: { id: item.id } }}>Open</Link>;

router.push({ pathname: '/items/[id]', params: { id } });
router.replace('/login');
router.back();
```

### 4. Typed Routes

Enable typed routes once in `app.json` so `href`/`router.push` are type-checked:

```json
{ "expo": { "experiments": { "typedRoutes": true } } }
```

Expo generates the route types into `.expo/types` when the dev server starts
(`npx expo start`); make sure `tsconfig.json` includes `".expo/types/**/*.ts"` and
`"expo-env.d.ts"`.

### 5. Verify

```bash
npx tsc --noEmit
```

## Rules

- Navigators are `_layout.tsx` files: `Stack` / `Tabs` from `expo-router`, `Drawer`
  from `expo-router/drawer`. No `NavigationContainer`, no `createXNavigator()`.
- Every file in `src/app/` is a route; put components, hooks and tests elsewhere.
- Read params with `useLocalSearchParams<...>()` (or `useGlobalSearchParams` when a
  layout must react to child params); never pass data through navigation props.
- Pass ids in params, not objects — load the record from React Query in the screen.
- Use `<Link>` for declarative navigation and `router` for imperative navigation;
  keep typed routes on so a broken `href` fails `tsc`.
- Auth gating: use `Stack.Protected guard={...}` (or a `<Redirect>` in a group's
  `_layout.tsx`) rather than conditionally rendering navigators.
- Screen titles come from `t('...')`, never hardcoded strings.

## Generated Files

```
src/app/_layout.tsx                 (only if missing)
src/app/(tabs)/_layout.tsx          (tabs)
src/app/(tabs)/<screen>.tsx
src/app/<name>/_layout.tsx          (stack)
src/app/<name>/index.tsx
src/app/<name>/[id].tsx
src/app/(drawer)/_layout.tsx        (drawer)
```

See `references/navigation-examples.md` for full tabs, stack, drawer, modal,
auth-gated and deep-link examples.
