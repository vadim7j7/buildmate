# Error Handling Patterns

Robust error handling for reliable scrapers.

## HTTP Error Handling

Handle different HTTP status codes appropriately.

### Python

```python
import httpx
from enum import Enum

class ErrorAction(Enum):
    RETRY = "retry"
    SKIP = "skip"
    ABORT = "abort"

def handle_http_error(status_code: int) -> ErrorAction:
    """Determine action based on HTTP status code."""
    if status_code == 429:  # Rate limited
        return ErrorAction.RETRY
    elif status_code == 404:  # Not found
        return ErrorAction.SKIP
    elif status_code in (500, 502, 503, 504):  # Server errors
        return ErrorAction.RETRY
    elif status_code == 403:  # Forbidden
        return ErrorAction.ABORT  # Might be blocked
    elif status_code == 401:  # Unauthorized
        return ErrorAction.ABORT  # Re-authenticate needed
    else:
        return ErrorAction.SKIP

async def fetch_with_error_handling(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.text
    except httpx.HTTPStatusError as e:
        action = handle_http_error(e.response.status_code)
        if action == ErrorAction.ABORT:
            raise
        elif action == ErrorAction.SKIP:
            print(f"Skipping {url}: {e.response.status_code}")
            return None
        else:
            raise  # Will be caught by retry logic
```

### Node.js

```typescript
enum ErrorAction {
  RETRY = 'retry',
  SKIP = 'skip',
  ABORT = 'abort',
}

function handleHttpError(status: number): ErrorAction {
  if (status === 429) return ErrorAction.RETRY;
  if (status === 404) return ErrorAction.SKIP;
  if ([500, 502, 503, 504].includes(status)) return ErrorAction.RETRY;
  if (status === 403) return ErrorAction.ABORT;
  if (status === 401) return ErrorAction.ABORT;
  return ErrorAction.SKIP;
}
```

## Retry with Exponential Backoff

Retry failed requests with increasing delays.

### Python

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TransportError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
async def fetch_with_retry(client: httpx.AsyncClient, url: str) -> str:
    response = await client.get(url)
    response.raise_for_status()
    return response.text
```

### Node.js

```typescript
async function fetchWithRetry(
  url: string,
  maxAttempts = 5,
  baseDelay = 2000
): Promise<string> {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      const response = await axios.get(url);
      return response.data;
    } catch (error: any) {
      const isRetryable =
        error.response?.status === 429 ||
        [500, 502, 503, 504].includes(error.response?.status) ||
        error.code === 'ECONNRESET';

      if (!isRetryable || attempt === maxAttempts - 1) {
        throw error;
      }

      const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 1000;
      console.log(`Retry ${attempt + 1} after ${delay}ms`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  throw new Error('Max retries exceeded');
}
```

## Extraction Error Handling

Handle missing or malformed page elements.

### Python

```python
from bs4 import BeautifulSoup
from typing import Optional

class ExtractionError(Exception):
    """Raised when critical data cannot be extracted."""
    pass

def safe_extract(
    soup: BeautifulSoup,
    selector: str,
    attribute: str = None,
    required: bool = False,
    default: str = None,
) -> Optional[str]:
    """Safely extract text or attribute from element."""
    element = soup.select_one(selector)

    if element is None:
        if required:
            raise ExtractionError(f"Required element not found: {selector}")
        return default

    if attribute:
        value = element.get(attribute)
    else:
        value = element.get_text(strip=True)

    return value or default

# Usage
def extract_product(soup: BeautifulSoup) -> dict:
    return {
        "name": safe_extract(soup, "h1.product-name", required=True),
        "price": safe_extract(soup, ".price", required=True),
        "sku": safe_extract(soup, "[data-sku]", attribute="data-sku"),
        "image": safe_extract(soup, ".product-image", attribute="src"),
        "description": safe_extract(soup, ".description", default=""),
    }
```

### Node.js

```typescript
class ExtractionError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ExtractionError';
  }
}

function safeExtract(
  $: cheerio.CheerioAPI,
  selector: string,
  options: {
    attribute?: string;
    required?: boolean;
    default?: string;
  } = {}
): string | null {
  const element = $(selector).first();

  if (element.length === 0) {
    if (options.required) {
      throw new ExtractionError(`Required element not found: ${selector}`);
    }
    return options.default ?? null;
  }

  const value = options.attribute
    ? element.attr(options.attribute)
    : element.text().trim();

  return value || options.default || null;
}
```

## Circuit Breaker

Stop scraping when too many errors occur.

### Python

```python
from datetime import datetime, timedelta
from collections import deque

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: timedelta = timedelta(minutes=5),
        window_size: int = 10,
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.window_size = window_size
        self.failures: deque = deque(maxlen=window_size)
        self.last_failure_time: datetime | None = None
        self.is_open = False

    def record_success(self):
        self.failures.append(False)
        self._check_state()

    def record_failure(self):
        self.failures.append(True)
        self.last_failure_time = datetime.now()
        self._check_state()

    def _check_state(self):
        failure_count = sum(1 for f in self.failures if f)
        if failure_count >= self.failure_threshold:
            self.is_open = True
        elif self.is_open and self.last_failure_time:
            if datetime.now() - self.last_failure_time > self.reset_timeout:
                self.is_open = False
                self.failures.clear()

    def can_proceed(self) -> bool:
        self._check_state()
        return not self.is_open

# Usage
breaker = CircuitBreaker(failure_threshold=5)

for url in urls:
    if not breaker.can_proceed():
        print("Circuit breaker open - stopping scraper")
        break

    try:
        data = await scrape(url)
        breaker.record_success()
    except Exception as e:
        breaker.record_failure()
        print(f"Error: {e}")
```

## Error Logging

Structured error logging for debugging.

### Python

```python
import logging
import json
from datetime import datetime

class ScraperLogger:
    def __init__(self, name: str, log_file: str = "scraper.log"):
        self.logger = logging.getLogger(name)
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log_request(self, url: str, status: int, duration_ms: float):
        self.logger.info(json.dumps({
            "event": "request",
            "url": url,
            "status": status,
            "duration_ms": duration_ms,
        }))

    def log_error(self, url: str, error: Exception, context: dict = None):
        self.logger.error(json.dumps({
            "event": "error",
            "url": url,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
        }))

    def log_extraction(self, url: str, items_count: int, errors: list = None):
        self.logger.info(json.dumps({
            "event": "extraction",
            "url": url,
            "items_count": items_count,
            "errors": errors or [],
        }))
```

## Error Recovery Strategies

### Continue on Error

```python
async def scrape_all(urls: list[str]) -> list[dict]:
    results = []
    for url in urls:
        try:
            data = await scrape(url)
            results.append(data)
        except Exception as e:
            logger.log_error(url, e)
            continue  # Skip this URL, continue with others
    return results
```

### Checkpoint and Resume

```python
import json
from pathlib import Path

class CheckpointedScraper:
    def __init__(self, checkpoint_file: Path):
        self.checkpoint_file = checkpoint_file
        self.completed_urls: set[str] = set()
        self.load_checkpoint()

    def load_checkpoint(self):
        if self.checkpoint_file.exists():
            data = json.loads(self.checkpoint_file.read_text())
            self.completed_urls = set(data.get("completed", []))

    def save_checkpoint(self):
        self.checkpoint_file.write_text(json.dumps({
            "completed": list(self.completed_urls)
        }))

    async def scrape(self, urls: list[str]):
        for url in urls:
            if url in self.completed_urls:
                continue

            try:
                await self.process(url)
                self.completed_urls.add(url)
                self.save_checkpoint()
            except Exception as e:
                logger.error(f"Failed: {url}: {e}")
                raise  # Or continue, depending on strategy
```

## Best Practices

1. **Never ignore errors** - Always log, even if skipping
2. **Categorize errors** - Different handling for different types
3. **Implement retries** - Transient errors often resolve
4. **Use circuit breakers** - Prevent cascade failures
5. **Checkpoint progress** - Enable resumption after crashes
6. **Monitor error rates** - Alert when thresholds exceeded
