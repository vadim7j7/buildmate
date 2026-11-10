# gluestack-ui Style Guide

gluestack-ui (v3 and later; the docs are on v5) is **not a package you import
components from**. The CLI copies each component's source into the project, and the
components are styled with Tailwind classes through NativeWind (or UniWind). You own
and edit that code.

The v1 packages (`@gluestack-ui/themed`, `@gluestack-style/react`,
`@gluestack-ui/config`, `bg="$primary500"` style props) are retired: never add them.

---

## Setup

```bash
npx gluestack-ui@latest init                 # picks the styling engine, adds GluestackUIProvider,
                                             # edits metro/babel config, global.css and the entry file
npx gluestack-ui@latest add button input box # one component at a time
npx gluestack-ui@latest add --all            # or everything
```

The CLI writes to `components/ui/` by default. This project keeps app code in `src/`,
so pass `--path src/components/ui` (and record it in `gluestack-ui.config.json`
under `app.components`). Components are then imported as `@/components/ui/<name>`.
`init` rewrites `babel.config.js` and `metro.config.js`: keep the Drizzle lines
(`inline-import` for `.sql`, `sourceExts.push("sql")`) when it does.

```typescript
// src/app/_layout.tsx
import '@/global.css';
import { Stack } from 'expo-router';
import { GluestackUIProvider } from '@/components/ui/gluestack-ui-provider';

export default function RootLayout() {
  return (
    <GluestackUIProvider mode="system">  {/* 'light' | 'dark' | 'system' */}
      <Stack />
    </GluestackUIProvider>
  );
}
```

---

## Theme

Tokens are CSS variables defined per mode in
`src/components/ui/gluestack-ui-provider/config.ts` (bare RGB triplets, so opacity
modifiers work) and mapped to Tailwind colours in `global.css`:

```typescript
// src/components/ui/gluestack-ui-provider/config.ts
import { vars } from 'nativewind';

export const config = {
  light: vars({ '--primary': '59 130 246', '--primary-foreground': '255 255 255' /* ... */ }),
  dark: vars({ '--primary': '147 197 253', '--primary-foreground': '15 23 42' /* ... */ }),
};
```

Use the semantic colour classes the theme defines: `bg-background`, `text-foreground`,
`bg-card`, `bg-primary` / `text-primary-foreground`, `bg-secondary`, `bg-muted` /
`text-muted-foreground`, `bg-destructive`, `border-border`, `border-input`, plus opacity
(`bg-primary/10`). Projects generated with v3 use numbered scales (`bg-primary-500`):
follow whatever the generated `config.ts` defines. Brand changes go in `config.ts`,
never as hex values in components.

---

## Using Components

```typescript
// src/components/forms/SaveButton.tsx
import { Button, ButtonText, ButtonSpinner } from '@/components/ui/button';

interface SaveButtonProps {
  label: string;
  isSaving: boolean;
  onPress: () => void;
}

export function SaveButton({ label, isSaving, onPress }: SaveButtonProps) {
  return (
    <Button action="primary" size="md" isDisabled={isSaving} onPress={onPress}>
      {isSaving && <ButtonSpinner className="mr-2" />}
      <ButtonText>{label}</ButtonText>
    </Button>
  );
}
```

- Variant props (`action`, `variant`, `size`) come from the component's `tva` definition.
- Extra styling is `className`; it is merged with the variant classes.
- Layout primitives: `Box`, `VStack` / `HStack` (`space="md"`), `Center`, `Text`,
  `Heading`, all from `@/components/ui/<name>`.

### A Card Built from Primitives

```typescript
// src/components/lists/TransactionCard.tsx
import { Pressable } from '@/components/ui/pressable';
import { HStack } from '@/components/ui/hstack';
import { VStack } from '@/components/ui/vstack';
import { Text } from '@/components/ui/text';
import type { Transaction } from '@/db/schema';

interface TransactionCardProps {
  transaction: Transaction;
  onPress?: (id: string) => void;
}

export function TransactionCard({ transaction, onPress }: TransactionCardProps) {
  const isExpense = transaction.amount < 0;
  return (
    <Pressable
      onPress={() => onPress?.(transaction.id)}
      className="mx-4 rounded-lg bg-card p-4 data-[active=true]:opacity-80"
    >
      <HStack space="md" className="items-center">
        <VStack className="flex-1">
          <Text className="text-foreground" numberOfLines={1}>{transaction.description}</Text>
          <Text size="sm" className="capitalize text-muted-foreground">{transaction.category}</Text>
        </VStack>
        <Text bold className={isExpense ? 'text-destructive' : 'text-primary'}>
          {transaction.amount.toFixed(2)}
        </Text>
      </HStack>
    </Pressable>
  );
}
```

State styling uses the `data-*` attributes the components set (`data-[active=true]`,
`data-[disabled=true]`, `data-[focus=true]`, `data-[invalid=true]`).

### Form Field

```typescript
import { FormControl, FormControlLabel, FormControlLabelText, FormControlError,
  FormControlErrorText } from '@/components/ui/form-control';
import { Input, InputField } from '@/components/ui/input';

<FormControl isInvalid={!!errors.name} isRequired>
  <FormControlLabel>
    <FormControlLabelText>{t('budgets.name')}</FormControlLabelText>
  </FormControlLabel>
  <Input variant="outline" size="md">
    <InputField value={name} onChangeText={setName} testID="budget-name-input" />
  </Input>
  <FormControlError>
    <FormControlErrorText>{errors.name}</FormControlErrorText>
  </FormControlError>
</FormControl>
```

---

## Writing Your Own Variants

New project components follow the generated files: a `tva` style definition plus a
component that forwards `className`. Import `tva` from the same module the generated
components in `src/components/ui/` import it from (the path differs between versions).

```typescript
// src/components/ui/badge-pill/index.tsx
import { Text } from 'react-native';
import { tva, type VariantProps } from '<same import as src/components/ui/box/index.tsx>';

const pillStyle = tva({
  base: 'self-start rounded-full px-2 py-0.5 text-xs font-medium',
  variants: {
    tone: {
      neutral: 'bg-muted text-foreground',
      success: 'bg-primary/10 text-primary',
      danger: 'bg-destructive/10 text-destructive',
    },
  },
  defaultVariants: { tone: 'neutral' },
});

type PillProps = React.ComponentProps<typeof Text> & VariantProps<typeof pillStyle>;

export function Pill({ tone, className, ...props }: PillProps) {
  return <Text className={pillStyle({ tone, class: className })} {...props} />;
}
```

React 19: `ref` is a normal prop, so components take it in their props; no `forwardRef`.

---

## Rules

1. Add components with the CLI, then edit the copied source; don't wrap them in
   another layer just to restyle them.
2. Style with `className` and theme colour classes; no `StyleSheet.create`, no hex values.
3. Class names are whole static strings (`isExpense ? 'text-destructive' : 'text-primary'`),
   never built with template strings (`text-${tone}`), which Tailwind can't see.
4. Variants live in `tva`, not in ad-hoc conditionals spread across screens.
5. Inline `style` only for runtime-computed values (animations, measured sizes).
