# StyleSheet Style Guide

Styling rules for projects that style with plain React Native `StyleSheet`
(the `ui` option `none`: no NativeWind, Tamagui or Gluestack).

---

## 1. StyleSheet.create Rules

**Always** use `StyleSheet.create()` for all styles. Never use inline style objects.

```typescript
// CORRECT
const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: spacing.md,
    backgroundColor: colors.background,
  },
});

<View style={styles.container} />

// CORRECT - combining styles
<View style={[styles.container, styles.centered]} />

// CORRECT - conditional styles
<Text style={[styles.label, isActive && styles.labelActive]} />

// WRONG - inline style object
<View style={{ flex: 1, padding: 16, backgroundColor: '#fff' }} />

// WRONG - computed object outside StyleSheet
const customStyle = { padding: 16 };
<View style={customStyle} />
```

Define styles at the bottom of the file, after the component:

```typescript
export function MyComponent() {
  return <View style={styles.container}>...</View>;
}

const styles = StyleSheet.create({
  container: { ... },
});
```

---

## 2. Theme Constants

Import all visual values from `@/constants`. **Never hardcode** colours, fonts,
or border radii.

```typescript
// CORRECT
import { colors, spacing, typography, borderRadius, shadows } from '@/constants';

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    ...shadows.sm,
  },
  title: {
    ...typography.heading3,
    color: colors.text,
  },
});

// WRONG - hardcoded values
const styles = StyleSheet.create({
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 8,
    padding: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
  },
});
```

Available constant modules:

| Module | Purpose | Example |
|---|---|---|
| `colors` | Colour palette | `colors.primary`, `colors.text`, `colors.surface` |
| `spacing` | Spacing scale | `spacing.xs`, `spacing.md`, `spacing.xl` |
| `typography` | Font presets | `typography.body`, `typography.heading3` |
| `borderRadius` | Border radius scale | `borderRadius.sm`, `borderRadius.md` |
| `shadows` | Platform shadows | `shadows.sm`, `shadows.md` |
| `layout` | Screen dimensions | `layout.screenWidth`, `layout.safeAreaTop` |

---

## 3. Spacing Scale

Use the standard spacing scale for all padding, margin, and gap values:

| Token | Value | Use for |
|---|---|---|
| `spacing.xs` | 4 | Tight spacing, icon gaps |
| `spacing.sm` | 8 | Inner padding, list item gaps |
| `spacing.md` | 16 | Standard padding, section gaps |
| `spacing.lg` | 24 | Section separators, card padding |
| `spacing.xl` | 32 | Screen-level padding, major sections |
| `spacing.xxl` | 48 | Hero areas, large separators |

```typescript
// CORRECT
padding: spacing.md,
marginBottom: spacing.lg,
gap: spacing.sm,

// WRONG
padding: 16,
marginBottom: 24,
gap: 8,
```

