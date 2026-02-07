# Gluestack UI Style Guide

Universal component library for React Native.

---

## Setup

### Installation

```bash
npx gluestack-ui init
npx expo install @gluestack-ui/themed @gluestack-style/react
```

### Configuration

```typescript
// gluestack.config.ts
import { createConfig } from '@gluestack-ui/themed';
import { config as defaultConfig } from '@gluestack-ui/config';

export const config = createConfig({
  ...defaultConfig,
  tokens: {
    ...defaultConfig.tokens,
    colors: {
      ...defaultConfig.tokens.colors,
      // Custom brand colors
      primary50: '#eff6ff',
      primary100: '#dbeafe',
      primary200: '#bfdbfe',
      primary300: '#93c5fd',
      primary400: '#60a5fa',
      primary500: '#3b82f6',
      primary600: '#2563eb',
      primary700: '#1d4ed8',
      primary800: '#1e40af',
      primary900: '#1e3a8a',
    },
    space: {
      ...defaultConfig.tokens.space,
      xs: 4,
      sm: 8,
      md: 16,
      lg: 24,
      xl: 32,
      '2xl': 40,
    },
    radii: {
      ...defaultConfig.tokens.radii,
      sm: 4,
      md: 8,
      lg: 12,
      xl: 16,
      full: 9999,
    },
  },
  aliases: {
    ...defaultConfig.aliases,
    // Custom aliases
    bg: 'backgroundColor',
    p: 'padding',
    m: 'margin',
    w: 'width',
    h: 'height',
  },
});

type ConfigType = typeof config;

declare module '@gluestack-ui/themed' {
  interface ICustomConfig extends ConfigType {}
}
```

```typescript
// app/_layout.tsx
import { GluestackUIProvider } from '@gluestack-ui/themed';
import { config } from '../gluestack.config';

export default function RootLayout() {
  return (
    <GluestackUIProvider config={config}>
      <Stack />
    </GluestackUIProvider>
  );
}
```

---

## Component Patterns

### Button Component

```typescript
// components/Button.tsx
import {
  Button as GluestackButton,
  ButtonText,
  ButtonSpinner,
  ButtonIcon,
} from '@gluestack-ui/themed';
import { ComponentProps, ReactNode } from 'react';

interface ButtonProps extends ComponentProps<typeof GluestackButton> {
  title: string;
  isLoading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

export function Button({
  title,
  isLoading,
  leftIcon,
  rightIcon,
  variant = 'solid',
  size = 'md',
  action = 'primary',
  ...props
}: ButtonProps) {
  return (
    <GluestackButton
      variant={variant}
      size={size}
      action={action}
      isDisabled={isLoading || props.isDisabled}
      {...props}
    >
      {isLoading && <ButtonSpinner mr="$2" />}
      {leftIcon && <ButtonIcon as={leftIcon} mr="$2" />}
      <ButtonText>{title}</ButtonText>
      {rightIcon && <ButtonIcon as={rightIcon} ml="$2" />}
    </GluestackButton>
  );
}

// Usage
<Button title="Sign In" action="primary" />
<Button title="Cancel" variant="outline" action="secondary" />
<Button title="Delete" action="negative" />
<Button title="Loading..." isLoading />
```

### Card Component

```typescript
// components/Card.tsx
import {
  Box,
  Heading,
  Text,
  VStack,
  HStack,
  Pressable,
} from '@gluestack-ui/themed';
import { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  onPress?: () => void;
  variant?: 'elevated' | 'outlined' | 'filled';
}

export function Card({ children, onPress, variant = 'elevated' }: CardProps) {
  const variantStyles = {
    elevated: {
      bg: '$white',
      shadowColor: '$gray400',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.1,
      shadowRadius: 8,
      elevation: 3,
    },
    outlined: {
      bg: '$white',
      borderWidth: 1,
      borderColor: '$gray200',
    },
    filled: {
      bg: '$gray50',
    },
  };

  const Wrapper = onPress ? Pressable : Box;

  return (
    <Wrapper
      onPress={onPress}
      p="$4"
      borderRadius="$lg"
      {...variantStyles[variant]}
      sx={{
        ':active': onPress ? { opacity: 0.8 } : undefined,
      }}
    >
      {children}
    </Wrapper>
  );
}

export function CardHeader({
  title,
  subtitle,
}: {
  title: string;
  subtitle?: string;
}) {
  return (
    <VStack space="xs" mb="$3" pb="$3" borderBottomWidth={1} borderColor="$gray100">
      <Heading size="md">{title}</Heading>
      {subtitle && (
        <Text size="sm" color="$gray500">
          {subtitle}
        </Text>
      )}
    </VStack>
  );
}

export function CardContent({ children }: { children: ReactNode }) {
  return <VStack space="sm">{children}</VStack>;
}

export function CardFooter({ children }: { children: ReactNode }) {
  return (
    <HStack space="sm" mt="$4" justifyContent="flex-end">
      {children}
    </HStack>
  );
}
```

### Input Component

```typescript
// components/Input.tsx
import {
  FormControl,
  FormControlLabel,
  FormControlLabelText,
  FormControlHelper,
  FormControlHelperText,
  FormControlError,
  FormControlErrorIcon,
  FormControlErrorText,
  Input as GluestackInput,
  InputField,
  InputSlot,
  InputIcon,
} from '@gluestack-ui/themed';
import { AlertCircle } from 'lucide-react-native';
import { ComponentProps, forwardRef, ReactNode } from 'react';

interface InputProps extends ComponentProps<typeof InputField> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  isRequired?: boolean;
}

export const Input = forwardRef<any, InputProps>(
  (
    { label, error, helperText, leftIcon, rightIcon, isRequired, ...props },
    ref
  ) => {
    return (
      <FormControl isInvalid={!!error} isRequired={isRequired}>
        {label && (
          <FormControlLabel>
            <FormControlLabelText>{label}</FormControlLabelText>
          </FormControlLabel>
        )}

        <GluestackInput
          variant="outline"
          size="md"
          isInvalid={!!error}
        >
          {leftIcon && (
            <InputSlot pl="$3">
              <InputIcon as={leftIcon} color="$gray400" />
            </InputSlot>
          )}

          <InputField ref={ref} {...props} />

          {rightIcon && (
            <InputSlot pr="$3">
              <InputIcon as={rightIcon} color="$gray400" />
            </InputSlot>
          )}
        </GluestackInput>

        {error && (
          <FormControlError>
            <FormControlErrorIcon as={AlertCircle} />
            <FormControlErrorText>{error}</FormControlErrorText>
          </FormControlError>
        )}

        {helperText && !error && (
          <FormControlHelper>
            <FormControlHelperText>{helperText}</FormControlHelperText>
          </FormControlHelper>
        )}
      </FormControl>
    );
  }
);
```

---

## Layout Components

### Screen Layout

```typescript
// components/ScreenLayout.tsx
import { Box, ScrollView, VStack } from '@gluestack-ui/themed';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { KeyboardAvoidingView, Platform } from 'react-native';
import { ReactNode } from 'react';

interface ScreenLayoutProps {
  children: ReactNode;
  scrollable?: boolean;
  padded?: boolean;
}

export function ScreenLayout({
  children,
  scrollable = true,
  padded = true,
}: ScreenLayoutProps) {
  const insets = useSafeAreaInsets();

  const content = (
    <VStack
      flex={1}
      bg="$white"
      px={padded ? '$4' : '$0'}
      pt={insets.top}
      pb={insets.bottom}
    >
      {children}
    </VStack>
  );

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      {scrollable ? (
        <ScrollView
          flex={1}
          bg="$white"
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ flexGrow: 1 }}
        >
          {content}
        </ScrollView>
      ) : (
        content
      )}
    </KeyboardAvoidingView>
  );
}
```

### Stack Layouts

```typescript
// Using Gluestack's built-in stacks
import { HStack, VStack, Box } from '@gluestack-ui/themed';

// Horizontal stack
<HStack space="md" alignItems="center" justifyContent="space-between">
  <Button title="Cancel" variant="outline" />
  <Button title="Save" action="primary" />
</HStack>

// Vertical stack
<VStack space="sm" p="$4">
  <Input label="Email" placeholder="Enter email" />
  <Input label="Password" placeholder="Enter password" type="password" />
  <Button title="Sign In" />
</VStack>

// Grid-like layout
<HStack flexWrap="wrap" space="sm">
  {items.map((item) => (
    <Box key={item.id} w="48%">
      <Card>{item.content}</Card>
    </Box>
  ))}
</HStack>
```

---

## Theming

### Color Modes

```typescript
// hooks/useColorMode.ts
import { useColorMode as useGluestackColorMode } from '@gluestack-ui/themed';

export function useColorMode() {
  const { colorMode, toggleColorMode, setColorMode } = useGluestackColorMode();
  return { colorMode, toggleColorMode, setColorMode };
}

// Usage
function ThemeToggle() {
  const { colorMode, toggleColorMode } = useColorMode();

  return (
    <Button
      title={colorMode === 'dark' ? 'Light Mode' : 'Dark Mode'}
      onPress={toggleColorMode}
    />
  );
}
```

### Theme-aware Styling

```typescript
// components/ThemedCard.tsx
import { Box, useColorMode } from '@gluestack-ui/themed';

export function ThemedCard({ children }) {
  const { colorMode } = useColorMode();

  return (
    <Box
      bg={colorMode === 'dark' ? '$gray800' : '$white'}
      p="$4"
      borderRadius="$lg"
      borderWidth={1}
      borderColor={colorMode === 'dark' ? '$gray700' : '$gray200'}
    >
      {children}
    </Box>
  );
}
```

---

## Forms

### Form Pattern

```typescript
// components/LoginForm.tsx
import { VStack } from '@gluestack-ui/themed';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Input } from './Input';
import { Button } from './Button';

const loginSchema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm({ onSubmit }: { onSubmit: (data: LoginFormData) => void }) {
  const { control, handleSubmit, formState: { errors, isSubmitting } } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  return (
    <VStack space="md">
      <Controller
        control={control}
        name="email"
        render={({ field: { onChange, onBlur, value } }) => (
          <Input
            label="Email"
            placeholder="Enter your email"
            keyboardType="email-address"
            autoCapitalize="none"
            onChangeText={onChange}
            onBlur={onBlur}
            value={value}
            error={errors.email?.message}
          />
        )}
      />

      <Controller
        control={control}
        name="password"
        render={({ field: { onChange, onBlur, value } }) => (
          <Input
            label="Password"
            placeholder="Enter your password"
            type="password"
            onChangeText={onChange}
            onBlur={onBlur}
            value={value}
            error={errors.password?.message}
          />
        )}
      />

      <Button
        title="Sign In"
        onPress={handleSubmit(onSubmit)}
        isLoading={isSubmitting}
      />
    </VStack>
  );
}
```

---

## Best Practices

1. **Use semantic tokens** - Reference tokens like `$primary500` instead of raw colors
2. **Compose components** - Build complex components from primitives
3. **Form integration** - Use react-hook-form with Controller
4. **Accessibility** - Use semantic components with proper labels
5. **Theme consistency** - Stick to the design system tokens
6. **Performance** - Use memoization for complex renders
7. **Type safety** - Leverage TypeScript for props

```typescript
// Example: Accessible button group
import { ButtonGroup, Button, ButtonText } from '@gluestack-ui/themed';

<ButtonGroup isAttached>
  <Button variant="outline" action="secondary">
    <ButtonText>Option 1</ButtonText>
  </Button>
  <Button variant="solid" action="primary">
    <ButtonText>Option 2</ButtonText>
  </Button>
  <Button variant="outline" action="secondary">
    <ButtonText>Option 3</ButtonText>
  </Button>
</ButtonGroup>
```
