# Rate Limiting Patterns

Control request rates to avoid detection and respect server resources.

## Fixed Delay

Simple delay between each request.

### Python

```python
import asyncio

class FixedRateLimiter:
    def __init__(self, delay_seconds: float = 2.0):
        self.delay = delay_seconds

    async def wait(self):
        await asyncio.sleep(self.delay)

# Usage
limiter = FixedRateLimiter(delay_seconds=2.0)
for url in urls:
    await limiter.wait()
    response = await client.get(url)
```

### Node.js

```typescript
class FixedRateLimiter {
  private delay: number;

  constructor(delayMs = 2000) {
    this.delay = delayMs;
  }

  async wait(): Promise<void> {
    await new Promise(resolve => setTimeout(resolve, this.delay));
  }
}
```

## Random Delay

Randomized delays to appear more human-like.

### Python

```python
import asyncio
import random

class RandomRateLimiter:
    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        self.min_delay = min_delay
        self.max_delay = max_delay

    async def wait(self):
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)

# Usage
limiter = RandomRateLimiter(min_delay=1.5, max_delay=4.0)
```

### Node.js

```typescript
class RandomRateLimiter {
  private minDelay: number;
  private maxDelay: number;

  constructor(minDelayMs = 1000, maxDelayMs = 3000) {
    this.minDelay = minDelayMs;
    this.maxDelay = maxDelayMs;
  }

  async wait(): Promise<void> {
    const delay = this.minDelay + Math.random() * (this.maxDelay - this.minDelay);
    await new Promise(resolve => setTimeout(resolve, delay));
  }
}
```

## Token Bucket

Allow bursts while maintaining average rate.

### Python

```python
import asyncio
from time import time

class TokenBucketLimiter:
    def __init__(self, rate: float, burst: int):
        """
        Args:
            rate: Tokens per second (e.g., 0.5 = 1 request every 2 seconds)
            burst: Maximum tokens (allows short bursts)
        """
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_update = time()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time()
            # Add tokens based on time elapsed
            self.tokens = min(
                self.burst,
                self.tokens + (now - self.last_update) * self.rate
            )
            self.last_update = now

            if self.tokens < 1:
                # Wait for a token
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1

# Usage: 1 request per 2 seconds, burst of 5
limiter = TokenBucketLimiter(rate=0.5, burst=5)
for url in urls:
    await limiter.acquire()
    response = await client.get(url)
```

### Node.js

```typescript
class TokenBucketLimiter {
  private rate: number;
  private burst: number;
  private tokens: number;
  private lastUpdate: number;

  constructor(rate: number, burst: number) {
    this.rate = rate;
    this.burst = burst;
    this.tokens = burst;
    this.lastUpdate = Date.now();
  }

  async acquire(): Promise<void> {
    const now = Date.now();
    this.tokens = Math.min(
      this.burst,
      this.tokens + ((now - this.lastUpdate) / 1000) * this.rate
    );
    this.lastUpdate = now;

    if (this.tokens < 1) {
      const waitTime = ((1 - this.tokens) / this.rate) * 1000;
      await new Promise(resolve => setTimeout(resolve, waitTime));
      this.tokens = 0;
    } else {
      this.tokens -= 1;
    }
  }
}
```

## Per-Domain Rate Limiting

Different rates for different domains.

### Python

```python
from urllib.parse import urlparse
from collections import defaultdict

class PerDomainRateLimiter:
    def __init__(self, default_delay: float = 2.0):
        self.default_delay = default_delay
        self.domain_delays: dict[str, float] = {}
        self.last_request: dict[str, float] = defaultdict(float)

    def set_domain_delay(self, domain: str, delay: float):
        self.domain_delays[domain] = delay

    async def wait(self, url: str):
        domain = urlparse(url).netloc
        delay = self.domain_delays.get(domain, self.default_delay)

        now = time()
        elapsed = now - self.last_request[domain]
        if elapsed < delay:
            await asyncio.sleep(delay - elapsed)

        self.last_request[domain] = time()

# Usage
limiter = PerDomainRateLimiter(default_delay=2.0)
limiter.set_domain_delay("api.example.com", 1.0)  # Faster for API
limiter.set_domain_delay("shop.example.com", 3.0)  # Slower for shop
```

## Respect Retry-After Headers

Handle server-requested delays.

### Python

```python
async def fetch_with_retry_after(client: httpx.AsyncClient, url: str) -> str:
    while True:
        response = await client.get(url)

        if response.status_code == 429:
            # Rate limited - respect Retry-After header
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                if retry_after.isdigit():
                    delay = int(retry_after)
                else:
                    # HTTP date format
                    from email.utils import parsedate_to_datetime
                    target = parsedate_to_datetime(retry_after)
                    delay = (target - datetime.now()).total_seconds()
            else:
                delay = 60  # Default wait

            print(f"Rate limited. Waiting {delay} seconds...")
            await asyncio.sleep(delay)
            continue

        response.raise_for_status()
        return response.text
```

### Node.js

```typescript
async function fetchWithRetryAfter(url: string): Promise<string> {
  while (true) {
    const response = await axios.get(url, { validateStatus: () => true });

    if (response.status === 429) {
      const retryAfter = response.headers['retry-after'];
      let delay: number;

      if (retryAfter && /^\d+$/.test(retryAfter)) {
        delay = parseInt(retryAfter, 10) * 1000;
      } else {
        delay = 60000; // Default 1 minute
      }

      console.log(`Rate limited. Waiting ${delay / 1000} seconds...`);
      await new Promise(resolve => setTimeout(resolve, delay));
      continue;
    }

    if (response.status >= 400) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.data;
  }
}
```

## Concurrent Request Limiting

Control concurrent requests.

### Python

```python
import asyncio

class ConcurrentLimiter:
    def __init__(self, max_concurrent: int = 5, delay: float = 0.5):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.delay = delay

    async def fetch(self, client: httpx.AsyncClient, url: str):
        async with self.semaphore:
            response = await client.get(url)
            await asyncio.sleep(self.delay)  # Rate limit within concurrent
            return response

# Usage
limiter = ConcurrentLimiter(max_concurrent=3, delay=1.0)
tasks = [limiter.fetch(client, url) for url in urls]
results = await asyncio.gather(*tasks)
```

### Node.js

```typescript
import pLimit from 'p-limit';

const limit = pLimit(3); // Max 3 concurrent

async function scrapeAll(urls: string[]): Promise<any[]> {
  const tasks = urls.map(url =>
    limit(async () => {
      const result = await scrape(url);
      await new Promise(resolve => setTimeout(resolve, 1000)); // Delay between
      return result;
    })
  );
  return Promise.all(tasks);
}
```

## Adaptive Rate Limiting

Adjust rate based on server responses.

### Python

```python
class AdaptiveRateLimiter:
    def __init__(
        self,
        initial_delay: float = 1.0,
        min_delay: float = 0.5,
        max_delay: float = 10.0,
    ):
        self.delay = initial_delay
        self.min_delay = min_delay
        self.max_delay = max_delay

    def success(self):
        """Speed up after successful request."""
        self.delay = max(self.min_delay, self.delay * 0.9)

    def failure(self, status_code: int):
        """Slow down after error."""
        if status_code == 429:
            self.delay = min(self.max_delay, self.delay * 2)
        elif status_code >= 500:
            self.delay = min(self.max_delay, self.delay * 1.5)

    async def wait(self):
        await asyncio.sleep(self.delay)

# Usage
limiter = AdaptiveRateLimiter()
for url in urls:
    await limiter.wait()
    try:
        response = await client.get(url)
        response.raise_for_status()
        limiter.success()
    except httpx.HTTPStatusError as e:
        limiter.failure(e.response.status_code)
```

## robots.txt Crawl-Delay

Respect robots.txt crawl delay.

### Python

```python
from urllib.robotparser import RobotFileParser

async def get_crawl_delay(base_url: str, user_agent: str = "*") -> float | None:
    rp = RobotFileParser()
    rp.set_url(f"{base_url}/robots.txt")
    rp.read()

    delay = rp.crawl_delay(user_agent)
    return delay

# Usage
delay = await get_crawl_delay("https://example.com")
if delay:
    limiter = FixedRateLimiter(delay_seconds=delay)
else:
    limiter = RandomRateLimiter(min_delay=2.0, max_delay=4.0)
```

## Best Practices

1. **Start conservative** - Begin with longer delays, speed up if stable
2. **Respect robots.txt** - Use specified crawl-delay
3. **Handle 429** - Always respect Retry-After headers
4. **Monitor response times** - Slow responses may indicate overload
5. **Use random delays** - Avoid predictable patterns
6. **Per-domain limits** - Different sites have different tolerances
7. **Time-of-day awareness** - Consider off-peak scraping
