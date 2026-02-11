# Data Validation Patterns

Validate and clean extracted data before storage.

## Schema Validation

Define schemas for extracted data.

### Python (Pydantic)

```python
from pydantic import BaseModel, HttpUrl, field_validator, ValidationError
from typing import Optional
from decimal import Decimal
from datetime import datetime

class Product(BaseModel):
    name: str
    price: Decimal
    url: HttpUrl
    sku: Optional[str] = None
    description: Optional[str] = None
    in_stock: bool = True
    scraped_at: datetime = datetime.now()

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        if len(v) > 500:
            raise ValueError("Name too long")
        return v

    @field_validator("price")
    @classmethod
    def price_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Price must be positive")
        if v > 1_000_000:
            raise ValueError("Price suspiciously high")
        return v

    @field_validator("description")
    @classmethod
    def clean_description(cls, v: Optional[str]) -> Optional[str]:
        if v:
            # Remove extra whitespace
            v = " ".join(v.split())
            # Truncate if too long
            if len(v) > 10000:
                v = v[:10000] + "..."
        return v

# Usage
def validate_product(raw_data: dict) -> Product | None:
    try:
        return Product(**raw_data)
    except ValidationError as e:
        print(f"Validation error: {e}")
        return None
```

### Node.js (Zod)

```typescript
import { z } from 'zod';

const ProductSchema = z.object({
  name: z
    .string()
    .min(1, 'Name cannot be empty')
    .max(500, 'Name too long')
    .transform(s => s.trim()),

  price: z
    .number()
    .positive('Price must be positive')
    .max(1_000_000, 'Price suspiciously high'),

  url: z.string().url('Invalid URL'),

  sku: z.string().optional(),

  description: z
    .string()
    .optional()
    .transform(s => s ? s.split(/\s+/).join(' ').slice(0, 10000) : undefined),

  inStock: z.boolean().default(true),

  scrapedAt: z.date().default(() => new Date()),
});

type Product = z.infer<typeof ProductSchema>;

function validateProduct(rawData: unknown): Product | null {
  const result = ProductSchema.safeParse(rawData);
  if (result.success) {
    return result.data;
  }
  console.error('Validation error:', result.error);
  return null;
}
```

## Data Cleaning

Clean common data issues.

### Python

```python
import re
from decimal import Decimal
from datetime import datetime
from typing import Optional

class DataCleaner:
    @staticmethod
    def clean_text(text: str | None) -> str:
        """Clean text: normalize whitespace, strip."""
        if not text:
            return ""
        # Normalize whitespace
        text = " ".join(text.split())
        # Remove zero-width characters
        text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
        return text.strip()

    @staticmethod
    def parse_price(text: str) -> Decimal | None:
        """Parse price from various formats."""
        if not text:
            return None

        # Remove currency symbols and text
        text = re.sub(r"[^\d.,]", "", text)

        # Handle European format (1.234,56)
        if "," in text and "." in text:
            if text.rindex(",") > text.rindex("."):
                # European: 1.234,56
                text = text.replace(".", "").replace(",", ".")
            else:
                # US: 1,234.56
                text = text.replace(",", "")
        elif "," in text:
            # Could be 1,234 or 1,23
            parts = text.split(",")
            if len(parts[-1]) == 2:
                text = text.replace(",", ".")
            else:
                text = text.replace(",", "")

        try:
            return Decimal(text)
        except:
            return None

    @staticmethod
    def parse_date(text: str) -> datetime | None:
        """Parse date from common formats."""
        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%B %d, %Y",
            "%d %B %Y",
            "%Y-%m-%dT%H:%M:%S",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(text.strip(), fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def parse_boolean(text: str) -> bool:
        """Parse boolean from text."""
        truthy = {"true", "yes", "1", "in stock", "available"}
        return text.lower().strip() in truthy
```

### Node.js

```typescript
class DataCleaner {
  static cleanText(text: string | null): string {
    if (!text) return '';
    // Normalize whitespace
    return text.split(/\s+/).join(' ').trim();
  }

  static parsePrice(text: string): number | null {
    if (!text) return null;

    // Remove currency symbols
    let cleaned = text.replace(/[^\d.,]/g, '');

    // Handle European format
    if (cleaned.includes(',') && cleaned.includes('.')) {
      if (cleaned.lastIndexOf(',') > cleaned.lastIndexOf('.')) {
        cleaned = cleaned.replace(/\./g, '').replace(',', '.');
      } else {
        cleaned = cleaned.replace(/,/g, '');
      }
    } else if (cleaned.includes(',')) {
      const parts = cleaned.split(',');
      if (parts[parts.length - 1].length === 2) {
        cleaned = cleaned.replace(',', '.');
      } else {
        cleaned = cleaned.replace(/,/g, '');
      }
    }

    const num = parseFloat(cleaned);
    return isNaN(num) ? null : num;
  }

  static parseBoolean(text: string): boolean {
    const truthy = ['true', 'yes', '1', 'in stock', 'available'];
    return truthy.includes(text.toLowerCase().trim());
  }
}
```

## Deduplication

Remove duplicate items.

### Python

```python
from typing import Iterator, TypeVar
from hashlib import sha256

T = TypeVar("T")

class Deduplicator:
    def __init__(self, key_fields: list[str]):
        self.key_fields = key_fields
        self.seen: set[str] = set()

    def get_key(self, item: dict) -> str:
        """Generate unique key from item fields."""
        values = [str(item.get(f, "")) for f in self.key_fields]
        return sha256("|".join(values).encode()).hexdigest()

    def dedupe(self, items: Iterator[dict]) -> Iterator[dict]:
        """Yield only unique items."""
        for item in items:
            key = self.get_key(item)
            if key not in self.seen:
                self.seen.add(key)
                yield item

# Usage
deduper = Deduplicator(key_fields=["sku", "name"])
unique_products = list(deduper.dedupe(all_products))
```

## Validation Pipeline

Chain validation steps.

### Python

```python
from dataclasses import dataclass
from typing import Any, Callable

@dataclass
class ValidationResult:
    valid: bool
    data: Any | None
    errors: list[str]

class ValidationPipeline:
    def __init__(self):
        self.validators: list[Callable] = []

    def add(self, validator: Callable):
        self.validators.append(validator)
        return self

    def validate(self, data: dict) -> ValidationResult:
        errors = []
        current = data.copy()

        for validator in self.validators:
            try:
                current = validator(current)
            except Exception as e:
                errors.append(str(e))

        return ValidationResult(
            valid=len(errors) == 0,
            data=current if not errors else None,
            errors=errors,
        )

# Usage
pipeline = ValidationPipeline()
pipeline.add(lambda d: {**d, "name": d["name"].strip()})
pipeline.add(lambda d: {**d, "price": DataCleaner.parse_price(d["price"])})
pipeline.add(lambda d: Product(**d).model_dump())

result = pipeline.validate(raw_data)
if result.valid:
    save(result.data)
else:
    log_errors(result.errors)
```

## Quality Metrics

Track data quality.

```python
from dataclasses import dataclass, field
from typing import Counter

@dataclass
class QualityMetrics:
    total_items: int = 0
    valid_items: int = 0
    invalid_items: int = 0
    field_errors: Counter = field(default_factory=Counter)

    @property
    def validity_rate(self) -> float:
        if self.total_items == 0:
            return 0
        return self.valid_items / self.total_items

    def record(self, is_valid: bool, errors: list[str] = None):
        self.total_items += 1
        if is_valid:
            self.valid_items += 1
        else:
            self.invalid_items += 1
            for error in errors or []:
                # Extract field name from error
                self.field_errors[error.split(":")[0]] += 1

    def report(self) -> str:
        return f"""
Data Quality Report
-------------------
Total items: {self.total_items}
Valid: {self.valid_items} ({self.validity_rate:.1%})
Invalid: {self.invalid_items}

Top field errors:
{chr(10).join(f"  {k}: {v}" for k, v in self.field_errors.most_common(5))}
"""
```

## Best Practices

1. **Validate early** - Check data before processing
2. **Fail fast** - Reject bad data immediately
3. **Log errors** - Track validation failures for debugging
4. **Define schemas** - Use typed schemas, not ad-hoc validation
5. **Handle nulls** - Define behavior for missing fields
6. **Monitor quality** - Track validity rates over time
