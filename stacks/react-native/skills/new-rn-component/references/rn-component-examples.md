# React Native Component Examples

## Card Component (UI Primitive)

A versatile card component with variants, shadow support, and theme constants.

```typescript
// components/ui/Card.tsx
import React from 'react';
import { View, StyleSheet, ViewStyle, Pressable } from 'react-native';
import { colors, spacing, borderRadius, shadows } from '@/constants';

export interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  variant?: 'default' | 'elevated' | 'outlined';
  onPress?: () => void;
  testID?: string;
}

export function Card({
  children,
  style,
  variant = 'default',
  onPress,
  testID,
}: CardProps) {
  const cardStyle = [styles.base, variantStyles[variant], style];

  if (onPress) {
    return (
      <Pressable
        style={({ pressed }) => [
          ...cardStyle,
          pressed && styles.pressed,
        ]}
        onPress={onPress}
        testID={testID}
      >
        {children}
      </Pressable>
    );
  }

  return (
    <View style={cardStyle} testID={testID}>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  base: {
    padding: spacing.md,
    borderRadius: borderRadius.md,
    backgroundColor: colors.surface,
  },
  pressed: {
    opacity: 0.85,
  },
});

const variantStyles = StyleSheet.create({
  default: {},
  elevated: {
    ...shadows.md,
  },
  outlined: {
    borderWidth: 1,
    borderColor: colors.border,
  },
});
```

---

## List Item Component (with React.memo)

A transaction card component designed for use in FlashList. Wrapped in
React.memo to prevent unnecessary re-renders.

```typescript
// components/lists/TransactionCard.tsx
import React from 'react';
import { View, Text, Pressable, StyleSheet, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, typography, borderRadius, shadows } from '@/constants';
import type { Transaction } from '@/db/schema';

export interface TransactionCardProps {
  transaction: Transaction;
  onPress?: (id: string) => void;
  testID?: string;
}

function formatCurrency(amount: number): string {
  const formatted = Math.abs(amount).toFixed(2);
  return amount < 0 ? `-$${formatted}` : `$${formatted}`;
}

const CATEGORY_ICONS: Record<string, string> = {
  food: 'restaurant-outline',
  transport: 'car-outline',
  housing: 'home-outline',
  entertainment: 'game-controller-outline',
  shopping: 'bag-outline',
  other: 'ellipsis-horizontal-outline',
};

export const TransactionCard = React.memo(function TransactionCard({
  transaction,
  onPress,
  testID,
}: TransactionCardProps) {
  const isExpense = transaction.amount < 0;
  const iconName = CATEGORY_ICONS[transaction.category ?? 'other'] ?? 'ellipsis-horizontal-outline';

  return (
    <Pressable
      style={({ pressed }) => [
        styles.container,
        pressed && styles.pressed,
      ]}
      onPress={() => onPress?.(transaction.id)}
      android_ripple={{ color: 'rgba(0,0,0,0.08)', borderless: false }}
      testID={testID}
    >
      <View style={styles.iconContainer}>
        <Ionicons
          name={iconName as any}
          size={20}
          color={colors.primary}
        />
      </View>

      <View style={styles.details}>
        <Text style={styles.description} numberOfLines={1}>
          {transaction.description}
        </Text>
        {transaction.category && (
          <Text style={styles.category} testID="category-badge">
            {transaction.category}
          </Text>
        )}
      </View>

      <Text style={[styles.amount, isExpense ? styles.expense : styles.income]}>
        {formatCurrency(transaction.amount)}
      </Text>
    </Pressable>
  );
});

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    marginHorizontal: spacing.md,
    ...shadows.sm,
  },
  pressed: {
    opacity: Platform.OS === 'ios' ? 0.7 : 1,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.sm,
  },
  details: {
    flex: 1,
    marginRight: spacing.sm,
  },
  description: {
    ...typography.body,
    color: colors.text,
    marginBottom: 2,
  },
  category: {
    ...typography.caption,
    color: colors.textSecondary,
    textTransform: 'capitalize',
  },
  amount: {
    ...typography.body,
    fontWeight: '600',
  },
  expense: {
    color: colors.error,
  },
  income: {
    color: colors.success,
  },
});
```

---

## Form Input Component

A styled text input with label, error message, and proper accessibility.

```typescript
// components/ui/TextInput.tsx
import React from 'react';
import {
  View,
  Text,
  TextInput as RNTextInput,
  TextInputProps as RNTextInputProps,
  StyleSheet,
} from 'react-native';
import { colors, spacing, typography, borderRadius } from '@/constants';

export interface TextInputProps extends Omit<RNTextInputProps, 'style'> {
  label: string;
  error?: string;
  testID?: string;
}

export function TextInput({
  label,
  error,
  testID,
  ...inputProps
}: TextInputProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.label}>{label}</Text>
      <RNTextInput
        style={[styles.input, error && styles.inputError]}
        placeholderTextColor={colors.textTertiary}
        testID={testID}
        accessibilityLabel={label}
        {...inputProps}
      />
      {error && <Text style={styles.error}>{error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.xs,
  },
  label: {
    ...typography.caption,
    color: colors.text,
    fontWeight: '500',
  },
  input: {
    ...typography.body,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.md,
    padding: spacing.sm,
    color: colors.text,
    backgroundColor: colors.surface,
    minHeight: 44, // Minimum touch target
  },
  inputError: {
    borderColor: colors.error,
  },
  error: {
    ...typography.caption,
    color: colors.error,
  },
});
```

---

## Badge / Chip Component

A small badge component for labels and categories.

```typescript
// components/ui/Badge.tsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, spacing, typography, borderRadius } from '@/constants';

export interface BadgeProps {
  label: string;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md';
  testID?: string;
}

const VARIANT_COLORS: Record<
  NonNullable<BadgeProps['variant']>,
  { bg: string; text: string }
> = {
  default: { bg: colors.surfaceSecondary, text: colors.text },
  success: { bg: colors.successLight, text: colors.success },
  warning: { bg: colors.warningLight, text: colors.warning },
  error: { bg: colors.errorLight, text: colors.error },
  info: { bg: colors.primaryLight, text: colors.primary },
};

export function Badge({
  label,
  variant = 'default',
  size = 'sm',
  testID,
}: BadgeProps) {
  const variantColor = VARIANT_COLORS[variant];

  return (
    <View
      style={[
        styles.base,
        size === 'md' && styles.sizeMd,
        { backgroundColor: variantColor.bg },
      ]}
      testID={testID}
    >
      <Text
        style={[
          styles.label,
          size === 'md' && styles.labelMd,
          { color: variantColor.text },
        ]}
      >
        {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  base: {
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: borderRadius.full,
    alignSelf: 'flex-start',
  },
  sizeMd: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
  label: {
    ...typography.caption,
    fontWeight: '500',
    fontSize: 11,
  },
  labelMd: {
    fontSize: 13,
  },
});
```

---

## Section Component (Layout)

A reusable section wrapper with title and optional action.

```typescript
// components/ui/Section.tsx
import React from 'react';
import { View, Text, Pressable, StyleSheet } from 'react-native';
import { colors, spacing, typography, borderRadius, shadows } from '@/constants';

export interface SectionProps {
  title: string;
  children: React.ReactNode;
  action?: {
    label: string;
    onPress: () => void;
  };
  testID?: string;
}

export function Section({ title, children, action, testID }: SectionProps) {
  return (
    <View style={styles.container} testID={testID}>
      <View style={styles.header}>
        <Text style={styles.title}>{title}</Text>
        {action && (
          <Pressable onPress={action.onPress}>
            <Text style={styles.actionLabel}>{action.label}</Text>
          </Pressable>
        )}
      </View>
      <View style={styles.content}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    ...shadows.sm,
    overflow: 'hidden',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingTop: spacing.md,
    paddingBottom: spacing.sm,
  },
  title: {
    ...typography.heading3,
    color: colors.text,
  },
  actionLabel: {
    ...typography.body,
    color: colors.primary,
    fontWeight: '500',
  },
  content: {
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.md,
  },
});
```

---

## Platform-Specific Component

A floating action button that only renders on Android, following Material
Design patterns.

```typescript
// components/ui/FloatingActionButton.tsx
import React from 'react';
import { Pressable, StyleSheet, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, shadows } from '@/constants';

export interface FloatingActionButtonProps {
  icon: keyof typeof Ionicons.glyphMap;
  onPress: () => void;
  testID?: string;
}

export function FloatingActionButton({
  icon,
  onPress,
  testID,
}: FloatingActionButtonProps) {
  // FAB is an Android pattern; on iOS use header buttons
  if (Platform.OS === 'ios') return null;

  return (
    <Pressable
      style={({ pressed }) => [
        styles.container,
        pressed && styles.pressed,
      ]}
      onPress={onPress}
      android_ripple={{ color: 'rgba(255,255,255,0.3)', borderless: true }}
      testID={testID}
    >
      <Ionicons name={icon} size={24} color={colors.onPrimary} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: spacing.lg,
    right: spacing.lg,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    ...shadows.lg,
  },
  pressed: {
    opacity: 0.9,
  },
});
```
