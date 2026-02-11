# Python Web Scraping Style Guide

Conventions for Python-based web scrapers.

## Project Structure

```
project/
├── scrapers/
│   ├── __init__.py
│   └── spiders/
│       ├── __init__.py
│       └── products.py
├── extractors/
│   ├── __init__.py
│   └── product_extractor.py
├── pipelines/
│   ├── __init__.py
│   ├── clean.py
│   └── validate.py
├── utils/
│   ├── __init__.py
│   ├── rate_limiter.py
│   ├── user_agents.py
│   └── proxy.py
├── tests/
│   ├── __init__.py
│   ├── test_spiders.py
│   └── fixtures/
│       └── sample_page.html
├── pyproject.toml
├── settings.py
└── scrapy.cfg  # If using Scrapy
```

## Code Style

### Type Hints

Always use type hints for function signatures:

```python
# Good
async def fetch_page(url: str, timeout: float = 30.0) -> str:
    ...

def extract_products(html: str) -> list[Product]:
    ...

# Bad
async def fetch_page(url, timeout=30.0):
    ...
```

### Async/Await

Prefer async for HTTP operations:

```python
# Good
import httpx

async def scrape(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return parse_response(response.text)

# Bad - blocking I/O
import requests

def scrape(url: str) -> dict:
    response = requests.get(url)
    return parse_response(response.text)
```

### Pydantic Models

Use Pydantic for data validation:

```python
from pydantic import BaseModel, HttpUrl, field_validator
from decimal import Decimal

class Product(BaseModel):
    name: str
    price: Decimal
    url: HttpUrl
    in_stock: bool = True

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("price", mode="before")
    @classmethod
    def parse_price(cls, v: str | Decimal) -> Decimal:
        if isinstance(v, str):
            return Decimal(v.replace("$", "").replace(",", ""))
        return v
```

### Context Managers

Use context managers for resource management:

```python
# Good
async with httpx.AsyncClient() as client:
    response = await client.get(url)

async with async_playwright() as p:
    browser = await p.chromium.launch()
    ...

# Bad
client = httpx.AsyncClient()
response = await client.get(url)
# Forgot to close client
```

### Error Handling

Use specific exceptions:

```python
class ScraperError(Exception):
    """Base exception for scraper errors."""
    pass

class ExtractionError(ScraperError):
    """Raised when data extraction fails."""
    pass

class RateLimitError(ScraperError):
    """Raised when rate limited."""
    pass

# Usage
try:
    data = extract_product(html)
except ExtractionError as e:
    logger.error(f"Extraction failed: {e}")
    raise
```

## HTTP Client Configuration

### httpx Setup

```python
import httpx

def create_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, connect=10.0),
        follow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0 ...",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        },
        limits=httpx.Limits(
            max_keepalive_connections=5,
            max_connections=10,
        ),
    )
```

## Selector Style

### BeautifulSoup

Prefer CSS selectors over find methods:

```python
from bs4 import BeautifulSoup

# Good
soup.select_one("h1.product-name")
soup.select(".product-item")
soup.select_one("[data-price]")["data-price"]

# Avoid for complex selectors
soup.find("h1", class_="product-name")
```

### lxml

Use XPath for complex queries:

```python
from lxml import html

tree = html.fromstring(page_content)

# XPath for complex selections
products = tree.xpath("//div[@class='product'][.//span[@class='in-stock']]")
```

## Logging

Use structured logging:

```python
import structlog

logger = structlog.get_logger()

# Good
logger.info(
    "page_scraped",
    url=url,
    items_count=len(items),
    duration_ms=duration,
)

# Bad
print(f"Scraped {len(items)} items from {url}")
```

## Testing

### Test Fixtures

Store HTML fixtures for testing:

```python
from pathlib import Path
import pytest

FIXTURES = Path(__file__).parent / "fixtures"

@pytest.fixture
def product_page_html() -> str:
    return (FIXTURES / "product_page.html").read_text()

def test_extract_product(product_page_html):
    product = extract_product(product_page_html)
    assert product.name == "Test Product"
    assert product.price == Decimal("29.99")
```

### Mocking HTTP

Use respx for async HTTP mocking:

```python
import respx
import httpx
import pytest

@pytest.mark.asyncio
@respx.mock
async def test_scrape_products():
    respx.get("https://example.com/products").mock(
        return_value=httpx.Response(200, html="<div>...</div>")
    )

    scraper = ProductScraper("https://example.com")
    products = await scraper.scrape("/products")

    assert len(products) == 3
```

## Dependencies

### pyproject.toml

```toml
[project]
name = "my-scraper"
version = "0.1.0"
dependencies = [
    "httpx>=0.25.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=4.9.0",
    "pydantic>=2.0.0",
    "structlog>=23.0.0",
]

[project.optional-dependencies]
browser = [
    "playwright>=1.40.0",
]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "respx>=0.20.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "UP", "B"]

[tool.mypy]
strict = true
```

## Quality Gates

```bash
# Linting
uv run ruff check .
uv run ruff check --fix .

# Type checking
uv run mypy .

# Tests
uv run pytest -v

# With coverage
uv run pytest --cov=scrapers --cov-report=html
```

## Anti-Patterns to Avoid

```python
# Bad: Hardcoded credentials
password = "secret123"

# Bad: No timeout
response = await client.get(url)

# Bad: Swallowing exceptions
try:
    data = extract(html)
except:
    pass

# Bad: Blocking in async code
import time
time.sleep(1)  # Use asyncio.sleep

# Bad: No rate limiting
for url in urls:
    await client.get(url)  # Too fast
```

## Recommended Libraries

| Purpose | Library |
|---------|---------|
| HTTP Client | httpx |
| HTML Parsing | BeautifulSoup, lxml |
| Validation | Pydantic |
| Browser | Playwright |
| Logging | structlog |
| Testing | pytest, respx |
| Linting | ruff |
| Types | mypy |
