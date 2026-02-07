# Tamagui Style Guide

Universal UI kit for React Native with optimal performance.

---

## Setup

### Installation

```bash
npx expo install tamagui @tamagui/config @tamagui/babel-plugin
```

### Configuration

```typescript
// tamagui.config.ts
import { createTamagui } from 'tamagui';
import { config } from '@tamagui/config/v3';

const appConfig = createTamagui({
  ...config,
  themes: {
    ...config.themes,
    // Custom themes
    brand: {
      background: '#ffffff',
      backgroundHover: '#f5f5f5',
      backgroundPress: '#ebebeb',
      color: '#1a1a1a',
      colorHover: '#333333',
      primary: '#3b82f6',
      secondary: '#6366f1',
    },
    brand_dark: {
      background: '#1a1a1a',
      backgroundHover: '#2a2a2a',
      backgroundPress: '#3a3a3a',
      color: '#ffffff',
      colorHover: '#ebebeb',
      primary: '#60a5fa',
      secondary: '#818cf8',
    },
  },
  tokens: {
    ...config.tokens,
    // Custom tokens
    color: {
      ...config.tokens.color,
      brandPrimary: '#3b82f6',
      brandSecondary: '#6366f1',
    },
    space: {
      ...config.tokens.space,
      xs: 4,
      sm: 8,
      md: 16,
      lg: 24,
      xl: 32,
    },
    radius: {
      ...config.tokens.radius,
      sm: 4,
      md: 8,
      lg: 12,
      xl: 16,
      full: 9999,
    },
  },
});

export type AppConfig = typeof appConfig;

declare module 'tamagui' {
  interface TamaguiCustomConfig extends AppConfig {}
}

export default appConfig;
```

```javascript
// babel.config.js
module.exports = function (api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: [
      [
        '@tamagui/babel-plugin',
        {
          components: ['tamagui'],
          config: './tamagui.config.ts',
          logTimings: true,
          disableExtraction: process.env.NODE_ENV === 'development',
        },
      ],
      'react-native-reanimated/plugin',
    ],
  };
};
```

```typescript
// app/_layout.tsx
import { TamaguiProvider } from 'tamagui';
import config from '../tamagui.config';

export default function RootLayout() {
  return (
    <TamaguiProvider config={config}>
      <Stack />
    </TamaguiProvider>
  );
}
```

---

## Component Patterns

### Button Component

```typescript
// components/Button.tsx
import { Button as TamaguiButton, styled, GetProps } from 'tamagui';

export const Button = styled(TamaguiButton, {
  name: 'Button',

  // Base styles
  borderRadius: '$md',
  fontWeight: '600',
  pressStyle: {
    opacity: 0.8,
    scale: 0.98,
  },
  animation: 'quick',

  // Variants
  variants: {
    variant: {
      primary: {
        backgroundColor: '$primary',
        color: 'white',
      },
      secondary: {
        backgroundColor: '$secondary',
        color: 'white',
      },
      outline: {
        backgroundColor: 'transparent',
        borderWidth: 2,
        borderColor: '$primary',
        color: '$primary',
      },
      ghost: {
        backgroundColor: 'transparent',
        color: '$primary',
        hoverStyle: {
          backgroundColor: '$backgroundHover',
        },
      },
    },
    size: {
      sm: {
        height: 36,
        paddingHorizontal: '$sm',
        fontSize: '$3',
      },
      md: {
        height: 44,
        paddingHorizontal: '$md',
        fontSize: '$4',
      },
      lg: {
        height: 52,
        paddingHorizontal: '$lg',
        fontSize: '$5',
      },
    },
    fullWidth: {
      true: {
        width: '100%',
      },
    },
  } as const,

  // Default variants
  defaultVariants: {
    variant: 'primary',
    size: 'md',
  },
});

export type ButtonProps = GetProps<typeof Button>;
```

### Card Component

```typescript
// components/Card.tsx
import { Card as TamaguiCard, styled, XStack, YStack, H3, Paragraph } from 'tamagui';

export const Card = styled(TamaguiCard, {
  name: 'Card',

  backgroundColor: '$background',
  borderRadius: '$lg',
  padding: '$md',
  borderWidth: 1,
  borderColor: '$borderColor',

  variants: {
    elevated: {
      true: {
        shadowColor: '$shadowColor',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 8,
        elevation: 3,
      },
    },
    pressable: {
      true: {
        pressStyle: {
          scale: 0.98,
          backgroundColor: '$backgroundHover',
        },
        animation: 'quick',
      },
    },
  } as const,
});

export function CardHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <YStack paddingBottom="$sm" borderBottomWidth={1} borderColor="$borderColor">
      <H3>{title}</H3>
      {subtitle && (
        <Paragraph theme="alt2" size="$3">
          {subtitle}
        </Paragraph>
      )}
    </YStack>
  );
}

export function CardContent({ children }: { children: React.ReactNode }) {
  return <YStack paddingTop="$sm">{children}</YStack>;
}

export function CardFooter({ children }: { children: React.ReactNode }) {
  return (
    <XStack paddingTop="$sm" justifyContent="flex-end" gap="$sm">
      {children}
    </XStack>
  );
}
```

### Input Component

```typescript
// components/Input.tsx
import { Input as TamaguiInput, Label, YStack, Paragraph, styled } from 'tamagui';
import { forwardRef } from 'react';

const StyledInput = styled(TamaguiInput, {
  name: 'Input',

  backgroundColor: '$backgroundHover',
  borderRadius: '$md',
  borderWidth: 1,
  borderColor: '$borderColor',
  paddingHorizontal: '$md',
  height: 48,

  focusStyle: {
    borderColor: '$primary',
    backgroundColor: '$background',
  },

  variants: {
    error: {
      true: {
        borderColor: '$red10',
      },
    },
    size: {
      sm: { height: 36, fontSize: '$3' },
      md: { height: 48, fontSize: '$4' },
      lg: { height: 56, fontSize: '$5' },
    },
  } as const,

  defaultVariants: {
    size: 'md',
  },
});

interface InputProps extends React.ComponentProps<typeof StyledInput> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = forwardRef<any, InputProps>(
  ({ label, error, helperText, ...props }, ref) => {
    return (
      <YStack gap="$xs">
        {label && (
          <Label htmlFor={props.id} size="$3" fontWeight="500">
            {label}
          </Label>
        )}

        <StyledInput ref={ref} error={!!error} {...props} />

        {error && (
          <Paragraph size="$2" color="$red10">
            {error}
          </Paragraph>
        )}

        {helperText && !error && (
          <Paragraph size="$2" theme="alt2">
            {helperText}
          </Paragraph>
        )}
      </YStack>
    );
  }
);
```

---

## Layout Components

### Screen Layout

```typescript
// components/ScreenLayout.tsx
import { YStack, ScrollView } from 'tamagui';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
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
    <YStack
      flex={1}
      backgroundColor="$background"
      paddingHorizontal={padded ? '$md' : 0}
      paddingTop={insets.top}
      paddingBottom={insets.bottom}
    >
      {children}
    </YStack>
  );

  if (scrollable) {
    return (
      <ScrollView
        flex={1}
        backgroundColor="$background"
        showsVerticalScrollIndicator={false}
      >
        {content}
      </ScrollView>
    );
  }

  return content;
}
```

### Stack Layouts

```typescript
// Using Tamagui's built-in stacks
import { XStack, YStack, ZStack } from 'tamagui';

// Horizontal stack
<XStack gap="$md" alignItems="center" justifyContent="space-between">
  <Button>Cancel</Button>
  <Button variant="primary">Save</Button>
</XStack>

// Vertical stack
<YStack gap="$sm" padding="$md">
  <Input label="Email" />
  <Input label="Password" secureTextEntry />
  <Button fullWidth>Sign In</Button>
</YStack>

// Overlapping stack
<ZStack width={100} height={100}>
  <Circle size={80} backgroundColor="$blue10" />
  <Circle size={60} backgroundColor="$green10" />
  <Circle size={40} backgroundColor="$red10" />
</ZStack>
```

---

## Themes

### Using Themes

```typescript
// Light/dark mode
import { useColorScheme } from 'react-native';
import { Theme } from 'tamagui';

function App() {
  const colorScheme = useColorScheme();

  return (
    <Theme name={colorScheme === 'dark' ? 'brand_dark' : 'brand'}>
      <YStack flex={1} backgroundColor="$background">
        <Paragraph color="$color">Themed content</Paragraph>
      </YStack>
    </Theme>
  );
}

// Nested themes
<Theme name="brand">
  <Card>
    <Theme name="brand_dark">
      <YStack padding="$md" backgroundColor="$background">
        <Paragraph>Dark section</Paragraph>
      </YStack>
    </Theme>
  </Card>
</Theme>
```

---

## Animations

```typescript
// components/AnimatedCard.tsx
import { Card, YStack, Paragraph } from 'tamagui';

export function AnimatedCard({ title, description }) {
  return (
    <Card
      animation="bouncy"
      pressStyle={{ scale: 0.95 }}
      hoverStyle={{ scale: 1.02 }}
      elevated
      padding="$md"
    >
      <YStack gap="$sm">
        <Paragraph fontWeight="600">{title}</Paragraph>
        <Paragraph theme="alt2">{description}</Paragraph>
      </YStack>
    </Card>
  );
}
```

---

## Best Practices

1. **Use styled()** - Create reusable styled components
2. **Define variants** - Use variants for component variations
3. **Token-based design** - Reference tokens instead of raw values
4. **Type safety** - Use GetProps for prop typing
5. **Theme-aware** - Use theme tokens for colors
6. **Performance** - Enable extraction in production
7. **Responsive** - Use media queries for responsive design

```typescript
// Responsive styles
const ResponsiveBox = styled(YStack, {
  padding: '$md',

  '@sm': {
    padding: '$lg',
  },

  '@md': {
    padding: '$xl',
    flexDirection: 'row',
  },
});
```
