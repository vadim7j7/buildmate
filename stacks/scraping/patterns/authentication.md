# Authentication Patterns

Handle authenticated scraping scenarios.

## Cookie-Based Sessions

Maintain session cookies across requests.

### Python

```python
import httpx

class AuthenticatedScraper:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url,
            follow_redirects=True,
        )

    async def login(self, username: str, password: str) -> bool:
        """Login and store session cookies."""
        response = await self.client.post(
            "/login",
            data={"username": username, "password": password},
        )

        # Check for successful login (redirect or success page)
        if response.status_code in (200, 302):
            # Cookies are automatically stored
            return True
        return False

    async def get(self, path: str):
        """Make authenticated request."""
        return await self.client.get(path)

    async def close(self):
        await self.client.aclose()
```

### Node.js

```typescript
import axios, { AxiosInstance } from 'axios';
import { wrapper } from 'axios-cookiejar-support';
import { CookieJar } from 'tough-cookie';

class AuthenticatedScraper {
  private client: AxiosInstance;
  private jar: CookieJar;

  constructor(baseUrl: string) {
    this.jar = new CookieJar();
    this.client = wrapper(axios.create({
      baseURL: baseUrl,
      jar: this.jar,
      withCredentials: true,
    }));
  }

  async login(username: string, password: string): Promise<boolean> {
    const response = await this.client.post('/login', {
      username,
      password,
    });
    return response.status === 200;
  }

  async get(path: string) {
    return this.client.get(path);
  }
}
```

## Form-Based Login

Handle traditional form login with CSRF tokens.

### Python

```python
from bs4 import BeautifulSoup

class FormLoginScraper:
    async def login(self, login_url: str, username: str, password: str) -> bool:
        # Get login page to extract CSRF token
        response = await self.client.get(login_url)
        soup = BeautifulSoup(response.text, "lxml")

        # Extract CSRF token
        csrf_token = soup.select_one("input[name='csrf_token']")
        if csrf_token:
            csrf_value = csrf_token["value"]
        else:
            csrf_value = None

        # Submit login form
        form_data = {
            "username": username,
            "password": password,
        }
        if csrf_value:
            form_data["csrf_token"] = csrf_value

        response = await self.client.post(
            login_url,
            data=form_data,
            headers={"Referer": login_url},
        )

        # Check for successful redirect or dashboard page
        return "dashboard" in str(response.url) or "welcome" in response.text.lower()
```

## Browser-Based Login

For complex login flows (JavaScript, CAPTCHA).

### Python (Playwright)

```python
from playwright.async_api import async_playwright

class BrowserLoginScraper:
    async def login(self, login_url: str, username: str, password: str):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto(login_url)

            # Fill login form
            await page.fill("input[name='username']", username)
            await page.fill("input[name='password']", password)

            # Click submit
            await page.click("button[type='submit']")

            # Wait for navigation
            await page.wait_for_url("**/dashboard**")

            # Extract cookies for use in HTTP client
            cookies = await context.cookies()
            return cookies
```

### Node.js (Playwright)

```typescript
import { chromium, Cookie } from 'playwright';

async function browserLogin(
  loginUrl: string,
  username: string,
  password: string
): Promise<Cookie[]> {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  await page.goto(loginUrl);

  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');

  await page.waitForURL('**/dashboard**');

  const cookies = await context.cookies();
  await browser.close();

  return cookies;
}
```

## API Key Authentication

Handle API key in headers or query parameters.

### Python

```python
class APIKeyScraper:
    def __init__(self, base_url: str, api_key: str, key_location: str = "header"):
        self.base_url = base_url
        self.api_key = api_key
        self.key_location = key_location

        if key_location == "header":
            self.client = httpx.AsyncClient(
                base_url=base_url,
                headers={"Authorization": f"Bearer {api_key}"},
            )
        else:
            self.client = httpx.AsyncClient(base_url=base_url)

    async def get(self, path: str, **params):
        if self.key_location == "query":
            params["api_key"] = self.api_key
        return await self.client.get(path, params=params)
```

## OAuth 2.0 Token

Handle OAuth token refresh.

### Python

```python
from datetime import datetime, timedelta

class OAuthScraper:
    def __init__(self, base_url: str, client_id: str, client_secret: str):
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires = None
        self.client = httpx.AsyncClient()

    async def ensure_token(self):
        """Refresh token if expired."""
        if self.access_token and self.token_expires > datetime.now():
            return

        response = await self.client.post(
            f"{self.base_url}/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        data = response.json()
        self.access_token = data["access_token"]
        self.token_expires = datetime.now() + timedelta(seconds=data["expires_in"] - 60)

    async def get(self, path: str):
        await self.ensure_token()
        return await self.client.get(
            f"{self.base_url}{path}",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
```

## Session Persistence

Save and restore sessions for long-running scrapers.

### Python

```python
import json
from pathlib import Path

class PersistentSessionScraper:
    def __init__(self, base_url: str, session_file: Path):
        self.session_file = session_file
        self.client = httpx.AsyncClient(base_url=base_url)

    async def load_session(self) -> bool:
        """Load saved session cookies."""
        if not self.session_file.exists():
            return False

        data = json.loads(self.session_file.read_text())
        for cookie in data["cookies"]:
            self.client.cookies.set(
                cookie["name"],
                cookie["value"],
                domain=cookie.get("domain"),
            )
        return True

    async def save_session(self):
        """Save current session cookies."""
        cookies = [
            {"name": c.name, "value": c.value, "domain": c.domain}
            for c in self.client.cookies.jar
        ]
        self.session_file.write_text(json.dumps({"cookies": cookies}))

    async def is_logged_in(self) -> bool:
        """Check if session is still valid."""
        response = await self.client.get("/api/me")
        return response.status_code == 200
```

## Security Best Practices

1. **Never hardcode credentials** - Use environment variables
2. **Store tokens securely** - Encrypt session files
3. **Rotate credentials** - Use service accounts for scraping
4. **Respect rate limits** - Authenticated endpoints may have stricter limits
5. **Handle session expiry** - Re-authenticate when sessions expire
6. **Log out when done** - Clean up sessions properly

```python
import os

# Good: Use environment variables
username = os.environ["SCRAPER_USERNAME"]
password = os.environ["SCRAPER_PASSWORD"]

# Bad: Hardcoded credentials
# username = "admin"  # NEVER DO THIS
```
