# /analyze-site

Comprehensive site-wide analysis for large-scale scraping projects.

## Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `domain` | Target domain to analyze | Yes |
| `--sitemap` | Use sitemap for discovery | No |
| `--max-pages` | Maximum pages to sample | No |
| `--output` | Save analysis to file | No |

## Examples

```bash
/analyze-site example.com
/analyze-site example.com --sitemap --max-pages 100
/analyze-site example.com --output site-analysis.md
```

## Analysis Scope

### 1. Site Discovery

- **Sitemap parsing** - Find all indexable URLs
- **Internal linking** - Discover page types
- **URL patterns** - Identify structured routes
- **Content categories** - Group pages by type

### 2. Page Type Classification

| Page Type | URL Pattern | Volume | Priority |
|-----------|-------------|--------|----------|
| Listing | `/products`, `/category/*` | High | Primary |
| Detail | `/product/*`, `/item/*` | High | Primary |
| Search | `/search?q=*` | Medium | Secondary |
| Static | `/about`, `/contact` | Low | Skip |

### 3. Technical Assessment

| Aspect | Finding | Impact |
|--------|---------|--------|
| CDN | Cloudflare | May need proxy |
| JavaScript | React SPA | Browser required |
| API Endpoints | REST API found | May scrape API directly |
| Authentication | Login required for prices | Session handling needed |

### 4. Scale Estimation

- **Total pages**: ~50,000
- **Scraping time**: ~28 hours at 2s/page
- **Data volume**: ~500MB JSON estimated
- **Storage needs**: Consider database vs files

## Output Format

```markdown
# Site Analysis: example.com

## Overview
- **Domain**: example.com
- **Technology**: Next.js, React
- **CDN**: Cloudflare
- **API**: REST endpoints discovered

## URL Structure

### Discovered Patterns
| Pattern | Example | Count |
|---------|---------|-------|
| `/category/{slug}` | /category/electronics | 25 |
| `/product/{id}` | /product/12345 | 5,000+ |
| `/brand/{name}` | /brand/apple | 100 |
| `/search` | /search?q=phone | Dynamic |

### Sitemap Analysis
- **Sitemap URL**: https://example.com/sitemap.xml
- **Index sitemaps**: 10
- **Total URLs**: 52,847
- **Last modified**: 2024-01-15

## Page Types

### Category Pages
- **Count**: ~25
- **Structure**: Grid layout, pagination
- **Data**: Product links, filters
- **Priority**: Crawl for discovery

### Product Pages
- **Count**: ~50,000
- **Structure**: Detail template
- **Data**: Name, price, description, images, specs
- **Priority**: Primary extraction target

### Search Results
- **Type**: AJAX-loaded
- **Pagination**: Infinite scroll
- **Strategy**: Use API directly

## Technical Requirements

### Rendering
- **Static pages**: Category, brand pages
- **Dynamic pages**: Product details (React hydration)
- **Recommendation**: Use browser for product pages

### Authentication
- **Public**: Category browsing, basic info
- **Login required**: Pricing, inventory
- **Strategy**: Cookie-based session

### Anti-Bot Measures
| Measure | Detected | Severity |
|---------|----------|----------|
| Cloudflare | Yes | Medium |
| CAPTCHA | Occasional | Low |
| Rate limit | 30 req/min | Medium |

## Recommended Architecture

### Crawler Design
```
                    ┌─────────────────┐
                    │   Coordinator   │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼───────┐
│ Category      │   │ Product       │   │ API           │
│ Crawler       │   │ Scraper       │   │ Client        │
└───────────────┘   └───────────────┘   └───────────────┘
```

### Data Pipeline
```
Scrape → Validate → Clean → Dedupe → Store → Export
```

## Resource Estimates

| Resource | Estimate |
|----------|----------|
| Total pages | 50,000 |
| Scrape time | 28 hours |
| Requests/day | 43,000 |
| Bandwidth | ~2GB |
| Storage | 500MB JSON |

## Implementation Plan

### Phase 1: Categories
- Scrape all category pages
- Build product URL list
- Estimate: 1 hour

### Phase 2: Products
- Scrape product details
- Validate and store
- Estimate: 27 hours

### Phase 3: Incremental
- Monitor for changes
- Rescrape updated items
- Ongoing maintenance

## Risks

1. **Cloudflare blocks** - Need proxy rotation
2. **Rate limiting** - Throttle to 30 req/min
3. **Dynamic pricing** - Login required
4. **Site changes** - Monitor selector stability
```

## Implementation Steps

1. **Fetch robots.txt and sitemap**
2. **Sample pages** from different URL patterns
3. **Classify page types** and data availability
4. **Assess technical requirements**
5. **Estimate scale and resources**
6. **Generate architecture recommendations**

## Self-Verification

After analysis, verify:

- [ ] Sitemap fully parsed
- [ ] Page types classified accurately
- [ ] Scale estimates are reasonable
- [ ] Technical requirements identified
- [ ] Risks documented with mitigations
- [ ] Implementation plan is actionable
