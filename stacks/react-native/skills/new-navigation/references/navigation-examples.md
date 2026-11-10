# expo-router Navigation Examples

Reference examples for generating navigation with expo-router. Routes live in
`src/app/`; the `@/` alias maps to `src/`. Never use `NavigationContainer` or
`createXNavigator()` from React Navigation directly.

## File Tree

```
src/app/
  _layout.tsx               # root Stack (+ providers, migrations, fonts)
  +not-found.tsx            # unmatched routes
  (auth)/
    _layout.tsx             # Stack for sign-in flow
    login.tsx               # /login
  (tabs)/
    _layout.tsx             # Tabs
    index.tsx               # /
    search.tsx              # /search
    profile.tsx             # /profile
  items/
    _layout.tsx             # Stack inside the items section
    index.tsx               # /items
    [id].tsx                # /items/42
    [id]/edit.tsx           # /items/42/edit
  (modals)/
    new-item.tsx            # /new-item, presented as a modal by the root Stack
```

## Root Layout (providers + auth gate)

```tsx
// src/app/_layout.tsx
import { QueryClientProvider } from '@tanstack/react-query';
import { Stack } from 'expo-router';
import { queryClient } from '@/queries/queryClient';
import { useSession } from '@/hooks/useSession';
import '@/i18n';

export default function RootLayout() {
  const { isSignedIn } = useSession();

  return (
    <QueryClientProvider client={queryClient}>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Protected guard={isSignedIn}>
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="items" />
          <Stack.Screen
            name="(modals)/new-item"
            options={{ presentation: 'modal', headerShown: true }}
          />
        </Stack.Protected>
        <Stack.Protected guard={!isSignedIn}>
          <Stack.Screen name="(auth)" />
        </Stack.Protected>
      </Stack>
    </QueryClientProvider>
  );
}
```

`Stack.Protected` removes the guarded screens when `guard` is false and redirects
to the first available screen. On older expo-router versions, use a `<Redirect>`
inside the group's `_layout.tsx` instead:

```tsx
// src/app/(tabs)/_layout.tsx (redirect variant)
import { Redirect, Tabs } from 'expo-router';
import { useSession } from '@/hooks/useSession';

export default function TabsLayout() {
  const { isSignedIn } = useSession();
  if (!isSignedIn) return <Redirect href="/login" />;
  return <Tabs />;
}
```

## Tabs

```tsx
// src/app/(tabs)/_layout.tsx
import { Tabs } from 'expo-router';
import { Home, Search, User } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';
import { colors } from '@/constants';

export default function TabsLayout() {
  const { t } = useTranslation();

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textSecondary,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: t('tabs.home'),
          tabBarIcon: ({ color, size }) => <Home color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="search"
        options={{
          title: t('tabs.search'),
          tabBarIcon: ({ color, size }) => <Search color={color} size={size} />,
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

## Stack Section with a Dynamic Route

```tsx
// src/app/items/_layout.tsx
import { Stack } from 'expo-router';
import { useTranslation } from 'react-i18next';

export default function ItemsLayout() {
  const { t } = useTranslation();
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: t('items.title') }} />
      <Stack.Screen name="[id]" options={{ title: '' }} />
      <Stack.Screen name="[id]/edit" options={{ presentation: 'modal' }} />
    </Stack>
  );
}
```

```tsx
// src/app/items/[id].tsx
import { Stack, useLocalSearchParams, router } from 'expo-router';
import { Button, Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { useItem } from '@/queries/useItems';

export default function ItemDetailScreen() {
  const { t } = useTranslation();
  const { id } = useLocalSearchParams<{ id: string }>();
  const { data: item } = useItem(id);

  return (
    <View>
      {/* Set the title from data once it loads */}
      <Stack.Screen options={{ title: item?.title ?? '' }} />
      <Text>{item?.description}</Text>
      <Button
        title={t('common.edit')}
        onPress={() =>
          router.push({ pathname: '/items/[id]/edit', params: { id } })
        }
      />
    </View>
  );
}
```

## Drawer

```bash
npx expo install @react-navigation/drawer react-native-gesture-handler react-native-reanimated
```

```tsx
// src/app/(drawer)/_layout.tsx
import { Drawer } from 'expo-router/drawer';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { useTranslation } from 'react-i18next';

export default function DrawerLayout() {
  const { t } = useTranslation();
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <Drawer>
        <Drawer.Screen name="index" options={{ title: t('drawer.home') }} />
        <Drawer.Screen name="settings" options={{ title: t('drawer.settings') }} />
      </Drawer>
    </GestureHandlerRootView>
  );
}
```

Custom drawer content still uses the drawer's own components, passed through the
`drawerContent` prop:

```tsx
import { DrawerContentScrollView, DrawerItemList } from '@react-navigation/drawer';
import { Drawer } from 'expo-router/drawer';

<Drawer
  drawerContent={(props) => (
    <DrawerContentScrollView {...props}>
      <DrawerItemList {...props} />
    </DrawerContentScrollView>
  )}
/>;
```

## Navigating

```tsx
import { Link, router, useLocalSearchParams, useRouter } from 'expo-router';

// Declarative — typed when experiments.typedRoutes is on
<Link href="/profile">Profile</Link>;
<Link href={{ pathname: '/items/[id]', params: { id: item.id } }} asChild>
  <Pressable>{/* row */}</Pressable>
</Link>;

// Imperative
router.push('/search');
router.push({ pathname: '/items/[id]', params: { id } });
router.replace('/login');     // no back entry (e.g. after sign-out)
router.back();
router.dismissAll();          // close every modal on the stack

// Inside components that prefer a hook
const r = useRouter();

// Params (always strings; parse numbers yourself)
const { id, tab } = useLocalSearchParams<{ id: string; tab?: string }>();
```

## Typed Routes

```json
// app.json
{ "expo": { "experiments": { "typedRoutes": true } } }
```

```json
// tsconfig.json (paths + generated route types)
{
  "extends": "expo/tsconfig.base",
  "compilerOptions": { "strict": true, "paths": { "@/*": ["./src/*"] } },
  "include": ["**/*.ts", "**/*.tsx", ".expo/types/**/*.ts", "expo-env.d.ts"]
}
```

With typed routes on, `router.push('/itmes/1')` or a missing `params.id` fails
`npx tsc --noEmit`.

## Deep Linking

expo-router derives deep links from the file tree — no linking config. Set the
scheme in `app.json` and every route is reachable:

```json
{ "expo": { "scheme": "myapp" } }
```

`myapp://items/42` opens `src/app/items/[id].tsx` with `id = "42"`. Universal links
/ App Links use the same paths once `ios.associatedDomains` and
`android.intentFilters` are configured.

## Not Found

```tsx
// src/app/+not-found.tsx
import { Link, Stack } from 'expo-router';
import { Text, View } from 'react-native';
import { useTranslation } from 'react-i18next';

export default function NotFoundScreen() {
  const { t } = useTranslation();
  return (
    <View>
      <Stack.Screen options={{ title: t('notFound.title') }} />
      <Text>{t('notFound.message')}</Text>
      <Link href="/">{t('notFound.home')}</Link>
    </View>
  );
}
```

## Testing Navigation

```tsx
// src/__tests__/app/navigation.test.tsx
import { renderRouter, screen } from 'expo-router/testing-library';
import ItemDetailScreen from '@/app/items/[id]';

it('opens an item from a deep link', () => {
  renderRouter(
    { index: () => null, 'items/[id]': ItemDetailScreen },
    { initialUrl: '/items/42' }
  );
  expect(screen).toHavePathname('/items/42');
});
```
