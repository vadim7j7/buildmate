# Pagination Patterns

Handle different pagination mechanisms when scraping multi-page content.

## URL Parameter Pagination

The most common pattern: `?page=1`, `?page=2`, etc.

### Python

```python
from typing import Iterator, TypeVar
import httpx

T = TypeVar("T")

async def paginate_url_params(
    client: httpx.AsyncClient,
    base_url: str,
    extractor: callable,
    param_name: str = "page",
    start_page: int = 1,
) -> Iterator[T]:
    """Iterate through pages using URL parameters."""
    page = start_page

    while True:
        url = f"{base_url}?{param_name}={page}"
        response = await client.get(url)

        if response.status_code == 404:
            break

        items = extractor(response.text)
        if not items:
            break

        for item in items:
            yield item

        page += 1

# Usage
async for product in paginate_url_params(client, "/products", extract_products):
    print(product)
```

### Node.js

```typescript
async function* paginateUrlParams<T>(
  baseUrl: string,
  extractor: (html: string) => T[],
  paramName = 'page',
  startPage = 1
): AsyncGenerator<T> {
  let page = startPage;

  while (true) {
    const url = `${baseUrl}?${paramName}=${page}`;
    const response = await axios.get(url);

    if (response.status === 404) break;

    const items = extractor(response.data);
    if (items.length === 0) break;

    for (const item of items) {
      yield item;
    }

    page++;
  }
}

// Usage
for await (const product of paginateUrlParams('/products', extractProducts)) {
  console.log(product);
}
```

## Next Button Navigation

Follow "Next" links until they disappear.

### Python

```python
from bs4 import BeautifulSoup
from urllib.parse import urljoin

async def paginate_next_button(
    client: httpx.AsyncClient,
    start_url: str,
    extractor: callable,
    next_selector: str = "a.next",
) -> Iterator[T]:
    """Follow next button links."""
    url = start_url

    while url:
        response = await client.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        items = extractor(soup)
        for item in items:
            yield item

        # Find next page link
        next_link = soup.select_one(next_selector)
        url = urljoin(start_url, next_link["href"]) if next_link else None
```

### Node.js

```typescript
async function* paginateNextButton<T>(
  startUrl: string,
  extractor: ($: cheerio.CheerioAPI) => T[],
  nextSelector = 'a.next'
): AsyncGenerator<T> {
  let url: string | null = startUrl;

  while (url) {
    const response = await axios.get(url);
    const $ = cheerio.load(response.data);

    const items = extractor($);
    for (const item of items) {
      yield item;
    }

    const nextHref = $(nextSelector).attr('href');
    url = nextHref ? new URL(nextHref, startUrl).href : null;
  }
}
```

## Infinite Scroll

Handle JavaScript-powered infinite scroll.

### Python (Playwright)

```python
from playwright.async_api import Page

async def scrape_infinite_scroll(
    page: Page,
    item_selector: str,
    max_scrolls: int = 50,
    scroll_delay: float = 2.0,
) -> list:
    """Scroll down until no new items appear."""
    items = []
    previous_count = 0
    scroll_count = 0

    while scroll_count < max_scrolls:
        # Get current items
        elements = await page.query_selector_all(item_selector)
        current_count = len(elements)

        if current_count == previous_count:
            # No new items loaded
            break

        previous_count = current_count

        # Scroll to bottom
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(scroll_delay * 1000)

        scroll_count += 1

    # Extract all items
    elements = await page.query_selector_all(item_selector)
    for element in elements:
        items.append(await element.inner_text())

    return items
```

### Node.js (Playwright)

```typescript
async function scrapeInfiniteScroll(
  page: Page,
  itemSelector: string,
  maxScrolls = 50,
  scrollDelay = 2000
): Promise<string[]> {
  let previousCount = 0;
  let scrollCount = 0;

  while (scrollCount < maxScrolls) {
    const elements = await page.$$(itemSelector);
    const currentCount = elements.length;

    if (currentCount === previousCount) break;

    previousCount = currentCount;

    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(scrollDelay);

    scrollCount++;
  }

  const elements = await page.$$(itemSelector);
  return Promise.all(elements.map(el => el.innerText()));
}
```

## Load More Button

Click "Load More" button repeatedly.

### Python (Playwright)

```python
async def scrape_load_more(
    page: Page,
    button_selector: str,
    item_selector: str,
    max_clicks: int = 100,
) -> list:
    """Click load more button until it disappears."""
    clicks = 0

    while clicks < max_clicks:
        button = await page.query_selector(button_selector)
        if not button:
            break

        await button.click()
        await page.wait_for_load_state("networkidle")
        clicks += 1

    elements = await page.query_selector_all(item_selector)
    return [await el.inner_text() for el in elements]
```

## Cursor-Based Pagination

Handle API cursor pagination (common in modern APIs).

### Python

```python
import httpx
from typing import Iterator

async def paginate_cursor(
    client: httpx.AsyncClient,
    base_url: str,
    cursor_field: str = "next_cursor",
) -> Iterator[dict]:
    """Handle cursor-based API pagination."""
    cursor = None

    while True:
        params = {"cursor": cursor} if cursor else {}
        response = await client.get(base_url, params=params)
        data = response.json()

        for item in data.get("items", []):
            yield item

        cursor = data.get(cursor_field)
        if not cursor:
            break
```

### Node.js

```typescript
async function* paginateCursor(
  baseUrl: string,
  cursorField = 'next_cursor'
): AsyncGenerator<any> {
  let cursor: string | null = null;

  while (true) {
    const params = cursor ? { cursor } : {};
    const response = await axios.get(baseUrl, { params });
    const data = response.data;

    for (const item of data.items || []) {
      yield item;
    }

    cursor = data[cursorField];
    if (!cursor) break;
  }
}
```

## Offset Pagination

Handle `?offset=0&limit=100` style pagination.

### Python

```python
async def paginate_offset(
    client: httpx.AsyncClient,
    base_url: str,
    limit: int = 100,
) -> Iterator[dict]:
    """Handle offset-based pagination."""
    offset = 0

    while True:
        response = await client.get(
            base_url,
            params={"offset": offset, "limit": limit}
        )
        items = response.json().get("items", [])

        if not items:
            break

        for item in items:
            yield item

        if len(items) < limit:
            break

        offset += limit
```

## Pagination Detection

Auto-detect pagination type from page analysis.

```python
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

def detect_pagination_type(soup: BeautifulSoup, url: str) -> str:
    """Detect the type of pagination used on a page."""

    # Check for URL parameters
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    if "page" in params or "p" in params:
        return "url_params"

    # Check for next button
    if soup.select_one("a.next, a[rel='next'], .pagination a:contains('Next')"):
        return "next_button"

    # Check for load more button
    if soup.select_one("button.load-more, [data-action='load-more']"):
        return "load_more"

    # Check for infinite scroll indicators
    if soup.select_one("[data-infinite-scroll], .infinite-scroll"):
        return "infinite_scroll"

    return "unknown"
```

## Best Practices

1. **Track seen items** - Avoid duplicates if pagination restarts
2. **Handle empty pages** - Stop when no items returned
3. **Implement rate limiting** - Add delays between page requests
4. **Set maximum limits** - Prevent infinite loops
5. **Log progress** - Track pages processed for debugging
