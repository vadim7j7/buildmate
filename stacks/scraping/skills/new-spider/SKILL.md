# /new-spider

Generate a new Scrapy spider (Python) or structured scraper class.

## Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `name` | Spider/scraper name (e.g., `products`, `listings`) | Yes |
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

{% if variables.language == 'Python' %}
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

{% else %}
### Node.js

```
scrapers/
├── src/
│   └── spiders/
│       └── {{ name }}.ts       # Scraper class
└── tests/
    └── {{ name }}.test.ts
```

### Spider Template

```typescript
import axios from 'axios';
import * as cheerio from 'cheerio';
import { z } from 'zod';

const {{ Name }}Schema = z.object({
  name: z.string().min(1),
  price: z.number().positive(),
  url: z.string().url(),
  description: z.string().optional(),
});

type {{ Name }} = z.infer<typeof {{ Name }}Schema>;

export class {{ Name }}Spider {
  private baseUrl: string;
  private delay: number = 2000;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async scrape(path: string): Promise<{{ Name }}[]> {
    const items: {{ Name }}[] = [];
    let currentUrl = `${this.baseUrl}${path}`;

    while (currentUrl) {
      const response = await axios.get(currentUrl);
      const $ = cheerio.load(response.data);

      $('.item').each((_, element) => {
        const rawItem = {
          name: $(element).find('.name').text().trim(),
          price: this.parsePrice($(element).find('.price').text()),
          url: new URL($(element).find('a').attr('href') || '', this.baseUrl).href,
        };

        const item = {{ Name }}Schema.parse(rawItem);
        items.push(item);
      });

      // Handle pagination
      const nextHref = $('a.next').attr('href');
      currentUrl = nextHref ? new URL(nextHref, this.baseUrl).href : '';

      if (currentUrl) {
        await this.sleep(this.delay);
      }
    }

    return items;
  }

  private parsePrice(text: string): number {
    const clean = text.replace(/[^\d.]/g, '');
    return parseFloat(clean) || 0;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```
{% endif %}

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
