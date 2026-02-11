# Anti-Detection Patterns

Techniques to avoid bot detection and blocking when scraping.

## User-Agent Rotation

Never use a static User-Agent. Rotate through realistic browser strings.

### Python

```python
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

class UserAgentRotator:
    def __init__(self, agents: list[str] = USER_AGENTS):
        self.agents = agents

    def get_random(self) -> str:
        return random.choice(self.agents)

    def get_headers(self) -> dict:
        return {
            "User-Agent": self.get_random(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
```

### Node.js

```typescript
const USER_AGENTS = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
];

function getRandomUserAgent(): string {
  return USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
}

function getHeaders(): Record<string, string> {
  return {
    'User-Agent': getRandomUserAgent(),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
  };
}
```

## Request Timing

Add random delays between requests to appear human-like.

### Python

```python
import asyncio
import random

class RateLimiter:
    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request = 0

    async def wait(self):
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)

    async def throttled_request(self, client, url: str):
        await self.wait()
        return await client.get(url)
```

### Node.js

```typescript
class RateLimiter {
  private minDelay: number;
  private maxDelay: number;

  constructor(minDelay = 1000, maxDelay = 3000) {
    this.minDelay = minDelay;
    this.maxDelay = maxDelay;
  }

  async wait(): Promise<void> {
    const delay = this.minDelay + Math.random() * (this.maxDelay - this.minDelay);
    await new Promise(resolve => setTimeout(resolve, delay));
  }
}
```

## Proxy Rotation

Rotate through proxy servers to distribute requests.

### Python

```python
import httpx
from itertools import cycle

class ProxyRotator:
    def __init__(self, proxies: list[str]):
        self.proxy_cycle = cycle(proxies)

    def get_client(self) -> httpx.AsyncClient:
        proxy = next(self.proxy_cycle)
        return httpx.AsyncClient(
            proxies={"all://": proxy},
            timeout=30.0,
        )

# Usage
proxies = [
    "http://proxy1.example.com:8080",
    "http://proxy2.example.com:8080",
    "http://proxy3.example.com:8080",
]
rotator = ProxyRotator(proxies)
```

### Node.js

```typescript
import { HttpsProxyAgent } from 'https-proxy-agent';
import axios from 'axios';

class ProxyRotator {
  private proxies: string[];
  private index = 0;

  constructor(proxies: string[]) {
    this.proxies = proxies;
  }

  getNext(): string {
    const proxy = this.proxies[this.index];
    this.index = (this.index + 1) % this.proxies.length;
    return proxy;
  }

  createClient() {
    const proxy = this.getNext();
    return axios.create({
      httpAgent: new HttpsProxyAgent(proxy),
      httpsAgent: new HttpsProxyAgent(proxy),
    });
  }
}
```

## Browser Fingerprint Evasion

For browser-based scraping, use stealth techniques.

### Python (Playwright)

```python
from playwright.async_api import async_playwright

async def create_stealth_browser():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
        ],
    )

    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        locale="en-US",
        timezone_id="America/New_York",
    )

    # Override navigator.webdriver
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)

    return browser, context
```

### Node.js (Playwright)

```typescript
import { chromium, BrowserContext } from 'playwright';

async function createStealthBrowser(): Promise<BrowserContext> {
  const browser = await chromium.launch({
    headless: true,
    args: [
      '--disable-blink-features=AutomationControlled',
      '--disable-dev-shm-usage',
    ],
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    locale: 'en-US',
    timezoneId: 'America/New_York',
  });

  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
  });

  return context;
}
```

## Cookie and Session Management

Maintain cookies across requests for session persistence.

### Python

```python
import httpx

class SessionManager:
    def __init__(self):
        self.client = httpx.AsyncClient(
            follow_redirects=True,
            cookies=httpx.Cookies(),
        )

    async def login(self, url: str, credentials: dict) -> bool:
        response = await self.client.post(url, data=credentials)
        return response.status_code == 200

    async def get(self, url: str):
        return await self.client.get(url)
```

## Request Header Consistency

Match headers to the User-Agent for consistency.

```python
def get_chrome_headers(user_agent: str) -> dict:
    return {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }
```

## Detection Checklist

- [ ] User-Agent rotation enabled
- [ ] Request delays implemented (1-3 seconds)
- [ ] Realistic browser headers
- [ ] Cookie persistence for sessions
- [ ] Proxy rotation (if high volume)
- [ ] Fingerprint evasion (for browser scrapers)
- [ ] Respect robots.txt
- [ ] Handle 429 with exponential backoff
