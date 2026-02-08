# React Native Verification Pattern

## Overview

React Native implementations are verified using Jest tests, TypeScript checks,
and Expo dev server validation. Tests ensure components render, handle props,
and respond to interactions correctly.

## Prerequisites

- Expo dev server can start
- Jest configured with React Native Testing Library
- TypeScript configured

## Verification Workflow

### 1. TypeScript Check

```bash
npx tsc --noEmit
```

### 2. Run Component Tests

```bash
npm test -- --testPathPattern="ComponentName" --coverage
```

### 3. Check Expo Bundler

```bash
# Start Expo
npx expo start --no-dev &

# Wait for bundler
until curl -s http://localhost:8081/status; do sleep 1; done

# Check bundle compiles
curl http://localhost:8081/index.bundle?platform=ios
```

### 4. Lint Check

```bash
npm run lint
```

## Component Testing

### Basic Render Test

```typescript
import React from 'react';
import { render } from '@testing-library/react-native';
import { HeroSection } from '../HeroSection';

describe('HeroSection', () => {
  const defaultProps = {
    title: 'Welcome',
    subtitle: 'Get started today',
    primaryCta: 'Sign Up',
  };

  it('renders without crashing', () => {
    const { toJSON } = render(<HeroSection {...defaultProps} />);
    expect(toJSON()).toBeTruthy();
  });

  it('displays title and subtitle', () => {
    const { getByText } = render(<HeroSection {...defaultProps} />);
    expect(getByText('Welcome')).toBeTruthy();
    expect(getByText('Get started today')).toBeTruthy();
  });

  it('renders primary CTA button', () => {
    const { getByText } = render(<HeroSection {...defaultProps} />);
    expect(getByText('Sign Up')).toBeTruthy();
  });
});
```

### Interaction Testing

```typescript
import { fireEvent } from '@testing-library/react-native';

it('calls onPrimaryPress when button pressed', () => {
  const onPress = jest.fn();
  const { getByText } = render(
    <HeroSection {...defaultProps} onPrimaryPress={onPress} />
  );

  fireEvent.press(getByText('Sign Up'));
  expect(onPress).toHaveBeenCalledTimes(1);
});
```

### Snapshot Testing

```typescript
it('matches snapshot', () => {
  const { toJSON } = render(<HeroSection {...defaultProps} />);
  expect(toJSON()).toMatchSnapshot();
});
```

### Accessibility Testing

```typescript
it('has accessible button', () => {
  const { getByRole } = render(<HeroSection {...defaultProps} />);
  expect(getByRole('button', { name: 'Sign Up' })).toBeTruthy();
});

it('has accessible labels', () => {
  const { getByLabelText } = render(
    <HeroSection {...defaultProps} />
  );
  // Check custom accessibility labels
  expect(getByLabelText('Hero section')).toBeTruthy();
});
```

## Platform Compatibility

### Check Platform-Specific Code

```bash
# Find platform extensions
find src -name "*.ios.tsx" -o -name "*.android.tsx"

# Check Platform usage
grep -r "Platform.OS" src/
grep -r "Platform.select" src/
```

### Platform-Safe APIs

| Web API | React Native Alternative |
|---------|-------------------------|
| `window.innerWidth` | `Dimensions.get('window').width` |
| `localStorage` | `AsyncStorage` |
| `window.location` | `Linking` |
| `document.querySelector` | Use refs |
| `addEventListener` | Use component lifecycle |

## StyleSheet Validation

### Check Style Properties

```typescript
// Valid RN styles
const validStyles = {
  flex: 1,
  flexDirection: 'row',
  backgroundColor: '#fff',
  padding: 16,
  borderRadius: 8,
  shadowColor: '#000',
  shadowOffset: { width: 0, height: 2 },
  shadowOpacity: 0.1,
  shadowRadius: 4,
  elevation: 3, // Android shadow
};

// Invalid (web-only)
const invalidStyles = {
  cursor: 'pointer',       // No cursor on mobile
  userSelect: 'none',      // Not supported
  transition: '0.3s',      // Use Animated
  display: 'grid',         // Use flexbox
  boxShadow: '0 2px 4px',  // Use shadow* props
};
```

### StyleSheet.create Enforcement

```typescript
// Good - uses StyleSheet.create
const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
});

// Bad - inline styles (performance issue)
<View style={{ flex: 1, padding: 16 }} />
```

## Performance Checks

### Avoid These Patterns

```typescript
// Bad - inline function recreated each render
<Button onPress={() => doSomething(id)} />

// Good - use useCallback
const handlePress = useCallback(() => doSomething(id), [id]);
<Button onPress={handlePress} />

// Bad - inline style object
<View style={{ margin: 10 }} />

// Good - StyleSheet
<View style={styles.container} />

// Bad - missing keys in list
items.map(item => <Item {...item} />)

// Good - with keys
items.map(item => <Item key={item.id} {...item} />)
```

### Memoization

```typescript
// Memoize expensive components
export const HeroSection = React.memo(function HeroSection(props) {
  // ...
});

// Memoize computed values
const expensiveValue = useMemo(() => compute(data), [data]);

// Memoize callbacks
const handlePress = useCallback(() => {}, []);
```

## Auto-Fix Patterns

### Test Fails - Missing Mock

**Error:** `Cannot find module 'react-native-gesture-handler'`

**Fix:**
```typescript
// jest.setup.js
import 'react-native-gesture-handler/jestSetup';

// or mock it
jest.mock('react-native-gesture-handler', () => ({}));
```

### Type Error

**Error:** `Property 'onPress' is missing`

**Fix:**
```typescript
interface HeroSectionProps {
  title: string;
  subtitle: string;
  primaryCta: string;
  onPrimaryPress?: () => void; // Make optional with ?
}
```

### Style Error

**Error:** `Invalid style property 'cursor'`

**Fix:** Remove web-only style properties:
```typescript
// Remove cursor, userSelect, etc.
const styles = StyleSheet.create({
  button: {
    // cursor: 'pointer', // Remove
    padding: 16,
  },
});
```

### Platform Crash

**Error:** `window is not defined`

**Fix:**
```typescript
import { Dimensions, Platform } from 'react-native';

// Instead of window.innerWidth
const { width } = Dimensions.get('window');

// Platform-specific code
const value = Platform.select({
  ios: 'iOS value',
  android: 'Android value',
  default: 'default',
});
```

## Verification Report Template

```markdown
# React Native Verification Report

**Component:** HeroSection
**Time:** TIMESTAMP

## Test Results

```
PASS src/__tests__/HeroSection.test.tsx
  HeroSection
    ✓ renders without crashing (32ms)
    ✓ displays title and subtitle (12ms)
    ✓ calls onPrimaryPress when pressed (8ms)
    ✓ matches snapshot (15ms)

Tests: 4 passed
Coverage: 94%
```

## TypeScript

| Check | Status |
|-------|--------|
| No errors | ✓ Pass |
| Props typed | ✓ Pass |
| Strict mode | ✓ Pass |

## Platform Compatibility

| Check | Status |
|-------|--------|
| No web-only APIs | ✓ Pass |
| No invalid styles | ✓ Pass |
| Platform.select where needed | ✓ Pass |

## Performance

| Check | Status |
|-------|--------|
| StyleSheet.create used | ✓ Pass |
| No inline functions | ⚠ 2 found |
| Keys in lists | ✓ Pass |
| React.memo considered | ⚠ Recommend |

## Accessibility

| Check | Status |
|-------|--------|
| accessibilityLabel | ✓ Pass |
| accessibilityRole | ✓ Pass |
| Touch targets (44x44) | ✓ Pass |
```
