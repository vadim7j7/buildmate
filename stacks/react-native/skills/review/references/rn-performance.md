# React Native Performance Checklist

## List Rendering

### FlashList (Required for Long Lists)

Use `@shopify/flash-list` for any list that may contain more than ~20 items.
FlashList recycles views and is significantly more performant than FlatList for
large datasets.

```typescript
import { FlashList } from '@shopify/flash-list';

// CORRECT
<FlashList
  data={items}
  renderItem={({ item }) => <ItemCard item={item} />}
  estimatedItemSize={72}     // REQUIRED - measure your average item height
  keyExtractor={(item) => item.id}
/>

// WRONG - ScrollView + map for dynamic lists
<ScrollView>
  {items.map((item) => (
    <ItemCard key={item.id} item={item} />
  ))}
</ScrollView>

// WRONG - FlatList for potentially large lists
<FlatList
  data={items}
  renderItem={({ item }) => <ItemCard item={item} />}
/>
```

### estimatedItemSize

Always provide `estimatedItemSize`. Measure the average rendered height of your
list items and use that value. A wrong estimate still performs better than no
estimate, but an accurate one is best.

```typescript
// Measure once, set accurately
<FlashList estimatedItemSize={72} />  // Typical card item
<FlashList estimatedItemSize={48} />  // Simple single-line item
<FlashList estimatedItemSize={120} /> // Complex multi-line card
```

### Extract renderItem Components

Never use anonymous functions for `renderItem`. Extract a named component and
wrap it with `React.memo`.

```typescript
// CORRECT
const MemoizedItemCard = React.memo(ItemCard);

<FlashList
  data={items}
  renderItem={({ item }) => <MemoizedItemCard item={item} />}
  estimatedItemSize={72}
/>

// EVEN BETTER - Named renderItem function
const renderItem = useCallback(
  ({ item }: { item: Item }) => <MemoizedItemCard item={item} />,
  []
);

<FlashList
  data={items}
  renderItem={renderItem}
  estimatedItemSize={72}
/>

// WRONG - Anonymous function defined inline
<FlashList
  data={items}
  renderItem={({ item }) => (
    <View style={styles.card}>
      <Text>{item.name}</Text>
      <Text>{item.description}</Text>
    </View>
  )}
/>
```

---

## Memoisation

### React.memo for List Items

All components rendered inside list `renderItem` MUST be wrapped in `React.memo`.

```typescript
interface ItemCardProps {
  item: Item;
  onPress?: (id: string) => void;
}

export const ItemCard = React.memo(function ItemCard({
  item,
  onPress,
}: ItemCardProps) {
  return (
    <Pressable onPress={() => onPress?.(item.id)}>
      <Text>{item.name}</Text>
    </Pressable>
  );
});
```

### useCallback for Event Handlers

Event handlers passed as props to child components or list items must use
`useCallback` to prevent unnecessary re-renders.

```typescript
// CORRECT
const handlePress = useCallback((id: string) => {
  router.push(`/items/${id}`);
}, []);

// WRONG - Creates a new function on every render
const handlePress = (id: string) => {
  router.push(`/items/${id}`);
};
```

### useMemo for Expensive Computations

Use `useMemo` for filtering, sorting, or transforming large datasets in render.

```typescript
// CORRECT
const filteredItems = useMemo(() => {
  if (!filterCategory) return items;
  return items.filter((item) => item.category === filterCategory);
}, [items, filterCategory]);

// WRONG - Filters on every render
const filteredItems = items.filter(
  (item) => item.category === filterCategory
);
```

---

## Image Optimisation

### Use expo-image

Use `expo-image` instead of React Native's built-in `Image` component. It
provides caching, placeholder support, and better performance.

```typescript
import { Image } from 'expo-image';

// CORRECT
<Image
  source={{ uri: imageUrl }}
  style={styles.avatar}
  placeholder={blurhash}
  contentFit="cover"
  transition={200}
  cachePolicy="memory-disk"
/>

// WRONG - Built-in Image with no caching strategy
import { Image } from 'react-native';
<Image source={{ uri: imageUrl }} style={styles.avatar} />
```

### Image Sizing

Always specify explicit width and height for images. Avoid relying on aspect
ratio alone, which causes layout thrashing.

```typescript
const styles = StyleSheet.create({
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
  },
  thumbnail: {
    width: 120,
    height: 80,
    borderRadius: borderRadius.sm,
  },
});
```

---

## Avoiding Unnecessary Re-renders

### Fine-Grained Zustand Selectors

Subscribe to specific state slices, not the entire store.

```typescript
// CORRECT - Only re-renders when filterCategory changes
const filterCategory = useTransactionStore((s) => s.filterCategory);

// WRONG - Re-renders on ANY store change
const { filterCategory } = useTransactionStore();
```

### Stable References

Ensure objects and arrays passed as props have stable references.

```typescript
// CORRECT - Stable empty array reference
const EMPTY_ARRAY: Item[] = [];
const items = data ?? EMPTY_ARRAY;

// WRONG - New array reference on every render
const items = data ?? [];
```

### Split Components

Split large components into smaller ones so that state changes only re-render
the relevant portion.

```typescript
// CORRECT - Filter bar re-renders independently of the list
function ItemsScreen() {
  return (
    <View>
      <FilterBar />  {/* Has its own store subscription */}
      <ItemList />   {/* Has its own query subscription */}
    </View>
  );
}

// WRONG - Entire screen re-renders when filter changes
function ItemsScreen() {
  const filter = useFilterStore((s) => s.filter);
  const { data } = useItems(filter);
  return (
    <View>
      <FilterBar filter={filter} />
      <FlashList data={data} ... />
    </View>
  );
}
```

---

## React Query Performance

### Appropriate staleTime

Set `staleTime` to avoid unnecessary background re-fetches.

```typescript
// Data that rarely changes (settings, categories)
useQuery({
  queryKey: queryKeys.categories.all,
  queryFn: getCategories,
  staleTime: 30 * 60 * 1000, // 30 minutes
});

// Data that changes moderately (transactions list)
useQuery({
  queryKey: queryKeys.transactions.all,
  queryFn: getTransactions,
  staleTime: 5 * 60 * 1000, // 5 minutes
});

// Data that should always be fresh (real-time balance)
useQuery({
  queryKey: queryKeys.balance.current,
  queryFn: getBalance,
  staleTime: 0, // Always re-fetch
});
```

### Avoid Waterfall Queries

Fetch independent data in parallel, not sequentially.

```typescript
// CORRECT - Parallel fetching
function DashboardScreen() {
  const balance = useBalance();       // Starts immediately
  const transactions = useTransactions(); // Starts immediately
  const categories = useCategories();     // Starts immediately
  // All three fetch in parallel
}

// WRONG - Sequential fetching
function DashboardScreen() {
  const { data: user } = useUser();
  const { data: balance } = useBalance(user?.id); // Waits for user
  const { data: transactions } = useTransactions(user?.id); // Also waits
}
```

---

## Bundle Size

### Import Only What You Need

Use named imports instead of default imports for tree-shaking.

```typescript
// CORRECT
import { format } from 'date-fns';

// WRONG - Imports entire library
import dateFns from 'date-fns';
```

### Lazy Load Heavy Screens

Use React.lazy for screens that include heavy dependencies.

```typescript
// For screens with heavy charts or maps
const ChartScreen = React.lazy(() => import('./ChartScreen'));
```

---

## Animation Performance

### Use Reanimated for Complex Animations

Use `react-native-reanimated` for complex animations. Run animations on the UI
thread, not the JS thread.

```typescript
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
} from 'react-native-reanimated';

const offset = useSharedValue(0);

const animatedStyle = useAnimatedStyle(() => ({
  transform: [{ translateX: offset.value }],
}));
```

### Avoid Layout Animations on Lists

Layout animations on FlashList items can cause performance issues. Use them
sparingly and test on low-end devices.
