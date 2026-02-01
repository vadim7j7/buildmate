# Platform-Specific Patterns for React Native

## iOS vs Android UI Differences

### Navigation Patterns

| Pattern | iOS | Android |
|---------|-----|---------|
| Add action | Header bar button (top-right) | Floating Action Button (FAB) |
| Back navigation | Swipe from left edge + header back button | System back button + header back arrow |
| Modal dismiss | Swipe down + header close button | System back button + header close button |
| Tab bar | Bottom tab bar (native feel) | Bottom navigation or top tabs |
| Search | Pull-down search bar in navigation | Search icon in header with expanding input |
| Action sheets | Native iOS action sheet | Bottom sheet or material menu |

### Platform.OS Checks

Use `Platform.OS` for conditional rendering of platform-specific UI elements.

```typescript
import { Platform, View } from 'react-native';
import { Stack, Link, router } from 'expo-router';
import { FloatingActionButton } from '@/components/ui/FloatingActionButton';

export default function ItemsScreen() {
  return (
    <View style={styles.container}>
      <Stack.Screen
        options={{
          title: t('items.title'),
          // iOS: Header button for primary action
          ...(Platform.OS === 'ios' && {
            headerRight: () => (
              <Link href="/(modals)/item-form">
                <Text style={styles.headerAction}>{t('common.add')}</Text>
              </Link>
            ),
          }),
        }}
      />

      <FlashList data={items} renderItem={renderItem} estimatedItemSize={72} />

      {/* Android: FAB for primary action */}
      {Platform.OS === 'android' && (
        <FloatingActionButton
          icon="plus"
          onPress={() => router.push('/(modals)/item-form')}
        />
      )}
    </View>
  );
}
```

### Platform.select

Use `Platform.select` for platform-specific values.

```typescript
import { Platform, StyleSheet } from 'react-native';
import { spacing } from '@/constants';

const styles = StyleSheet.create({
  container: {
    paddingTop: Platform.select({
      ios: spacing.sm,
      android: spacing.md,
    }),
  },
  header: {
    fontWeight: Platform.select({
      ios: '600',
      android: '700',
    }),
  },
});
```

---

## SafeAreaView Usage

### Always Use Safe Area Handling

Devices with notches (iPhone), Dynamic Island, and Android system bars require
safe area insets.

```typescript
// Option 1: SafeAreaView from react-native-safe-area-context
import { SafeAreaView } from 'react-native-safe-area-context';

export default function SettingsScreen() {
  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView>{/* content */}</ScrollView>
    </SafeAreaView>
  );
}

// Option 2: useSafeAreaInsets for fine-grained control
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export default function CustomScreen() {
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.container, { paddingBottom: insets.bottom }]}>
      {/* content */}
    </View>
  );
}
```

### When to Use Which Edges

```typescript
// Screens with tab bar: no bottom safe area needed (tab bar handles it)
<SafeAreaView edges={['top']}>

// Full-screen modals: need all edges
<SafeAreaView edges={['top', 'bottom', 'left', 'right']}>

// Screens with navigation header: no top safe area needed (header handles it)
<SafeAreaView edges={['bottom']}>

// Screens with both header and tab bar: no safe area needed
// (both are handled by the navigation container)
```

---

## Shadows

Shadows work differently on iOS and Android. Always use platform-specific shadow
constants.

```typescript
// constants/shadows.ts
import { Platform, StyleSheet } from 'react-native';

export const shadows = StyleSheet.create({
  sm: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.1,
      shadowRadius: 2,
    },
    android: {
      elevation: 2,
    },
  })!,
  md: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.15,
      shadowRadius: 4,
    },
    android: {
      elevation: 4,
    },
  })!,
  lg: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.2,
      shadowRadius: 8,
    },
    android: {
      elevation: 8,
    },
  })!,
  xl: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 8 },
      shadowOpacity: 0.25,
      shadowRadius: 16,
    },
    android: {
      elevation: 16,
    },
  })!,
});
```

---

## KeyboardAvoidingView

Keyboard avoidance behaves differently on iOS and Android.

```typescript
import { KeyboardAvoidingView, Platform } from 'react-native';

// CORRECT: Platform-specific behavior
<KeyboardAvoidingView
  style={styles.container}
  behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
  keyboardVerticalOffset={Platform.OS === 'ios' ? 88 : 0}
>
  <ScrollView keyboardShouldPersistTaps="handled">
    {/* form fields */}
  </ScrollView>
</KeyboardAvoidingView>

// Note: On iOS, 'padding' adds padding to push content up.
// On Android, 'height' resizes the view. The offset accounts for
// the navigation header height on iOS.
```

### keyboardVerticalOffset

The offset depends on what is above the KeyboardAvoidingView:
- **No header**: 0 for both platforms
- **With navigation header**: ~88 on iOS (header + status bar), 0 on Android
- **With header + tab bar**: Adjust accordingly

---

## Haptic Feedback

iOS and Android have different haptic feedback capabilities.

```typescript
import * as Haptics from 'expo-haptics';
import { Platform } from 'react-native';

async function triggerHaptic(type: 'light' | 'medium' | 'heavy' | 'success' | 'error') {
  // Haptics are more nuanced on iOS; Android has basic vibration
  switch (type) {
    case 'light':
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      break;
    case 'medium':
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      break;
    case 'heavy':
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
      break;
    case 'success':
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      break;
    case 'error':
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      break;
  }
}
```

---

## Status Bar

Configure the status bar per-screen for proper appearance.

```typescript
import { StatusBar } from 'expo-status-bar';

// Light content (white text) for dark backgrounds
<StatusBar style="light" />

// Dark content (black text) for light backgrounds
<StatusBar style="dark" />

// Auto-detect based on theme
<StatusBar style="auto" />
```

---

## Pressable vs TouchableOpacity

Prefer `Pressable` over `TouchableOpacity` for more control and better Android
ripple support.

```typescript
import { Pressable, Platform, StyleSheet } from 'react-native';

<Pressable
  style={({ pressed }) => [
    styles.button,
    pressed && styles.buttonPressed,
  ]}
  android_ripple={{
    color: 'rgba(0, 0, 0, 0.1)',
    borderless: false,
  }}
  onPress={handlePress}
>
  <Text style={styles.buttonText}>{label}</Text>
</Pressable>

const styles = StyleSheet.create({
  button: {
    padding: spacing.md,
    borderRadius: borderRadius.md,
    backgroundColor: colors.primary,
  },
  buttonPressed: {
    // iOS only - android_ripple handles Android
    opacity: Platform.OS === 'ios' ? 0.7 : 1,
  },
  buttonText: {
    color: colors.onPrimary,
    textAlign: 'center',
    fontWeight: '600',
  },
});
```

---

## Platform-Specific File Extensions

For components with significant platform differences, use platform-specific
file extensions:

```
components/
  DatePicker.ios.tsx    # iOS-specific implementation
  DatePicker.android.tsx # Android-specific implementation
  DatePicker.tsx        # Shared types/interface (re-export)
```

React Native automatically resolves `.ios.tsx` or `.android.tsx` based on the
target platform. Use this pattern sparingly -- only when the implementations
are fundamentally different.

---

## Android Back Handler

Handle the Android hardware back button for custom navigation flows.

```typescript
import { useCallback } from 'react';
import { BackHandler, Platform } from 'react-native';
import { useFocusEffect } from 'expo-router';

function useAndroidBackHandler(handler: () => boolean) {
  useFocusEffect(
    useCallback(() => {
      if (Platform.OS !== 'android') return;

      const subscription = BackHandler.addEventListener(
        'hardwareBackPress',
        handler
      );

      return () => subscription.remove();
    }, [handler])
  );
}

// Usage in a screen with unsaved changes
function FormScreen() {
  const hasUnsavedChanges = useFormStore((s) => s.isDirty);

  useAndroidBackHandler(() => {
    if (hasUnsavedChanges) {
      Alert.alert(
        t('common.unsavedChanges'),
        t('common.unsavedChangesMessage'),
        [
          { text: t('common.cancel'), style: 'cancel' },
          { text: t('common.discard'), onPress: () => router.back() },
        ]
      );
      return true; // Prevent default back action
    }
    return false; // Allow default back action
  });
}
```

---

## Testing Platform-Specific Code

When testing platform-specific behaviour, mock `Platform.OS`:

```typescript
import { Platform } from 'react-native';

describe('ItemsScreen', () => {
  const originalOS = Platform.OS;

  afterEach(() => {
    Platform.OS = originalOS;
  });

  it('renders FAB on Android', () => {
    Platform.OS = 'android';
    render(<ItemsScreen />);
    expect(screen.getByTestId('fab-button')).toBeTruthy();
  });

  it('renders header button on iOS', () => {
    Platform.OS = 'ios';
    render(<ItemsScreen />);
    expect(screen.queryByTestId('fab-button')).toBeNull();
  });
});
```
