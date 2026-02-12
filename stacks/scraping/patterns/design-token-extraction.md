# Design Token Extraction Pattern

Patterns for extracting design system tokens (colors, typography, spacing) from websites.

## Color Extraction

### Extract Color Palette

```javascript
function extractColors() {
  const colors = new Map();

  document.querySelectorAll('*').forEach(el => {
    const style = getComputedStyle(el);

    // Collect all color properties
    [
      style.color,
      style.backgroundColor,
      style.borderColor,
      style.outlineColor,
    ].forEach(color => {
      if (color && color !== 'rgba(0, 0, 0, 0)' && color !== 'transparent') {
        const normalized = normalizeColor(color);
        colors.set(normalized, (colors.get(normalized) || 0) + 1);
      }
    });
  });

  // Sort by frequency and group similar colors
  return groupSimilarColors([...colors.entries()].sort((a, b) => b[1] - a[1]));
}

function normalizeColor(color) {
  // Convert all formats to hex
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = color;
  return ctx.fillStyle.toUpperCase();
}

function groupSimilarColors(colors) {
  const groups = [];
  const threshold = 30; // Color distance threshold

  colors.forEach(([color, count]) => {
    const existingGroup = groups.find(g =>
      colorDistance(g.primary, color) < threshold
    );

    if (existingGroup) {
      existingGroup.variations.push({ color, count });
    } else {
      groups.push({
        primary: color,
        count,
        variations: [],
      });
    }
  });

  return groups;
}
```

### Identify Color Roles

```javascript
function identifyColorRoles(colors) {
  const roles = {};

  // Primary is often most used on interactive elements
  const buttons = document.querySelectorAll('button, [role="button"], .btn');
  const buttonColors = new Map();
  buttons.forEach(btn => {
    const bg = normalizeColor(getComputedStyle(btn).backgroundColor);
    buttonColors.set(bg, (buttonColors.get(bg) || 0) + 1);
  });
  roles.primary = [...buttonColors.entries()].sort((a, b) => b[1] - a[1])[0]?.[0];

  // Background is usually body background
  roles.background = normalizeColor(getComputedStyle(document.body).backgroundColor);

  // Text color from body
  roles.text = normalizeColor(getComputedStyle(document.body).color);

  // Muted from secondary text elements
  const mutedElements = document.querySelectorAll('small, .text-muted, .caption');
  if (mutedElements.length) {
    roles.muted = normalizeColor(getComputedStyle(mutedElements[0]).color);
  }

  // Error from error messages or validation
  const errorElements = document.querySelectorAll('.error, [class*="error"], .invalid');
  if (errorElements.length) {
    roles.error = normalizeColor(getComputedStyle(errorElements[0]).color);
  }

  return roles;
}
```

## Typography Extraction

### Extract Font Stack

```javascript
function extractTypography() {
  const fonts = new Map();
  const sizes = new Map();
  const weights = new Map();
  const lineHeights = new Map();

  document.querySelectorAll('*').forEach(el => {
    const style = getComputedStyle(el);

    // Font family
    const family = style.fontFamily.split(',')[0].trim().replace(/['"]/g, '');
    fonts.set(family, (fonts.get(family) || 0) + 1);

    // Font size
    const size = style.fontSize;
    sizes.set(size, (sizes.get(size) || 0) + 1);

    // Font weight
    const weight = style.fontWeight;
    weights.set(weight, (weights.get(weight) || 0) + 1);

    // Line height
    const lh = style.lineHeight;
    lineHeights.set(lh, (lineHeights.get(lh) || 0) + 1);
  });

  return {
    families: sortByCount(fonts),
    sizes: sortByCount(sizes),
    weights: sortByCount(weights),
    lineHeights: sortByCount(lineHeights),
  };
}

function sortByCount(map) {
  return [...map.entries()].sort((a, b) => b[1] - a[1]);
}
```

### Build Type Scale

```javascript
function buildTypeScale() {
  const scale = {};

  // Headings
  for (let i = 1; i <= 6; i++) {
    const heading = document.querySelector(`h${i}`);
    if (heading) {
      const style = getComputedStyle(heading);
      scale[`h${i}`] = {
        fontSize: style.fontSize,
        fontWeight: style.fontWeight,
        lineHeight: style.lineHeight,
        letterSpacing: style.letterSpacing,
        fontFamily: style.fontFamily.split(',')[0].trim(),
      };
    }
  }

  // Body text
  const body = document.querySelector('p, .body');
  if (body) {
    const style = getComputedStyle(body);
    scale.body = {
      fontSize: style.fontSize,
      fontWeight: style.fontWeight,
      lineHeight: style.lineHeight,
      fontFamily: style.fontFamily.split(',')[0].trim(),
    };
  }

  // Small text
  const small = document.querySelector('small, .caption, .text-sm');
  if (small) {
    const style = getComputedStyle(small);
    scale.small = {
      fontSize: style.fontSize,
      fontWeight: style.fontWeight,
      lineHeight: style.lineHeight,
    };
  }

  return scale;
}
```

## Spacing Extraction

### Extract Spacing Values

```javascript
function extractSpacing() {
  const spacings = new Map();

  document.querySelectorAll('*').forEach(el => {
    const style = getComputedStyle(el);

    // Collect all spacing values
    [
      style.padding,
      style.paddingTop,
      style.paddingRight,
      style.paddingBottom,
      style.paddingLeft,
      style.margin,
      style.marginTop,
      style.marginRight,
      style.marginBottom,
      style.marginLeft,
      style.gap,
    ].forEach(value => {
      if (value && value !== '0px') {
        // Parse individual values
        value.split(' ').forEach(v => {
          if (v && v !== '0px') {
            spacings.set(v, (spacings.get(v) || 0) + 1);
          }
        });
      }
    });
  });

  // Convert to scale
  return buildSpacingScale([...spacings.entries()].sort((a, b) => {
    const aNum = parseFloat(a[0]);
    const bNum = parseFloat(b[0]);
    return aNum - bNum;
  }));
}

function buildSpacingScale(spacings) {
  // Find the base unit (most common divisor)
  const values = spacings.map(([v]) => parseFloat(v)).filter(v => v > 0);
  const base = findGCD(values) || 4;

  return {
    base: `${base}px`,
    scale: spacings.map(([value, count]) => ({
      value,
      multiplier: Math.round(parseFloat(value) / base),
      count,
    })),
  };
}
```

## Border Radius Extraction

```javascript
function extractBorderRadius() {
  const radii = new Map();

  document.querySelectorAll('*').forEach(el => {
    const style = getComputedStyle(el);
    const radius = style.borderRadius;

    if (radius && radius !== '0px') {
      radii.set(radius, (radii.get(radius) || 0) + 1);
    }
  });

  return [...radii.entries()]
    .sort((a, b) => parseFloat(a[0]) - parseFloat(b[0]))
    .map(([value, count]) => ({ value, count }));
}
```

## Shadow Extraction

```javascript
function extractShadows() {
  const shadows = new Map();

  document.querySelectorAll('*').forEach(el => {
    const style = getComputedStyle(el);
    const shadow = style.boxShadow;

    if (shadow && shadow !== 'none') {
      shadows.set(shadow, (shadows.get(shadow) || 0) + 1);
    }
  });

  return [...shadows.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([value, count]) => ({ value, count }));
}
```

## Output Format

### Design Tokens JSON

```json
{
  "colors": {
    "primary": "#3B82F6",
    "secondary": "#1F2937",
    "accent": "#F59E0B",
    "background": "#FFFFFF",
    "surface": "#F3F4F6",
    "text": "#111827",
    "muted": "#6B7280",
    "error": "#EF4444",
    "success": "#10B981"
  },
  "typography": {
    "fontFamily": {
      "heading": "Inter, system-ui, sans-serif",
      "body": "Inter, system-ui, sans-serif",
      "mono": "JetBrains Mono, monospace"
    },
    "fontSize": {
      "xs": "12px",
      "sm": "14px",
      "base": "16px",
      "lg": "18px",
      "xl": "20px",
      "2xl": "24px",
      "3xl": "30px",
      "4xl": "36px",
      "5xl": "48px"
    },
    "fontWeight": {
      "normal": "400",
      "medium": "500",
      "semibold": "600",
      "bold": "700"
    },
    "lineHeight": {
      "tight": "1.25",
      "snug": "1.375",
      "normal": "1.5",
      "relaxed": "1.625"
    }
  },
  "spacing": {
    "base": "4px",
    "0": "0",
    "1": "4px",
    "2": "8px",
    "3": "12px",
    "4": "16px",
    "5": "20px",
    "6": "24px",
    "8": "32px",
    "10": "40px",
    "12": "48px",
    "16": "64px"
  },
  "borderRadius": {
    "none": "0",
    "sm": "4px",
    "md": "8px",
    "lg": "12px",
    "xl": "16px",
    "full": "9999px"
  },
  "shadows": {
    "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
    "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
    "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
    "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1)"
  },
  "breakpoints": {
    "sm": "640px",
    "md": "768px",
    "lg": "1024px",
    "xl": "1280px",
    "2xl": "1536px"
  }
}
```

### Tailwind Config

```javascript
// tailwind.config.ts from extracted tokens
export default {
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#3B82F6',
          50: '#EFF6FF',
          100: '#DBEAFE',
          500: '#3B82F6',
          600: '#2563EB',
          700: '#1D4ED8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      spacing: {
        // Uses extracted base unit
      },
    },
  },
};
```

## Best Practices

1. **Sample multiple pages** - Design tokens should be consistent across site
2. **Filter out one-offs** - Only include values used multiple times
3. **Build scales** - Convert raw values to systematic scales
4. **Identify semantic tokens** - Map raw values to semantic names
5. **Check CSS variables** - Many sites already use custom properties
6. **Preserve relationships** - Note how colors are used together
7. **Document responsive behavior** - Extract breakpoints and their effects
