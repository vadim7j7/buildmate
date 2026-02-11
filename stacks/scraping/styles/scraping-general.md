# General Web Scraping Style Guide

Universal principles for building reliable, ethical web scrapers.

## Ethical Scraping

### robots.txt Compliance

Always check and respect robots.txt:

- Check `robots.txt` before scraping any domain
- Respect `Disallow` directives for your User-Agent
- Follow `Crawl-delay` when specified
- Never ignore restrictions without explicit permission

### Rate Limiting

Be a good citizen:

| Scenario | Recommended Delay |
|----------|-------------------|
| Small sites | 3-5 seconds |
| Medium sites | 2-3 seconds |
| Large sites | 1-2 seconds |
| APIs (with key) | Per API documentation |

### Identification

Consider identifying yourself:

```
User-Agent: MyBot/1.0 (https://mysite.com/bot; contact@mysite.com)
```

## Selector Best Practices

### Prefer Stable Selectors

| Priority | Selector Type | Example |
|----------|---------------|---------|
| 1 (Best) | data attributes | `[data-product-id]` |
| 2 | IDs | `#product-name` |
| 3 | Semantic classes | `.product-title` |
| 4 | Structure | `article.product h2` |
| 5 (Worst) | Generated classes | `.css-1abc23` |

### Use Fallback Selectors

```python
# Python
name = (
    soup.select_one("[data-testid='product-name']") or
    soup.select_one("h1.product-name") or
    soup.select_one("h1")
)
```

```typescript
// TypeScript
const name =
  $('[data-testid="product-name"]').first().text() ||
  $('h1.product-name').first().text() ||
  $('h1').first().text();
```

### Document Selector Logic

```python
# Selector for product price
# Primary: data-price attribute (most reliable)
# Fallback: .price-current (may include "From $X")
# Note: European sites use comma as decimal separator
price_selector = "[data-price], .price-current, .price"
```

## Data Modeling

### Define Schemas

Always define explicit schemas for extracted data:

```python
# Python (Pydantic)
class Product(BaseModel):
    name: str
    price: Decimal
    url: HttpUrl
```

```typescript
// TypeScript (Zod)
const ProductSchema = z.object({
  name: z.string(),
  price: z.number(),
  url: z.string().url(),
});
```

### Validate Early

Validate data immediately after extraction:

```python
raw_data = extract_from_page(html)
try:
    product = Product(**raw_data)
except ValidationError as e:
    log_validation_error(url, e)
    continue
```

### Track Metadata

Include scraping metadata:

```python
class ScrapedProduct(Product):
    scraped_at: datetime
    source_url: HttpUrl
    scraper_version: str
```

## Error Handling

### Categorize Errors

| Error Type | Action | Retry |
|------------|--------|-------|
| 429 Rate Limited | Wait, retry | Yes |
| 404 Not Found | Skip | No |
| 500 Server Error | Retry with backoff | Yes |
| Extraction Error | Log, skip | No |
| Network Error | Retry with backoff | Yes |

### Never Fail Silently

```python
# Bad
try:
    data = extract(html)
except:
    pass

# Good
try:
    data = extract(html)
except ExtractionError as e:
    logger.warning(f"Extraction failed: {e}", url=url)
    errors.append({"url": url, "error": str(e)})
```

### Implement Circuit Breakers

Stop scraping when too many errors occur:

```python
if consecutive_errors > 5:
    raise TooManyErrors("Stopping due to repeated failures")
```

## Testing Strategy

### Unit Tests

Test extractors with saved HTML fixtures:

```
tests/
├── fixtures/
│   ├── product_listing.html
│   ├── product_detail.html
│   └── edge_cases/
│       ├── empty_results.html
│       └── special_chars.html
└── test_extractors.py
```

### Integration Tests

Test full scrape flow with mocked HTTP:

```python
@respx.mock
def test_full_scrape_flow():
    respx.get("https://example.com/products").mock(...)
    products = scraper.scrape_all("/products")
    assert len(products) == expected
```

### Snapshot Tests

Compare extracted data against known-good snapshots:

```python
def test_extraction_matches_snapshot():
    result = extract(load_fixture("product.html"))
    assert result == load_snapshot("product_expected.json")
```

## Logging and Monitoring

### Structured Logging

Use structured logs for analysis:

```python
logger.info("page_scraped", {
    "url": url,
    "items_count": len(items),
    "duration_ms": duration,
    "status_code": response.status_code,
})
```

### Track Metrics

Monitor scraper health:

| Metric | Purpose |
|--------|---------|
| Success rate | % of successful requests |
| Items per page | Detect empty/changed pages |
| Response time | Detect slow/overloaded servers |
| Validation rate | % of items passing validation |
| Error rate | Track failures by type |

## File Organization

### Separate Concerns

```
scrapers/
├── spiders/          # HTTP fetching logic
├── extractors/       # HTML parsing logic
├── pipelines/        # Data cleaning/validation
├── utils/            # Rate limiting, proxies
└── storage/          # Database/file output
```

### Configuration

Externalize configuration:

```python
# config.py
class ScraperConfig:
    base_url: str
    delay_seconds: float = 2.0
    max_retries: int = 3
    user_agent: str = "MyBot/1.0"
```

## Anti-Patterns to Avoid

### Don't

1. **Hardcode selectors everywhere** - Use a selector registry
2. **Ignore robots.txt** - Always check first
3. **Scrape too fast** - Add delays between requests
4. **Skip validation** - Always validate extracted data
5. **Swallow errors** - Log everything
6. **Use static User-Agent** - Rotate User-Agents
7. **Store credentials in code** - Use environment variables
8. **Ignore encoding** - Handle UTF-8, Latin-1, etc.

### Do

1. **Use configuration files** - Externalize settings
2. **Implement retries** - Handle transient failures
3. **Add rate limiting** - Be respectful
4. **Validate data** - Use schemas
5. **Log structured data** - Enable debugging
6. **Test thoroughly** - Unit, integration, snapshot tests
7. **Monitor in production** - Track metrics
8. **Document selectors** - Explain why each selector works

## Checklist Before Deployment

- [ ] robots.txt checked and respected
- [ ] Rate limiting implemented
- [ ] User-Agent rotation enabled
- [ ] Error handling complete
- [ ] Retry logic with backoff
- [ ] Data validation schemas defined
- [ ] Unit tests for extractors
- [ ] Integration tests for full flow
- [ ] Structured logging configured
- [ ] Metrics/monitoring in place
- [ ] Configuration externalized
- [ ] No hardcoded credentials
