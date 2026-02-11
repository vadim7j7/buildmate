# Node.js Web Scraping Style Guide

Conventions for Node.js-based web scrapers.

## Project Structure

```
project/
├── src/
│   ├── spiders/
│   │   ├── index.ts
│   │   └── products.ts
│   ├── extractors/
│   │   ├── index.ts
│   │   └── productExtractor.ts
│   ├── pipelines/
│   │   ├── index.ts
│   │   ├── clean.ts
│   │   └── validate.ts
│   ├── utils/
│   │   ├── rateLimiter.ts
│   │   ├── userAgents.ts
│   │   └── proxy.ts
│   └── types/
│       └── product.ts
├── tests/
│   ├── spiders.test.ts
│   └── fixtures/
│       └── samplePage.html
├── package.json
├── tsconfig.json
└── jest.config.js
```

## Code Style

### TypeScript

Always use TypeScript with strict mode:

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "esModuleInterop": true,
    "outDir": "./dist"
  }
}
```

### Type Definitions

Define interfaces for scraped data:

```typescript
// types/product.ts
export interface Product {
  name: string;
  price: number;
  url: string;
  sku?: string;
  inStock: boolean;
  scrapedAt: Date;
}

export interface ScraperOptions {
  baseUrl: string;
  delay?: number;
  maxRetries?: number;
  userAgent?: string;
}
```

### Zod Validation

Use Zod for runtime validation:

```typescript
import { z } from 'zod';

export const ProductSchema = z.object({
  name: z.string().min(1).transform(s => s.trim()),
  price: z
    .string()
    .transform(s => parseFloat(s.replace(/[^\d.]/g, '')))
    .pipe(z.number().positive()),
  url: z.string().url(),
  sku: z.string().optional(),
  inStock: z.boolean().default(true),
  scrapedAt: z.date().default(() => new Date()),
});

export type Product = z.infer<typeof ProductSchema>;
```

### Async Generators

Use async generators for pagination:

```typescript
async function* scrapeAllPages(baseUrl: string): AsyncGenerator<Product> {
  let page = 1;

  while (true) {
    const products = await scrapePage(`${baseUrl}?page=${page}`);
    if (products.length === 0) break;

    for (const product of products) {
      yield product;
    }
    page++;
  }
}

// Usage
for await (const product of scrapeAllPages('/products')) {
  console.log(product);
}
```

### Error Handling

Use custom error classes:

```typescript
export class ScraperError extends Error {
  constructor(message: string, public readonly url?: string) {
    super(message);
    this.name = 'ScraperError';
  }
}

export class ExtractionError extends ScraperError {
  constructor(message: string, public readonly selector?: string) {
    super(message);
    this.name = 'ExtractionError';
  }
}

export class RateLimitError extends ScraperError {
  constructor(public readonly retryAfter?: number) {
    super('Rate limited');
    this.name = 'RateLimitError';
  }
}
```

## HTTP Client Configuration

### Axios Setup

```typescript
import axios, { AxiosInstance } from 'axios';

function createClient(baseUrl: string): AxiosInstance {
  return axios.create({
    baseURL: baseUrl,
    timeout: 30000,
    headers: {
      'User-Agent': 'Mozilla/5.0 ...',
      'Accept': 'text/html,application/xhtml+xml',
      'Accept-Language': 'en-US,en;q=0.9',
    },
    maxRedirects: 5,
    validateStatus: status => status < 500,
  });
}
```

### Fetch with retry

```typescript
async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  retries = 3
): Promise<Response> {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url, {
        ...options,
        signal: AbortSignal.timeout(30000),
      });

      if (response.ok) return response;

      if (response.status === 429) {
        const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
        await sleep(retryAfter * 1000);
        continue;
      }

      throw new Error(`HTTP ${response.status}`);
    } catch (error) {
      if (i === retries - 1) throw error;
      await sleep(Math.pow(2, i) * 1000);
    }
  }
  throw new Error('Max retries exceeded');
}
```

## Selector Style

### Cheerio

Use CSS selectors consistently:

```typescript
import * as cheerio from 'cheerio';

function extractProducts($: cheerio.CheerioAPI): Product[] {
  const products: Product[] = [];

  $('.product-card').each((_, element) => {
    const $el = $(element);
    products.push({
      name: $el.find('.product-name').text().trim(),
      price: parsePrice($el.find('.price').text()),
      url: $el.find('a').attr('href') || '',
      sku: $el.attr('data-sku'),
      inStock: $el.hasClass('in-stock'),
      scrapedAt: new Date(),
    });
  });

  return products;
}
```

### Safe Extraction

Handle missing elements gracefully:

```typescript
function safeText($: cheerio.CheerioAPI, selector: string): string | null {
  const el = $(selector);
  return el.length > 0 ? el.text().trim() : null;
}

function safeAttr(
  $: cheerio.CheerioAPI,
  selector: string,
  attr: string
): string | null {
  const el = $(selector);
  return el.length > 0 ? (el.attr(attr) ?? null) : null;
}

function requireText($: cheerio.CheerioAPI, selector: string): string {
  const text = safeText($, selector);
  if (!text) throw new ExtractionError(`Missing: ${selector}`, selector);
  return text;
}
```

## Class-Based Scrapers

```typescript
export abstract class BaseScraper<T> {
  protected client: AxiosInstance;
  protected rateLimiter: RateLimiter;

  constructor(protected options: ScraperOptions) {
    this.client = createClient(options.baseUrl);
    this.rateLimiter = new RateLimiter(options.delay ?? 2000);
  }

  abstract extract($: cheerio.CheerioAPI): T[];

  async scrape(path: string): Promise<T[]> {
    await this.rateLimiter.wait();
    const response = await this.client.get(path);
    const $ = cheerio.load(response.data);
    return this.extract($);
  }

  async *scrapeAll(paths: string[]): AsyncGenerator<T> {
    for (const path of paths) {
      const items = await this.scrape(path);
      for (const item of items) {
        yield item;
      }
    }
  }
}

// Implementation
export class ProductScraper extends BaseScraper<Product> {
  extract($: cheerio.CheerioAPI): Product[] {
    return extractProducts($);
  }
}
```

## Logging

Use pino for structured logging:

```typescript
import pino from 'pino';

const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  transport: {
    target: 'pino-pretty',
    options: { colorize: true },
  },
});

// Usage
logger.info({ url, itemsCount: items.length }, 'Page scraped');
logger.error({ url, error: err.message }, 'Scrape failed');
```

## Testing

### Jest Setup

```javascript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  testMatch: ['**/tests/**/*.test.ts'],
  collectCoverageFrom: ['src/**/*.ts'],
  coverageThreshold: {
    global: { branches: 80, functions: 80, lines: 80 },
  },
};
```

### Mocking HTTP

Use nock for HTTP mocking:

```typescript
import nock from 'nock';
import { ProductScraper } from '../src/spiders/products';

describe('ProductScraper', () => {
  afterEach(() => {
    nock.cleanAll();
  });

  it('extracts products from listing page', async () => {
    nock('https://example.com')
      .get('/products')
      .replyWithFile(200, 'tests/fixtures/listing.html', {
        'Content-Type': 'text/html',
      });

    const scraper = new ProductScraper({ baseUrl: 'https://example.com' });
    const products = await scraper.scrape('/products');

    expect(products).toHaveLength(3);
    expect(products[0].name).toBe('Test Product');
  });
});
```

## Dependencies

### package.json

```json
{
  "name": "my-scraper",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "build": "tsc",
    "test": "jest",
    "lint": "eslint src/",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "axios": "^1.6.0",
    "cheerio": "^1.0.0-rc.12",
    "zod": "^3.22.0",
    "pino": "^8.17.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.3.0",
    "jest": "^29.7.0",
    "ts-jest": "^29.1.0",
    "@types/jest": "^29.5.0",
    "nock": "^13.4.0",
    "eslint": "^8.56.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0"
  },
  "optionalDependencies": {
    "playwright": "^1.40.0"
  }
}
```

## Quality Gates

```bash
# Linting
npm run lint
npm run lint -- --fix

# Type checking
npm run typecheck

# Tests
npm test

# With coverage
npm test -- --coverage
```

## Anti-Patterns to Avoid

```typescript
// Bad: any types
const data: any = response.data;

// Bad: No error handling
const response = await axios.get(url);

// Bad: Callback hell
axios.get(url).then(response => {
  // ...
});

// Bad: No timeout
await fetch(url);

// Bad: Swallowing errors
try {
  await scrape(url);
} catch {
  // Silent failure
}
```

## Recommended Libraries

| Purpose | Library |
|---------|---------|
| HTTP Client | axios, got, node-fetch |
| HTML Parsing | cheerio |
| Validation | zod |
| Browser | playwright, puppeteer |
| Logging | pino |
| Testing | jest, nock |
| Types | typescript |
| Linting | eslint |
