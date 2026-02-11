# /new-scraper

Generate a standalone scraper for HTTP-based or browser-based data extraction.

## Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `name` | Scraper name (e.g., `product-details`, `search-results`) | Yes |
| `--url` | Target URL to scrape | No |
| `--browser` | Use browser automation: `playwright`, `puppeteer`, `none` | No |
| `--auth` | Authentication type: `none`, `cookie`, `login`, `api-key` | No |
| `--output` | Output format: `json`, `csv`, `database` | No |

## Examples

```bash
/new-scraper product-details --url https://example.com/product/123
/new-scraper search-results --browser playwright
/new-scraper api-data --auth api-key --output json
```

## Generated Files

{% if variables.language == 'Python' %}
```
scrapers/
├── scrapers/
│   └── {{ name }}_scraper.py
├── extractors/
│   └── {{ name }}_extractor.py
├── pipelines/
│   └── {{ name }}_pipeline.py
└── tests/
    └── test_{{ name }}_scraper.py
```

### HTTP Scraper Template

```python
import httpx
from bs4 import BeautifulSoup
from typing import TypeVar, Generic, List
from pydantic import BaseModel
import asyncio
import random

T = TypeVar("T", bound=BaseModel)

class {{ Name }}Scraper(Generic[T]):
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            headers=self._get_headers(),
            timeout=30.0,
            follow_redirects=True,
        )

    async def scrape(self, path: str) -> List[T]:
        url = f"{self.base_url}{path}"
        response = await self.client.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        return self._extract(soup)

    async def scrape_with_retry(self, path: str, max_retries: int = 3) -> List[T]:
        for attempt in range(max_retries):
            try:
                return await self.scrape(path)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    await asyncio.sleep(2 ** attempt + random.random())
                    continue
                raise
        raise Exception(f"Failed after {max_retries} attempts")

    def _extract(self, soup: BeautifulSoup) -> List[T]:
        raise NotImplementedError("Subclass must implement _extract")

    def _get_headers(self) -> dict:
        return {
            "User-Agent": "Mozilla/5.0 (compatible; MyScraper/1.0)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def close(self):
        await self.client.aclose()
```

### Browser Scraper Template (if --browser)

```python
from playwright.async_api import async_playwright, Browser, Page
from typing import List
import asyncio

class {{ Name }}BrowserScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Browser | None = None

    async def __aenter__(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        return self

    async def __aexit__(self, *args):
        if self.browser:
            await self.browser.close()

    async def scrape(self, url: str) -> dict:
        context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()

        # Block unnecessary resources
        await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2}", lambda r: r.abort())

        await page.goto(url, wait_until="networkidle")

        # Wait for dynamic content
        await page.wait_for_selector(".content", timeout=10000)

        # Extract data
        data = await page.evaluate(self._extraction_script())

        await context.close()
        return data

    def _extraction_script(self) -> str:
        return """
        () => {
            return {
                title: document.querySelector('h1')?.textContent?.trim(),
                // Add more extraction logic
            };
        }
        """
```

{% else %}
```
scrapers/
├── src/
│   ├── scrapers/
│   │   └── {{ name }}.ts
│   └── extractors/
│       └── {{ name }}Extractor.ts
└── tests/
    └── {{ name }}.test.ts
```

### HTTP Scraper Template

```typescript
import axios, { AxiosInstance } from 'axios';
import * as cheerio from 'cheerio';

export class {{ Name }}Scraper<T> {
  private client: AxiosInstance;
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    this.client = axios.create({
      baseURL: baseUrl,
      timeout: 30000,
      headers: this.getHeaders(),
    });
  }

  async scrape(path: string): Promise<T[]> {
    const response = await this.client.get(path);
    const $ = cheerio.load(response.data);
    return this.extract($);
  }

  async scrapeWithRetry(path: string, maxRetries = 3): Promise<T[]> {
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        return await this.scrape(path);
      } catch (error: any) {
        if (error.response?.status === 429) {
          await this.sleep(Math.pow(2, attempt) * 1000 + Math.random() * 1000);
          continue;
        }
        throw error;
      }
    }
    throw new Error(`Failed after ${maxRetries} attempts`);
  }

  protected extract($: cheerio.CheerioAPI): T[] {
    throw new Error('Subclass must implement extract');
  }

  private getHeaders(): Record<string, string> {
    return {
      'User-Agent': 'Mozilla/5.0 (compatible; MyScraper/1.0)',
      'Accept': 'text/html,application/xhtml+xml',
      'Accept-Language': 'en-US,en;q=0.9',
    };
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

### Browser Scraper Template (if --browser)

```typescript
import { chromium, Browser, BrowserContext } from 'playwright';

export class {{ Name }}BrowserScraper {
  private browser: Browser | null = null;

  async init(): Promise<void> {
    this.browser = await chromium.launch({ headless: true });
  }

  async close(): Promise<void> {
    await this.browser?.close();
  }

  async scrape(url: string): Promise<any> {
    if (!this.browser) throw new Error('Browser not initialized');

    const context = await this.browser.newContext({
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      viewport: { width: 1920, height: 1080 },
    });

    const page = await context.newPage();

    // Block unnecessary resources
    await page.route('**/*.{png,jpg,jpeg,gif,svg,woff,woff2}', route => route.abort());

    await page.goto(url, { waitUntil: 'networkidle' });

    // Wait for dynamic content
    await page.waitForSelector('.content', { timeout: 10000 });

    // Extract data
    const data = await page.evaluate(() => ({
      title: document.querySelector('h1')?.textContent?.trim(),
      // Add more extraction logic
    }));

    await context.close();
    return data;
  }
}
```
{% endif %}

## Implementation Steps

1. **Create scraper class** with HTTP client or browser setup
2. **Implement extraction logic** based on target page analysis
3. **Add retry logic** with exponential backoff
4. **Create pipeline** for data transformation
5. **Write tests** with mocked responses
6. **Verify with sample URLs**

## Self-Verification

After generation, verify:

- [ ] Scraper initializes without errors
- [ ] HTTP client configured with proper headers
- [ ] Retry logic handles rate limiting
- [ ] Extraction returns valid data
- [ ] Browser properly closes (if used)
- [ ] Tests pass
