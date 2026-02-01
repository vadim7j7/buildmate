# Expo Router Screen Examples

## List Screen Template

A list screen with FlashList, data loading, pull-to-refresh, empty state, and
platform-specific primary action.

```typescript
// app/(tabs)/budgets.tsx
import { useCallback } from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';
import { Stack, Link, router } from 'expo-router';
import { FlashList } from '@shopify/flash-list';
import { useTranslation } from 'react-i18next';
import { useBudgets } from '@/queries/useBudgets';
import { BudgetCard } from '@/components/lists/BudgetCard';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingScreen } from '@/components/ui/LoadingScreen';
import { ErrorScreen } from '@/components/ui/ErrorScreen';
import { FloatingActionButton } from '@/components/ui/FloatingActionButton';
import { colors, spacing } from '@/constants';
import type { Budget } from '@/db/schema';

export default function BudgetsScreen() {
  const { t } = useTranslation();
  const { data: budgets, isLoading, isError, error, refetch } = useBudgets();

  const handleBudgetPress = useCallback((id: string) => {
    router.push(`/budgets/${id}`);
  }, []);

  const renderItem = useCallback(
    ({ item }: { item: Budget }) => (
      <BudgetCard budget={item} onPress={() => handleBudgetPress(item.id)} />
    ),
    [handleBudgetPress]
  );

  if (isLoading) return <LoadingScreen />;
  if (isError) return <ErrorScreen message={error?.message ?? t('common.error')} onRetry={refetch} />;

  return (
    <View style={styles.container}>
      <Stack.Screen
        options={{
          title: t('budgets.title'),
          ...(Platform.OS === 'ios' && {
            headerRight: () => (
              <Link href="/(modals)/budget-form">
                <Text style={styles.headerAction}>{t('common.add')}</Text>
              </Link>
            ),
          }),
        }}
      />

      <FlashList
        data={budgets ?? []}
        renderItem={renderItem}
        estimatedItemSize={80}
        keyExtractor={(item) => item.id}
        onRefresh={refetch}
        refreshing={isLoading}
        ListEmptyComponent={
          <EmptyState
            message={t('budgets.empty')}
            actionLabel={t('budgets.createFirst')}
            onAction={() => router.push('/(modals)/budget-form')}
          />
        }
        contentContainerStyle={styles.listContent}
        ItemSeparatorComponent={() => <View style={styles.separator} />}
      />

      {Platform.OS === 'android' && (
        <FloatingActionButton
          icon="plus"
          onPress={() => router.push('/(modals)/budget-form')}
          testID="add-budget-fab"
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  listContent: {
    paddingVertical: spacing.sm,
  },
  separator: {
    height: spacing.xs,
  },
  headerAction: {
    color: colors.primary,
    fontSize: 16,
    fontWeight: '600',
  },
});
```

---

## Form Screen Template

A form screen with KeyboardAvoidingView, validation, header save button, and
mutation handling.

```typescript
// app/(modals)/budget-form.tsx
import { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Alert,
} from 'react-native';
import { Stack, router, useLocalSearchParams } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { useBudget, useCreateBudget, useUpdateBudget } from '@/queries/useBudgets';
import { TextInput } from '@/components/ui/TextInput';
import { SelectInput } from '@/components/ui/SelectInput';
import { CurrencyInput } from '@/components/ui/CurrencyInput';
import { colors, spacing, typography } from '@/constants';

const BUDGET_CATEGORIES = ['housing', 'food', 'transport', 'entertainment', 'savings', 'other'];

export default function BudgetFormScreen() {
  const { t } = useTranslation();
  const { id } = useLocalSearchParams<{ id?: string }>();
  const isEditing = !!id;

  // Load existing data when editing
  const { data: existingBudget } = useBudget(id ?? '');
  const createMutation = useCreateBudget();
  const updateMutation = useUpdateBudget();

  // Form state
  const [name, setName] = useState('');
  const [amount, setAmount] = useState(0);
  const [category, setCategory] = useState<string>('other');

  // Populate form when editing
  useEffect(() => {
    if (existingBudget) {
      setName(existingBudget.name);
      setAmount(existingBudget.amount);
      setCategory(existingBudget.category);
    }
  }, [existingBudget]);

  // Validation
  const errors: Record<string, string> = {};
  if (!name.trim()) errors.name = t('budgets.validation.nameRequired');
  if (amount <= 0) errors.amount = t('budgets.validation.amountPositive');
  const isValid = Object.keys(errors).length === 0;

  const isSaving = createMutation.isPending || updateMutation.isPending;

  const handleSave = async () => {
    if (!isValid || isSaving) return;

    try {
      if (isEditing && id) {
        await updateMutation.mutateAsync({ id, name, amount, category });
      } else {
        await createMutation.mutateAsync({ name, amount, category });
      }
      router.back();
    } catch {
      Alert.alert(t('common.error'), t('budgets.saveFailed'));
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 88 : 0}
    >
      <Stack.Screen
        options={{
          title: isEditing ? t('budgets.edit') : t('budgets.create'),
          presentation: 'modal',
          headerLeft: () => (
            <Pressable onPress={() => router.back()}>
              <Text style={styles.cancelButton}>{t('common.cancel')}</Text>
            </Pressable>
          ),
          headerRight: () => (
            <Pressable onPress={handleSave} disabled={!isValid || isSaving}>
              <Text
                style={[
                  styles.saveButton,
                  (!isValid || isSaving) && styles.saveButtonDisabled,
                ]}
              >
                {isSaving ? t('common.saving') : t('common.save')}
              </Text>
            </Pressable>
          ),
        }}
      />

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        <TextInput
          label={t('budgets.name')}
          value={name}
          onChangeText={setName}
          placeholder={t('budgets.namePlaceholder')}
          error={errors.name}
          autoFocus={!isEditing}
          testID="budget-name-input"
        />

        <CurrencyInput
          label={t('budgets.amount')}
          value={amount}
          onChangeValue={setAmount}
          error={errors.amount}
          testID="budget-amount-input"
        />

        <SelectInput
          label={t('budgets.category')}
          value={category}
          onValueChange={setCategory}
          options={BUDGET_CATEGORIES.map((cat) => ({
            label: t(`categories.${cat}`),
            value: cat,
          }))}
          testID="budget-category-select"
        />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollContent: {
    padding: spacing.md,
    gap: spacing.md,
  },
  cancelButton: {
    color: colors.textSecondary,
    fontSize: 16,
  },
  saveButton: {
    color: colors.primary,
    fontSize: 16,
    fontWeight: '600',
  },
  saveButtonDisabled: {
    opacity: 0.4,
  },
});
```

---

## Detail Screen Template

A detail screen with ScrollView, sections, data loading, and navigation
parameter handling.

```typescript
// app/(tabs)/budgets/[id].tsx
import { View, Text, ScrollView, StyleSheet, Alert } from 'react-native';
import { Stack, useLocalSearchParams, router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { useBudget, useDeleteBudget } from '@/queries/useBudgets';
import { Section } from '@/components/ui/Section';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { LoadingScreen } from '@/components/ui/LoadingScreen';
import { ErrorScreen } from '@/components/ui/ErrorScreen';
import { IconButton } from '@/components/ui/IconButton';
import { colors, spacing, typography } from '@/constants';

export default function BudgetDetailScreen() {
  const { t } = useTranslation();
  const { id } = useLocalSearchParams<{ id: string }>();
  const { data: budget, isLoading, error } = useBudget(id);
  const deleteMutation = useDeleteBudget();

  if (isLoading) return <LoadingScreen />;
  if (error || !budget) {
    return (
      <ErrorScreen
        message={t('budgets.notFound')}
        onRetry={() => router.back()}
      />
    );
  }

  const spentPercentage = budget.spent / budget.amount;
  const remaining = budget.amount - budget.spent;

  const handleEdit = () => {
    router.push(`/(modals)/budget-form?id=${budget.id}`);
  };

  const handleDelete = () => {
    Alert.alert(
      t('budgets.deleteTitle'),
      t('budgets.deleteMessage', { name: budget.name }),
      [
        { text: t('common.cancel'), style: 'cancel' },
        {
          text: t('common.delete'),
          style: 'destructive',
          onPress: async () => {
            await deleteMutation.mutateAsync(budget.id);
            router.back();
          },
        },
      ]
    );
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Stack.Screen
        options={{
          title: budget.name,
          headerRight: () => (
            <View style={styles.headerActions}>
              <IconButton icon="pencil" onPress={handleEdit} />
              <IconButton icon="trash" onPress={handleDelete} variant="danger" />
            </View>
          ),
        }}
      />

      {/* Budget Overview Section */}
      <Section title={t('budgets.overview')}>
        <View style={styles.amountRow}>
          <View>
            <Text style={styles.amountLabel}>{t('budgets.totalBudget')}</Text>
            <Text style={styles.amountValue}>
              {formatCurrency(budget.amount)}
            </Text>
          </View>
          <View style={styles.amountRight}>
            <Text style={styles.amountLabel}>{t('budgets.remaining')}</Text>
            <Text
              style={[
                styles.amountValue,
                remaining < 0 && styles.amountNegative,
              ]}
            >
              {formatCurrency(remaining)}
            </Text>
          </View>
        </View>
        <ProgressBar
          progress={Math.min(spentPercentage, 1)}
          color={spentPercentage > 0.9 ? colors.error : colors.primary}
        />
      </Section>

      {/* Category Section */}
      <Section title={t('budgets.details')}>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>{t('budgets.category')}</Text>
          <Text style={styles.detailValue}>
            {t(`categories.${budget.category}`)}
          </Text>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>{t('budgets.period')}</Text>
          <Text style={styles.detailValue}>{budget.period}</Text>
        </View>
      </Section>

      {/* Metadata Section */}
      <Section title={t('budgets.metadata')}>
        <Text style={styles.metaText}>
          {t('common.createdAt', { date: formatDate(budget.createdAt) })}
        </Text>
        {budget.updatedAt && (
          <Text style={styles.metaText}>
            {t('common.updatedAt', { date: formatDate(budget.updatedAt) })}
          </Text>
        )}
      </Section>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: spacing.md,
    gap: spacing.lg,
  },
  headerActions: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  amountRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
  },
  amountRight: {
    alignItems: 'flex-end',
  },
  amountLabel: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  amountValue: {
    ...typography.heading2,
    color: colors.text,
  },
  amountNegative: {
    color: colors.error,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: spacing.sm,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  detailLabel: {
    ...typography.body,
    color: colors.textSecondary,
  },
  detailValue: {
    ...typography.body,
    color: colors.text,
    fontWeight: '500',
  },
  metaText: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
});
```

---

## Screen with Tab Navigation Layout

```typescript
// app/(tabs)/_layout.tsx
import { Tabs } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '@/constants';

export default function TabLayout() {
  const { t } = useTranslation();

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textSecondary,
        headerShown: true,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: t('tabs.dashboard'),
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="budgets"
        options={{
          title: t('tabs.budgets'),
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="wallet-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="transactions"
        options={{
          title: t('tabs.transactions'),
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="list-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: t('tabs.settings'),
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="settings-outline" size={size} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}
```

---

## Root Layout with Providers

```typescript
// app/_layout.tsx
import { useEffect } from 'react';
import { Stack } from 'expo-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useFonts } from 'expo-font';
import * as SplashScreen from 'expo-splash-screen';
import { initI18n } from '@/locales/i18n';
import { initDatabase } from '@/db/client';

SplashScreen.preventAutoHideAsync();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 2,
    },
  },
});

export default function RootLayout() {
  const [fontsLoaded] = useFonts({
    // Add custom fonts here
  });

  useEffect(() => {
    async function prepare() {
      await initI18n();
      await initDatabase();
      if (fontsLoaded) {
        await SplashScreen.hideAsync();
      }
    }
    prepare();
  }, [fontsLoaded]);

  if (!fontsLoaded) return null;

  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <StatusBar style="auto" />
        <Stack>
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          <Stack.Screen
            name="(modals)"
            options={{ presentation: 'modal', headerShown: false }}
          />
          <Stack.Screen name="(auth)" options={{ headerShown: false }} />
          <Stack.Screen name="+not-found" />
        </Stack>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
```

---

## useFocusEffect for Data Refresh

Refresh data when a screen comes into focus (e.g., after returning from a form).

```typescript
import { useFocusEffect } from 'expo-router';
import { useCallback } from 'react';

export default function BudgetsScreen() {
  const { refetch } = useBudgets();

  // Refetch when screen comes into focus
  useFocusEffect(
    useCallback(() => {
      refetch();
    }, [refetch])
  );

  // ... rest of screen
}
```
