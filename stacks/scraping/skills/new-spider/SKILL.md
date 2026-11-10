---
name: new-spider
description: Generate a Scrapy spider with items, pipeline and tests
---

# /new-spider

> **Scrapy is Python-only**, so this skill is installed only with `--language=python`.
> Node.js projects use `/new-scraper` instead.

Generate a new Scrapy spider with its item definition and tests.

## Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `name` | Spider name (e.g., `products`, `listings`) | Yes |
| `--url` | Target base URL to scrape | No |
| `--type` | Spider type: `crawl`, `sitemap`, `api` | No |
| `--pagination` | Pagination type: `url`, `infinite`, `load-more` | No |

## Examples

```bash
/new-spider products --url https://example.com/products
/new-spider listings --type crawl --pagination url
/new-spider api-scraper --type api
```

## Generated Files

### Python (Scrapy)

```
scrapers/
├── spiders/
│   └── {{ name }}_spider.py    # Scrapy spider class
├── items/
│   └── {{ name }}.py           # Item definition
└── tests/
    └── test_{{ name }}_spider.py
```

### Spider Template

```python
import scrapy
from scrapy.http import Response
from typing import Iterator
from items.{{ name }} import {{ Name }}Item

class {{ Name }}Spider(scrapy.Spider):
    name = "{{ name }}"
    allowed_domains = ["example.com"]
    start_urls = ["https://example.com/{{ name }}"]

    custom_settings = {
        "DOWNLOAD_DELAY": 2,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
    }

    def parse(self, response: Response) -> Iterator[{{ Name }}Item]:
        for item in response.css(".item"):
            yield {{ Name }}Item(
                name=item.css(".name::text").get(),
                price=item.css(".price::text").get(),
                url=response.urljoin(item.css("a::attr(href)").get()),
            )

        # Handle pagination
        next_page = response.css("a.next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
```

### Item Template

```python
from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional

class {{ Name }}Item(BaseModel):
    name: str
    price: float
    url: HttpUrl
    description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("price", mode="before")
    @classmethod
    def parse_price(cls, v: str) -> float:
        # Remove currency symbols and convert
        import re
        clean = re.sub(r"[^\d.]", "", str(v))
        return float(clean) if clean else 0.0
```

## Implementation Steps

1. **Create spider file** with proper class structure
2. **Define item schema** with validation
3. **Implement selectors** based on target URL analysis
4. **Add pagination handling** if applicable
5. **Create test file** with mocked responses
6. **Run quality gates** to verify

## Self-Verification

After generation, verify:

- [ ] Spider starts without errors
- [ ] Selectors match target page structure
- [ ] Pagination follows all pages
- [ ] Items validate correctly
- [ ] Tests pass with mock data
