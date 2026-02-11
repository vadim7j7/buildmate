# /analyze-target

Analyze a target website to understand its structure and plan scraping strategy.

## Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `url` | Target URL to analyze | Yes |
| `--depth` | Analysis depth: `shallow`, `medium`, `deep` | No |
| `--output` | Save analysis to file | No |

## Examples

```bash
/analyze-target https://example.com/products
/analyze-target https://example.com/products --depth deep
/analyze-target https://example.com --output analysis.md
```

## Analysis Process

### 1. Initial Reconnaissance

- **HTTP Headers** - Server type, caching, security headers
- **robots.txt** - Crawl rules and restrictions
- **sitemap.xml** - Site structure overview
- **Response Time** - Baseline latency

### 2. Page Structure Analysis

- **DOM Structure** - Key containers and patterns
- **CSS Classes** - Semantic vs generated class names
- **Data Attributes** - Stable `data-*` attributes for selection
- **JavaScript Rendering** - Static HTML vs dynamic content

### 3. Anti-Bot Detection

| Detection Method | Risk Level | Mitigation |
|-----------------|------------|------------|
| Cloudflare | High | Browser automation, proxy rotation |
| reCAPTCHA | High | Manual solving, CAPTCHA service |
| Rate Limiting | Medium | Throttling, delays |
| Fingerprinting | Medium | Stealth browser plugins |
| IP Blocking | Low | Proxy rotation |

### 4. Data Extraction Points

Identify extractable data fields:

| Field | Selector | Type | Notes |
|-------|----------|------|-------|
| Product Name | `.product-title` | text | Stable class |
| Price | `[data-price]` | attribute | Numeric value |
| Image | `.gallery img` | attribute | Multiple images |
| Description | `#description` | HTML | May contain formatting |

### 5. Pagination Analysis

| Type | Detection | Strategy |
|------|-----------|----------|
| URL Parameters | `?page=N` | Increment until empty |
| Next Button | `a.next-page` | Follow until missing |
| Infinite Scroll | JavaScript loading | Scroll and wait |
| Load More | AJAX button | Click and capture |

## Output Format

```markdown
# Target Analysis: example.com/products

## Overview
- **URL**: https://example.com/products
- **Status**: 200 OK
- **Server**: nginx/1.18.0
- **Rendering**: Static HTML (no JavaScript required)

## Access Restrictions

### robots.txt
```
User-agent: *
Disallow: /admin/
Disallow: /cart/
Crawl-delay: 2
```

### Rate Limiting
- No explicit rate limit headers detected
- Recommended: 2-3 second delays

### Anti-Bot Protection
- **Cloudflare**: Not detected
- **CAPTCHA**: Not detected
- **Risk Level**: Low

## Page Structure

### Listing Page
- Container: `div.product-grid`
- Items: `div.product-card`
- Pagination: `nav.pagination a`

### Suggested Selectors
| Data | Primary Selector | Fallback |
|------|-----------------|----------|
| Name | `h2.product-name` | `.card-title` |
| Price | `span[data-price]` | `.price-current` |
| URL | `a.product-link` | `.card a:first-child` |
| Image | `img.product-image` | `.card img` |

### Pagination
- Type: URL parameter (`?page=N`)
- Pattern: Sequential pages
- Total Pages: ~50 (estimated from listing count)

## Recommended Strategy

1. **Method**: HTTP scraping (no browser needed)
2. **Rate**: 2 second delay between requests
3. **Concurrency**: 1 request at a time
4. **Pagination**: Follow page parameter until 404

## Extraction Code Preview

{% if variables.language == 'Python' %}
```python
from bs4 import BeautifulSoup

def extract_product(card) -> dict:
    return {
        "name": card.select_one("h2.product-name").text.strip(),
        "price": float(card.select_one("[data-price]")["data-price"]),
        "url": card.select_one("a.product-link")["href"],
        "image": card.select_one("img.product-image")["src"],
    }
```
{% else %}
```typescript
function extractProduct(card: cheerio.Cheerio): Product {
  return {
    name: card.find('h2.product-name').text().trim(),
    price: parseFloat(card.find('[data-price]').attr('data-price') || '0'),
    url: card.find('a.product-link').attr('href') || '',
    image: card.find('img.product-image').attr('src') || '',
  };
}
```
{% endif %}

## Risks and Considerations

1. **Class names may change** - Use data attributes when available
2. **Prices have currency symbols** - Parse and normalize
3. **Images are lazy-loaded** - May need `data-src` attribute
4. **Session required for details** - Consider cookie handling
```

## Implementation Steps

1. **Fetch target URL** and analyze response headers
2. **Check robots.txt** for restrictions
3. **Analyze DOM** for data patterns
4. **Test selectors** on sample pages
5. **Identify pagination** mechanism
6. **Assess anti-bot measures**
7. **Generate strategy report**

## Self-Verification

After analysis, verify:

- [ ] robots.txt checked and respected
- [ ] Selectors tested on multiple pages
- [ ] Pagination mechanism confirmed
- [ ] Rate limit recommendations provided
- [ ] Anti-bot risks identified
- [ ] Code preview is functional
