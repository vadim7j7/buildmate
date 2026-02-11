# /test-scraper

Run comprehensive tests for a scraper, including validation against live targets.

## Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `name` | Scraper/spider name to test | No (tests all if omitted) |
| `--live` | Run against live target (not mocked) | No |
| `--validate` | Validate extracted data against schema | No |
| `--sample` | Number of items to sample for validation | No |
| `--output` | Save results to file | No |

## Examples

```bash
/test-scraper products
/test-scraper products --live --sample 10
/test-scraper --validate --output results.json
```

## Test Categories

### 1. Unit Tests

Test individual components:

{% if variables.language == 'Python' %}
```bash
# Run unit tests only
uv run pytest tests/unit/ -v

# Run with coverage
uv run pytest tests/unit/ --cov=scrapers --cov-report=html
```
{% else %}
```bash
# Run unit tests only
npm test -- --testPathPattern="unit"

# Run with coverage
npm test -- --coverage
```
{% endif %}

### 2. Integration Tests (Mocked)

Test full scraper flow with mocked HTTP:

{% if variables.language == 'Python' %}
```bash
# Run integration tests
uv run pytest tests/integration/ -v -m "not live"
```
{% else %}
```bash
# Run integration tests
npm test -- --testPathPattern="integration" --testPathIgnorePatterns="live"
```
{% endif %}

### 3. Live Validation Tests

Test against actual target (use sparingly):

{% if variables.language == 'Python' %}
```bash
# Run live tests (careful with rate limiting)
uv run pytest tests/live/ -v --slow

# With sampling
uv run pytest tests/live/ -v -k "test_sample" --sample=5
```
{% else %}
```bash
# Run live tests
npm test -- --testPathPattern="live" --runInBand

# Single test with timeout
npm test -- --testPathPattern="live" --testTimeout=60000
```
{% endif %}

## Validation Checks

### Data Quality

| Check | Description |
|-------|-------------|
| Schema Compliance | All items match defined schema |
| Required Fields | No null values for required fields |
| Data Types | Correct types (numbers, dates, URLs) |
| Value Ranges | Prices positive, dates valid, etc. |

### Extraction Accuracy

| Check | Description |
|-------|-------------|
| Selector Stability | Selectors find expected elements |
| Content Match | Extracted text matches visible content |
| URL Resolution | Relative URLs resolved correctly |
| Encoding | No mojibake or encoding issues |

### Performance

| Check | Description |
|-------|-------------|
| Response Time | Requests complete within timeout |
| Memory Usage | No memory leaks over multiple runs |
| Rate Limiting | Respects configured delays |

## Test Output

```markdown
## Test Results: {{ name }} Scraper

### Summary
- Total Tests: 25
- Passed: 23
- Failed: 2
- Skipped: 0

### Unit Tests
- Extractor tests: 10/10 passed
- Validator tests: 5/5 passed

### Integration Tests
- Full scrape flow: 5/6 passed
  - FAILED: test_handles_empty_page

### Live Validation (--live)
- Sample extraction: 3/4 passed
  - FAILED: test_price_format

### Data Quality
- Items validated: 50
- Schema errors: 2
  - Item #12: price must be positive
  - Item #45: url is not valid

### Coverage
- Lines: 85%
- Branches: 72%
- Functions: 90%

### Recommendations
1. Fix empty page handling in extractor
2. Update price parser for new format
3. Add fallback selector for product URL
```

## Test Fixtures

Ensure fixtures exist for testing:

```
tests/
├── fixtures/
│   ├── listing_page.html
│   ├── detail_page.html
│   ├── empty_results.html
│   ├── paginated/
│   │   ├── page_1.html
│   │   ├── page_2.html
│   │   └── last_page.html
│   └── edge_cases/
│       ├── special_chars.html
│       ├── missing_fields.html
│       └── malformed.html
└── snapshots/
    └── expected_items.json
```

## Implementation Steps

1. **Discover tests** for the specified scraper
2. **Run unit tests** first (fast feedback)
3. **Run integration tests** with mocked responses
4. **Validate schemas** on extracted data
5. **Run live tests** if --live flag provided
6. **Generate report** with findings

## Self-Verification

After running tests, verify:

- [ ] All unit tests pass
- [ ] Integration tests cover main flows
- [ ] Fixtures represent real page variations
- [ ] Schema validation catches bad data
- [ ] Coverage meets threshold (80%+)
- [ ] Live tests work without rate limiting
