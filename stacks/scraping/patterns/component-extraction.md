# Component Extraction Pattern

Patterns for identifying and extracting reusable UI components from websites.

## Component Detection

### Semantic Selectors

Prefer stable, semantic selectors over generated class names:

```javascript
// GOOD - Semantic and stable
'[data-testid="product-card"]'
'[role="button"]'
'article.product'
'.product-card'

// BAD - Generated/volatile
'.css-1a2b3c4d'
'.sc-bdVaJa'
'div:nth-child(3) > div:nth-child(2)'
```

### Component Identification

Look for repeated patterns:

```javascript
// Find repeated structures
const findComponents = () => {
  const patterns = {};

  // Look for elements with similar class patterns
  document.querySelectorAll('*').forEach(el => {
    const key = el.className.split(' ')
      .filter(c => c.length > 3 && !c.match(/^(css|sc)-/))
      .sort()
      .join('|');

    if (key) {
      patterns[key] = (patterns[key] || 0) + 1;
    }
  });

  // Return patterns that appear multiple times (likely components)
  return Object.entries(patterns)
    .filter(([_, count]) => count >= 2)
    .sort((a, b) => b[1] - a[1]);
};
```

### Common Component Types

| Type | Selectors | Props to Extract |
|------|-----------|------------------|
| Card | `.card`, `[class*="Card"]`, `article` | title, image, description, link |
| Button | `button`, `[role="button"]`, `.btn` | text, variant, size, disabled |
| Input | `input`, `textarea`, `select` | type, placeholder, label, required |
| Modal | `[role="dialog"]`, `.modal` | title, content, actions |
| Table | `table`, `[role="grid"]` | headers, rows, sortable |
| Form | `form` | fields, action, method |

## Prop Extraction

### Extract Component Props

```javascript
function extractCardProps(element) {
  return {
    title: element.querySelector('h2, h3, [class*="title"]')?.textContent?.trim(),
    image: element.querySelector('img')?.src,
    description: element.querySelector('p, [class*="description"]')?.textContent?.trim(),
    link: element.querySelector('a')?.href,
    price: parsePrice(element.querySelector('[class*="price"]')?.textContent),
    badge: element.querySelector('[class*="badge"]')?.textContent?.trim(),
  };
}

function parsePrice(text) {
  if (!text) return null;
  const match = text.match(/[\d,]+\.?\d*/);
  return match ? parseFloat(match[0].replace(',', '')) : null;
}
```

### Variant Detection

```javascript
function detectButtonVariants(buttons) {
  const variants = new Map();

  buttons.forEach(btn => {
    const classes = [...btn.classList];
    const style = getComputedStyle(btn);

    const variant = {
      background: style.backgroundColor,
      color: style.color,
      border: style.border,
      padding: style.padding,
      borderRadius: style.borderRadius,
    };

    const key = JSON.stringify(variant);
    if (!variants.has(key)) {
      variants.set(key, {
        style: variant,
        classes: classes.filter(c => c.includes('btn') || c.includes('button')),
        count: 0,
      });
    }
    variants.get(key).count++;
  });

  return [...variants.values()].sort((a, b) => b.count - a.count);
}
```

## Component Hierarchy

### Extract Parent-Child Relationships

```javascript
function buildComponentTree(root) {
  const tree = {
    tag: root.tagName.toLowerCase(),
    classes: [...root.classList],
    role: root.getAttribute('role'),
    children: [],
  };

  // Only include meaningful children
  root.children.forEach(child => {
    if (isSignificantElement(child)) {
      tree.children.push(buildComponentTree(child));
    }
  });

  return tree;
}

function isSignificantElement(el) {
  // Skip empty divs and spans
  if (['DIV', 'SPAN'].includes(el.tagName) &&
      !el.className &&
      !el.id &&
      el.children.length === 0) {
    return false;
  }
  return true;
}
```

## State Detection

### Interactive States

```javascript
function detectInteractiveStates(element) {
  const states = [];

  // Check for hover styles
  const originalBg = getComputedStyle(element).backgroundColor;
  element.dispatchEvent(new MouseEvent('mouseenter'));
  const hoverBg = getComputedStyle(element).backgroundColor;
  if (originalBg !== hoverBg) {
    states.push({ trigger: 'hover', changes: { backgroundColor: hoverBg } });
  }
  element.dispatchEvent(new MouseEvent('mouseleave'));

  // Check for focus styles
  if (element.focus) {
    element.focus();
    const focusBorder = getComputedStyle(element).outline;
    if (focusBorder !== 'none') {
      states.push({ trigger: 'focus', changes: { outline: focusBorder } });
    }
    element.blur();
  }

  return states;
}
```

## Output Format

### Component Definition

```typescript
interface ExtractedComponent {
  name: string;
  type: 'ui' | 'section' | 'layout';
  instances: number;
  selector: string;
  props: PropDefinition[];
  variants: Variant[];
  states: InteractiveState[];
  children: string[];
  styles: StyleTokens;
}

interface PropDefinition {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'image' | 'link';
  required: boolean;
  selector: string;
}

interface Variant {
  name: string;
  classes: string[];
  styles: Record<string, string>;
}
```

### Example Output

```json
{
  "name": "ProductCard",
  "type": "ui",
  "instances": 12,
  "selector": ".product-card, [data-component=\"product\"]",
  "props": [
    {"name": "title", "type": "string", "required": true, "selector": "h3"},
    {"name": "price", "type": "number", "required": true, "selector": ".price"},
    {"name": "image", "type": "image", "required": true, "selector": "img"},
    {"name": "inStock", "type": "boolean", "required": false, "selector": ".in-stock"}
  ],
  "variants": [
    {"name": "default", "classes": ["product-card"]},
    {"name": "featured", "classes": ["product-card", "featured"]},
    {"name": "compact", "classes": ["product-card", "compact"]}
  ],
  "states": [
    {"trigger": "hover", "changes": {"boxShadow": "0 4px 12px rgba(0,0,0,0.15)"}}
  ],
  "children": ["Badge", "Button"],
  "styles": {
    "borderRadius": "8px",
    "padding": "16px",
    "background": "#ffffff"
  }
}
```

## Best Practices

1. **Prefer data attributes** - `data-testid`, `data-component` are stable
2. **Use semantic elements** - `article`, `nav`, `aside` indicate purpose
3. **Check ARIA roles** - `role="button"`, `role="dialog"` reveal intent
4. **Analyze class naming** - BEM patterns reveal component structure
5. **Count instances** - More instances = more likely to be a component
6. **Extract all variants** - Different sizes, colors, states
7. **Document dependencies** - What other components are used inside
