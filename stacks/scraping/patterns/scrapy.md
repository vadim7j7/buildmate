# Scrapy Patterns

## Spider Definition

```python
# spiders/example_spider.py
import scrapy
from items import ArticleItem

class ExampleSpider(scrapy.Spider):
    name = "example"
    allowed_domains = ["example.com"]
    start_urls = ["https://example.com/articles"]

    custom_settings = {
        "CONCURRENT_REQUESTS": 8,
        "DOWNLOAD_DELAY": 1.0,
        "ROBOTSTXT_OBEY": True,
    }

    def parse(self, response):
        for article in response.css("article.post"):
            yield ArticleItem(
                title=article.css("h2::text").get(),
                url=response.urljoin(article.css("a::attr(href)").get()),
                summary=article.css("p.summary::text").get(),
            )

        # Pagination
        next_page = response.css("a.next-page::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)
```

## Item Definition

```python
# items.py
import scrapy

class ArticleItem(scrapy.Item):
    title = scrapy.Field()
    url = scrapy.Field()
    summary = scrapy.Field()
    content = scrapy.Field()
    author = scrapy.Field()
    published_at = scrapy.Field()
```

## Item Pipeline

```python
# pipelines.py
import json
from itemadapter import ItemAdapter

class JsonWriterPipeline:
    def open_spider(self, spider):
        self.file = open("output.jsonl", "w")

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        line = json.dumps(adapter.asdict()) + "\n"
        self.file.write(line)
        return item

class ValidationPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if not adapter.get("title"):
            raise scrapy.exceptions.DropItem(f"Missing title: {item}")
        return item
```

## Middleware

```python
# middlewares.py
import random

class RotateUserAgentMiddleware:
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    ]

    def process_request(self, request, spider):
        request.headers["User-Agent"] = random.choice(self.USER_AGENTS)
```

## Settings

```python
# settings.py
BOT_NAME = "myscraper"
SPIDER_MODULES = ["spiders"]

ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 16
DOWNLOAD_DELAY = 0.5
COOKIES_ENABLED = False

ITEM_PIPELINES = {
    "pipelines.ValidationPipeline": 100,
    "pipelines.JsonWriterPipeline": 300,
}

DOWNLOADER_MIDDLEWARES = {
    "middlewares.RotateUserAgentMiddleware": 400,
}

# Retry settings
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Cache for development
HTTPCACHE_ENABLED = True
HTTPCACHE_DIR = "httpcache"
```

## CrawlSpider with Rules

```python
# spiders/deep_spider.py
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

class DeepSpider(CrawlSpider):
    name = "deep"
    allowed_domains = ["example.com"]
    start_urls = ["https://example.com"]

    rules = (
        Rule(LinkExtractor(allow=r"/category/"), follow=True),
        Rule(LinkExtractor(allow=r"/article/"), callback="parse_article"),
    )

    def parse_article(self, response):
        yield {
            "title": response.css("h1::text").get(),
            "content": response.css("article").get(),
            "url": response.url,
        }
```

## BeautifulSoup Integration

```python
# Using BS4 inside Scrapy for complex parsing
from bs4 import BeautifulSoup

def parse(self, response):
    soup = BeautifulSoup(response.text, "lxml")
    for table in soup.find_all("table", class_="data"):
        rows = table.find_all("tr")
        for row in rows[1:]:  # skip header
            cells = row.find_all("td")
            yield {
                "name": cells[0].get_text(strip=True),
                "value": cells[1].get_text(strip=True),
            }
```

## Key Rules

1. Always obey `robots.txt` unless explicitly authorized otherwise
2. Use `DOWNLOAD_DELAY` to avoid overloading servers
3. Validate items in pipelines before storing
4. Use `allowed_domains` to prevent crawling outside target
5. Use `response.follow()` for relative URLs
6. Use CSS selectors over XPath when possible (more readable)
7. Enable HTTP cache during development
8. Handle pagination in the parse method
