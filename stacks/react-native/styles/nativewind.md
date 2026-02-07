# NativeWind Style Guide

Tailwind CSS for React Native using NativeWind.

---

## Setup

### Installation

```bash
npx expo install nativewind tailwindcss react-native-reanimated react-native-safe-area-context
```

### Configuration

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,jsx,ts,tsx}',
    './components/**/*.{js,jsx,ts,tsx}',
  ],
  presets: [require('nativewind/preset')],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        secondary: {
          500: '#6366f1',
          600: '#4f46e5',
        },
      },
      fontFamily: {
        sans: ['Inter'],
        heading: ['Inter-Bold'],
      },
    },
  },
  plugins: [],
};
```

```javascript
// babel.config.js
module.exports = function (api) {
  api.cache(true);
  return {
    presets: [
      ['babel-preset-expo', { jsxImportSource: 'nativewind' }],
      'nativewind/babel',
    ],
  };
};
```

```javascript
// metro.config.js
const { getDefaultConfig } = require('expo/metro-config');
const { withNativeWind } = require('nativewind/metro');

const config = getDefaultConfig(__dirname);

module.exports = withNativeWind(config, { input: './global.css' });
```

```css
/* global.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

---

## Component Patterns

### Basic Styling

```typescript
// components/Button.tsx
import { Text, Pressable } from 'react-native';

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: 'bg-primary-600 active:bg-primary-700',
  secondary: 'bg-secondary-500 active:bg-secondary-600',
  outline: 'border-2 border-primary-600 bg-transparent',
  ghost: 'bg-transparent',
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5',
  md: 'px-4 py-2',
  lg: 'px-6 py-3',
};

const textVariantStyles: Record<ButtonVariant, string> = {
  primary: 'text-white',
  secondary: 'text-white',
  outline: 'text-primary-600',
  ghost: 'text-primary-600',
};

const textSizeStyles: Record<ButtonSize, string> = {
  sm: 'text-sm',
  md: 'text-base',
  lg: 'text-lg',
};

export function Button({
  title,
  onPress,
  variant = 'primary',
  size = 'md',
  disabled = false,
}: ButtonProps) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      className={`
        rounded-lg items-center justify-center
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${disabled ? 'opacity-50' : ''}
      `}
    >
      <Text
        className={`
          font-semibold
          ${textVariantStyles[variant]}
          ${textSizeStyles[size]}
        `}
      >
        {title}
      </Text>
    </Pressable>
  );
}
```

### Card Component

```typescript
// components/Card.tsx
import { View, Text, Pressable } from 'react-native';
import { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  onPress?: () => void;
  className?: string;
}

export function Card({ children, onPress, className = '' }: CardProps) {
  const Wrapper = onPress ? Pressable : View;

  return (
    <Wrapper
      onPress={onPress}
      className={`
        bg-white rounded-xl p-4 shadow-sm
        border border-gray-100
        ${onPress ? 'active:bg-gray-50' : ''}
        ${className}
      `}
    >
      {children}
    </Wrapper>
  );
}

export function CardHeader({ children }: { children: ReactNode }) {
  return (
    <View className="border-b border-gray-100 pb-3 mb-3">
      {children}
    </View>
  );
}

export function CardTitle({ children }: { children: string }) {
  return (
    <Text className="text-lg font-semibold text-gray-900">
      {children}
    </Text>
  );
}

export function CardContent({ children }: { children: ReactNode }) {
  return <View>{children}</View>;
}
```

### Input Component

```typescript
// components/Input.tsx
import { View, Text, TextInput, TextInputProps } from 'react-native';
import { forwardRef } from 'react';

interface InputProps extends TextInputProps {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = forwardRef<TextInput, InputProps>(
  ({ label, error, helperText, className = '', ...props }, ref) => {
    return (
      <View className="mb-4">
        {label && (
          <Text className="text-sm font-medium text-gray-700 mb-1.5">
            {label}
          </Text>
        )}

        <TextInput
          ref={ref}
          className={`
            px-4 py-3 rounded-lg
            bg-gray-50 border
            text-gray-900 text-base
            ${error ? 'border-red-500' : 'border-gray-200'}
            focus:border-primary-500 focus:bg-white
            ${className}
          `}
          placeholderTextColor="#9ca3af"
          {...props}
        />

        {error && (
          <Text className="text-sm text-red-500 mt-1">{error}</Text>
        )}

        {helperText && !error && (
          <Text className="text-sm text-gray-500 mt-1">{helperText}</Text>
        )}
      </View>
    );
  }
);
```

---

## Layout Patterns

### Screen Layout

```typescript
// components/ScreenLayout.tsx
import { View, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ReactNode } from 'react';

interface ScreenLayoutProps {
  children: ReactNode;
  scrollable?: boolean;
  padded?: boolean;
  safeArea?: boolean;
}

export function ScreenLayout({
  children,
  scrollable = true,
  padded = true,
  safeArea = true,
}: ScreenLayoutProps) {
  const Container = safeArea ? SafeAreaView : View;
  const padding = padded ? 'px-4' : '';

  const content = (
    <View className={`flex-1 bg-white ${padding}`}>
      {children}
    </View>
  );

  return (
    <Container className="flex-1 bg-white">
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        className="flex-1"
      >
        {scrollable ? (
          <ScrollView
            showsVerticalScrollIndicator={false}
            contentContainerStyle={{ flexGrow: 1 }}
          >
            {content}
          </ScrollView>
        ) : (
          content
        )}
      </KeyboardAvoidingView>
    </Container>
  );
}
```

### Flex Layouts

```typescript
// components/Flex.tsx
import { View } from 'react-native';
import { ReactNode } from 'react';

interface FlexProps {
  children: ReactNode;
  direction?: 'row' | 'column';
  justify?: 'start' | 'center' | 'end' | 'between' | 'around';
  align?: 'start' | 'center' | 'end' | 'stretch';
  gap?: number;
  wrap?: boolean;
  className?: string;
}

const justifyStyles = {
  start: 'justify-start',
  center: 'justify-center',
  end: 'justify-end',
  between: 'justify-between',
  around: 'justify-around',
};

const alignStyles = {
  start: 'items-start',
  center: 'items-center',
  end: 'items-end',
  stretch: 'items-stretch',
};

export function Flex({
  children,
  direction = 'row',
  justify = 'start',
  align = 'stretch',
  gap = 0,
  wrap = false,
  className = '',
}: FlexProps) {
  return (
    <View
      className={`
        ${direction === 'row' ? 'flex-row' : 'flex-col'}
        ${justifyStyles[justify]}
        ${alignStyles[align]}
        ${wrap ? 'flex-wrap' : ''}
        gap-${gap}
        ${className}
      `}
    >
      {children}
    </View>
  );
}
```

---

## Dark Mode

```typescript
// hooks/useColorScheme.ts
import { useColorScheme as useRNColorScheme } from 'react-native';

export function useColorScheme() {
  const colorScheme = useRNColorScheme();
  return colorScheme ?? 'light';
}

// Usage in components
function ThemedCard() {
  return (
    <View className="bg-white dark:bg-gray-800 p-4 rounded-lg">
      <Text className="text-gray-900 dark:text-white">
        Themed content
      </Text>
    </View>
  );
}
```

---

## Animations with Reanimated

```typescript
// components/AnimatedButton.tsx
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
} from 'react-native-reanimated';
import { Pressable, Text } from 'react-native';

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

export function AnimatedButton({ title, onPress }) {
  const scale = useSharedValue(1);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  return (
    <AnimatedPressable
      onPressIn={() => {
        scale.value = withSpring(0.95);
      }}
      onPressOut={() => {
        scale.value = withSpring(1);
      }}
      onPress={onPress}
      style={animatedStyle}
      className="bg-primary-600 px-6 py-3 rounded-xl"
    >
      <Text className="text-white font-semibold text-center">
        {title}
      </Text>
    </AnimatedPressable>
  );
}
```

---

## Best Practices

1. **Use semantic class names** - Group related styles together
2. **Extract repeated patterns** - Create reusable components
3. **Use variants** - Define variant props for component variations
4. **Leverage TypeScript** - Type your variant options
5. **Dark mode first** - Design with both modes in mind
6. **Responsive design** - Use breakpoint prefixes when needed
7. **Performance** - Memoize style objects when using dynamic values
