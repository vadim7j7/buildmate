# React Native Common Pitfalls & Anti-Patterns

Common mistakes and performance issues in React Native + Expo applications. All
agents must recognize and avoid these patterns.

---

## 1. Performance Anti-Patterns

### Inline Styles

```typescript
// WRONG - creates new object every render
function ListItem({ item }: { item: Item }) {
  return (
    <View style={{ padding: 16, backgroundColor: '#fff' }}>
      <Text style={{ fontSize: 16, color: '#333' }}>{item.name}</Text>
    </View>
  );
}

// CORRECT - StyleSheet.create (object identity stable)
function ListItem({ item }: { item: Item }) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>{item.name}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, backgroundColor: '#fff' },
  title: { fontSize: 16, color: '#333' },
});
```

### Anonymous Functions in Lists

```typescript
// WRONG - new function every render
<FlashList
  data={items}
  renderItem={({ item }) => (
    <Pressable onPress={() => handlePress(item.id)}>
      <Text>{item.name}</Text>
    </Pressable>
  )}
/>

// CORRECT - memoized component with stable handler
const ItemRow = memo(function ItemRow({
  item,
  onPress,
}: {
  item: Item;
  onPress: (id: string) => void;
}) {
  const handlePress = useCallback(() => onPress(item.id), [item.id, onPress]);

  return (
    <Pressable onPress={handlePress}>
      <Text>{item.name}</Text>
    </Pressable>
  );
});

function List() {
  const handlePress = useCallback((id: string) => {
    router.push(`/items/${id}`);
  }, []);

  return (
    <FlashList
      data={items}
      renderItem={({ item }) => <ItemRow item={item} onPress={handlePress} />}
      estimatedItemSize={50}
    />
  );
}
```

### Missing estimatedItemSize

```typescript
// WRONG - FlashList without estimatedItemSize
<FlashList data={items} renderItem={renderItem} />

// Warning: FlashList will use a default estimatedItemSize which may hurt performance

// CORRECT - always provide estimatedItemSize
<FlashList
  data={items}
  renderItem={renderItem}
  estimatedItemSize={72}  // Average height of your items
/>
```

---

## 2. FlatList vs FlashList

```typescript
// WRONG - FlatList for long lists (100+ items)
<FlatList
  data={transactions}  // 500 items
  renderItem={renderItem}
  keyExtractor={(item) => item.id}
/>

// CORRECT - FlashList for any list with more than ~20 items
import { FlashList } from '@shopify/flash-list';

<FlashList
  data={transactions}
  renderItem={renderItem}
  estimatedItemSize={72}
  keyExtractor={(item) => item.id}
/>

// FlatList is OK for:
// - Very short lists (< 20 items)
// - Lists where items change size dynamically
// - When you need specific FlatList features not in FlashList
```

---

## 3. Image Performance

### Using react-native Image

```typescript
// WRONG - react-native Image (slow, no caching)
import { Image } from 'react-native';

<Image source={{ uri: user.avatarUrl }} style={styles.avatar} />

// CORRECT - expo-image (caching, transitions, blurhash)
import { Image } from 'expo-image';

<Image
  source={{ uri: user.avatarUrl }}
  style={styles.avatar}
  contentFit="cover"
  transition={200}
  placeholder={blurhash}
/>
```

### Loading Large Images

```typescript
// WRONG - loading full-size images in lists
<Image source={{ uri: `${CDN}/images/${id}/original.jpg` }} />

// CORRECT - load appropriately sized images
const imageSize = PixelRatio.getPixelSizeForLayoutSize(100);
<Image source={{ uri: `${CDN}/images/${id}/thumb_${imageSize}.jpg` }} />

// Or use responsive image loading
function getOptimizedImageUrl(id: string, size: number) {
  const pixelSize = PixelRatio.getPixelSizeForLayoutSize(size);
  return `${CDN}/images/${id}?w=${pixelSize}&q=80`;
}
```

---

## 4. Memory Leaks

### Not Cleaning Up Subscriptions

```typescript
// WRONG - memory leak from event listener
useEffect(() => {
  const subscription = Dimensions.addEventListener('change', handleChange);
  // No cleanup!
}, []);

// CORRECT - cleanup on unmount
useEffect(() => {
  const subscription = Dimensions.addEventListener('change', handleChange);
  return () => subscription.remove();
}, []);

// WRONG - async operation after unmount
useEffect(() => {
  fetchData().then((data) => {
    setData(data);  // Component might be unmounted!
  });
}, []);

// CORRECT - check mounted state or use AbortController
useEffect(() => {
  let isMounted = true;

  fetchData().then((data) => {
    if (isMounted) {
      setData(data);
    }
  });

  return () => {
    isMounted = false;
  };
}, []);

// BETTER - use AbortController
useEffect(() => {
  const controller = new AbortController();

  fetch(url, { signal: controller.signal })
    .then((res) => res.json())
    .then(setData)
    .catch((err) => {
      if (err.name !== 'AbortError') {
        setError(err);
      }
    });

  return () => controller.abort();
}, [url]);
```

### Timer Cleanup

```typescript
// WRONG - timer not cleaned up
useEffect(() => {
  setInterval(() => {
    updateTime();
  }, 1000);
}, []);

// CORRECT - cleanup timer
useEffect(() => {
  const timer = setInterval(() => {
    updateTime();
  }, 1000);

  return () => clearInterval(timer);
}, []);
```

---

## 5. Bundle Size Issues

### Importing Entire Libraries

```typescript
// WRONG - imports entire library
import _ from 'lodash';
const sorted = _.sortBy(items, 'name');

// CORRECT - import only what you need
import sortBy from 'lodash/sortBy';
const sorted = sortBy(items, 'name');

// WRONG - importing all icons
import { Ionicons } from '@expo/vector-icons';

// Icons are tree-shaken, but be mindful of using multiple icon sets
```

### Large Dependencies

```typescript
// Avoid large dependencies when lighter alternatives exist

// WRONG - moment.js (~300KB)
import moment from 'moment';

// CORRECT - date-fns (~10KB for used functions)
import { format, parseISO } from 'date-fns';

// WRONG - lodash (if using few functions)
import _ from 'lodash';

// CORRECT - native JS or lodash-es with tree-shaking
const sorted = items.toSorted((a, b) => a.name.localeCompare(b.name));
```

---

## 6. Navigation Pitfalls

### Not Handling Back Navigation

```typescript
// WRONG - no back handler for custom back behavior
function FormScreen() {
  const [hasChanges, setHasChanges] = useState(false);

  // User can navigate back without warning, losing changes!
}

// CORRECT - handle back navigation
import { usePreventRemove } from '@react-navigation/native';

function FormScreen() {
  const [hasChanges, setHasChanges] = useState(false);

  usePreventRemove(hasChanges, ({ data }) => {
    Alert.alert(
      'Discard changes?',
      'You have unsaved changes. Are you sure you want to discard them?',
      [
        { text: "Don't leave", style: 'cancel' },
        {
          text: 'Discard',
          style: 'destructive',
          onPress: () => data.action.type && router.dispatch(data.action),
        },
      ]
    );
  });
}
```

### Stale Route Params

```typescript
// WRONG - stale closure over route params
function DetailScreen() {
  const { id } = useLocalSearchParams();

  const handleRefresh = useCallback(() => {
    fetchData(id);  // id might be stale if screen is reused
  }, []);  // Missing dependency!

  return <Button onPress={handleRefresh} title="Refresh" />;
}

// CORRECT - include params in dependencies
function DetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();

  const handleRefresh = useCallback(() => {
    if (id) fetchData(id);
  }, [id]);

  return <Button onPress={handleRefresh} title="Refresh" />;
}
```

---

## 7. Platform-Specific Issues

### Ignoring Platform Differences

```typescript
// WRONG - same UI for both platforms
function AddButton({ onPress }: { onPress: () => void }) {
  return (
    <Button title="Add" onPress={onPress} />  // Not platform-appropriate
  );
}

// CORRECT - platform-specific patterns
import { Platform } from 'react-native';

function AddButton({ onPress }: { onPress: () => void }) {
  if (Platform.OS === 'ios') {
    // iOS: Header button or action sheet
    return null;  // Use headerRight in Stack.Screen
  }

  // Android: FAB
  return <FloatingActionButton onPress={onPress} icon="plus" />;
}
```

### Shadow Differences

```typescript
// WRONG - iOS shadows don't work on Android
const styles = StyleSheet.create({
  card: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    // Works on iOS, invisible on Android!
  },
});

// CORRECT - platform-specific shadows
const styles = StyleSheet.create({
  card: {
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
      },
      android: {
        elevation: 3,
      },
    }),
    backgroundColor: '#fff',  // Required for shadows
  },
});

// OR use a shadows constant
import { shadows } from '@/constants';
const styles = StyleSheet.create({
  card: {
    ...shadows.sm,  // Handles both platforms
    backgroundColor: colors.surface,
  },
});
```

---

## 8. Keyboard Issues

### Keyboard Covering Inputs

```typescript
// WRONG - inputs hidden by keyboard
<View style={styles.container}>
  <TextInput placeholder="Email" />
  <TextInput placeholder="Password" />
  <Button title="Submit" />
</View>

// CORRECT - KeyboardAvoidingView with platform behavior
<KeyboardAvoidingView
  style={styles.container}
  behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
>
  <ScrollView keyboardShouldPersistTaps="handled">
    <TextInput placeholder="Email" />
    <TextInput placeholder="Password" />
    <Button title="Submit" />
  </ScrollView>
</KeyboardAvoidingView>
```

### Keyboard Dismissing Unexpectedly

```typescript
// WRONG - keyboard dismisses when tapping between inputs
<ScrollView>
  <TextInput />
  <TextInput />
</ScrollView>

// Tapping between inputs dismisses keyboard

// CORRECT - persist taps
<ScrollView keyboardShouldPersistTaps="handled">
  <TextInput />
  <TextInput />
</ScrollView>

// Or use 'always' to keep keyboard open on any tap
```

---

## 9. Safe Area Issues

### Ignoring Safe Areas

```typescript
// WRONG - content under notch/Dynamic Island
<View style={{ flex: 1 }}>
  <Text>Title hidden under notch!</Text>
</View>

// CORRECT - use SafeAreaView
import { SafeAreaView } from 'react-native-safe-area-context';

<SafeAreaView style={{ flex: 1 }}>
  <Text>Title visible</Text>
</SafeAreaView>

// CORRECT - use useSafeAreaInsets for more control
import { useSafeAreaInsets } from 'react-native-safe-area-context';

function Screen() {
  const insets = useSafeAreaInsets();

  return (
    <View style={{ flex: 1, paddingTop: insets.top }}>
      <Text>Title with custom spacing</Text>
    </View>
  );
}
```

### Wrong SafeAreaView Import

```typescript
// WRONG - deprecated SafeAreaView from react-native
import { SafeAreaView } from 'react-native';

// CORRECT - use react-native-safe-area-context
import { SafeAreaView } from 'react-native-safe-area-context';
```

---

## 10. State Management Issues

### Storing Server Data in Zustand

```typescript
// WRONG - Zustand for server data
const useStore = create((set) => ({
  users: [],
  isLoading: false,
  fetchUsers: async () => {
    set({ isLoading: true });
    const users = await api.getUsers();
    set({ users, isLoading: false });
  },
}));

// CORRECT - React Query for server data, Zustand for UI state
// Server data
function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: api.getUsers,
  });
}

// UI state only in Zustand
const useUIStore = create((set) => ({
  filterVisible: false,
  selectedSort: 'name',
  toggleFilter: () => set((s) => ({ filterVisible: !s.filterVisible })),
}));
```

### Missing Reset in Zustand

```typescript
// WRONG - no reset method
const useStore = create((set) => ({
  filter: null,
  sort: 'asc',
  setFilter: (filter) => set({ filter }),
}));

// How do you reset on logout? On test cleanup?

// CORRECT - include reset method
const initialState = {
  filter: null,
  sort: 'asc',
};

const useStore = create((set) => ({
  ...initialState,
  setFilter: (filter) => set({ filter }),
  reset: () => set(initialState),
}));

// On logout
useStore.getState().reset();
```

---

## 11. Async Storage Pitfalls

### Blocking Renders with AsyncStorage

```typescript
// WRONG - blocking initial render
function App() {
  const [isReady, setIsReady] = useState(false);
  const [theme, setTheme] = useState('light');

  useEffect(() => {
    const loadTheme = async () => {
      const saved = await AsyncStorage.getItem('theme');  // Blocks!
      setTheme(saved ?? 'light');
      setIsReady(true);
    };
    loadTheme();
  }, []);

  if (!isReady) return <Splash />;
  return <App theme={theme} />;
}

// CORRECT - use expo-splash-screen
import * as SplashScreen from 'expo-splash-screen';

SplashScreen.preventAutoHideAsync();

function App() {
  const [theme, setTheme] = useState('light');

  useEffect(() => {
    const loadTheme = async () => {
      const saved = await AsyncStorage.getItem('theme');
      setTheme(saved ?? 'light');
      await SplashScreen.hideAsync();
    };
    loadTheme();
  }, []);

  return <App theme={theme} />;
}
```

### Not Handling AsyncStorage Errors

```typescript
// WRONG - no error handling
const theme = await AsyncStorage.getItem('theme');

// CORRECT - handle potential failures
async function loadTheme(): Promise<string> {
  try {
    const theme = await AsyncStorage.getItem('theme');
    return theme ?? 'light';
  } catch (error) {
    console.warn('Failed to load theme:', error);
    return 'light';  // Fallback
  }
}
```

---

## 12. i18n Issues

### Hardcoded Strings

```typescript
// WRONG - hardcoded strings
<Button title="Save" />
<Text>No items found</Text>
<Alert.alert('Error', 'Something went wrong');

// CORRECT - use i18n
import { useTranslation } from 'react-i18next';

const { t } = useTranslation();

<Button title={t('common.save')} />
<Text>{t('items.empty')}</Text>
Alert.alert(t('common.error'), t('errors.generic'));
```

### String Concatenation

```typescript
// WRONG - concatenating translated strings
<Text>{t('hello')} {userName}!</Text>

// CORRECT - use interpolation
// en.json: { "greeting": "Hello, {{name}}!" }
<Text>{t('greeting', { name: userName })}</Text>

// WRONG - pluralization with concatenation
<Text>{items.length} {items.length === 1 ? t('item') : t('items')}</Text>

// CORRECT - use plural forms
// en.json: { "itemCount": "{{count}} item", "itemCount_plural": "{{count}} items" }
<Text>{t('itemCount', { count: items.length })}</Text>
```

---

## Quick Reference

| Problem | Solution |
|---------|----------|
| Inline styles | StyleSheet.create |
| Anonymous handlers | useCallback + memo |
| Slow lists | FlashList with estimatedItemSize |
| Poor image perf | expo-image with caching |
| Memory leaks | Cleanup effects, AbortController |
| Large bundle | Tree-shaking, lighter alternatives |
| Back navigation | usePreventRemove |
| Keyboard covers input | KeyboardAvoidingView |
| Notch overlap | SafeAreaView from safe-area-context |
| Server data in Zustand | Use React Query for server data |
| Hardcoded strings | Always use i18n |
