# /clone-page

Download and save a webpage locally for offline analysis and testing.

## Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `url` | URL to clone | Yes |
| `--name` | Name for saved files | No |
| `--assets` | Download assets (images, CSS, JS) | No |
| `--render` | Render JavaScript before saving | No |
| `--output` | Output directory | No |

## Examples

```bash
/clone-page https://example.com/products
/clone-page https://example.com/products --name product-listing
/clone-page https://example.com/product/123 --render --assets
/clone-page https://example.com --output fixtures/
```

## Use Cases

### 1. Test Fixtures

Create stable HTML fixtures for unit tests:

```bash
/clone-page https://example.com/product/123 --name product-detail
```

Creates:
```
tests/fixtures/
└── product-detail.html
```

### 2. Offline Development

Work on selectors without hitting live server:

```bash
/clone-page https://example.com/products --assets --name products
```

Creates:
```
tests/fixtures/
├── products.html
└── products_assets/
    ├── styles.css
    ├── logo.png
    └── app.js
```

### 3. JavaScript-Rendered Pages

For SPAs that require JavaScript:

```bash
/clone-page https://spa-example.com/products --render --name spa-products
```

Captures the fully rendered DOM after JavaScript execution.

### 4. Snapshot Comparison

Track changes to target pages over time:

```bash
/clone-page https://example.com/products --name products-$(date +%Y%m%d)
```

## Implementation

{% if variables.language == 'Python' %}
### HTTP Download

```python
import httpx
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

async def clone_page(url: str, output_dir: Path, name: str, include_assets: bool = False):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()

        html = response.text
        soup = BeautifulSoup(html, "lxml")

        if include_assets:
            html = await download_assets(soup, url, output_dir / f"{name}_assets", client)

        output_path = output_dir / f"{name}.html"
        output_path.write_text(html)
        print(f"Saved: {output_path}")

async def download_assets(soup: BeautifulSoup, base_url: str, assets_dir: Path, client):
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Download and rewrite image sources
    for img in soup.find_all("img", src=True):
        asset_url = urljoin(base_url, img["src"])
        local_path = await download_asset(asset_url, assets_dir, client)
        img["src"] = str(local_path.relative_to(assets_dir.parent))

    # Similar for CSS, JS...
    return str(soup)
```

### Browser Render

```python
from playwright.async_api import async_playwright

async def clone_rendered_page(url: str, output_dir: Path, name: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.goto(url, wait_until="networkidle")

        # Get rendered HTML
        html = await page.content()

        output_path = output_dir / f"{name}.html"
        output_path.write_text(html)

        await browser.close()
        print(f"Saved (rendered): {output_path}")
```

{% else %}
### HTTP Download

```typescript
import axios from 'axios';
import * as cheerio from 'cheerio';
import * as fs from 'fs/promises';
import * as path from 'path';

async function clonePage(
  url: string,
  outputDir: string,
  name: string,
  includeAssets = false
): Promise<void> {
  const response = await axios.get(url);
  let html = response.data;

  if (includeAssets) {
    const $ = cheerio.load(html);
    await downloadAssets($, url, path.join(outputDir, `${name}_assets`));
    html = $.html();
  }

  const outputPath = path.join(outputDir, `${name}.html`);
  await fs.mkdir(outputDir, { recursive: true });
  await fs.writeFile(outputPath, html);
  console.log(`Saved: ${outputPath}`);
}
```

### Browser Render

```typescript
import { chromium } from 'playwright';
import * as fs from 'fs/promises';
import * as path from 'path';

async function cloneRenderedPage(
  url: string,
  outputDir: string,
  name: string
): Promise<void> {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  await page.goto(url, { waitUntil: 'networkidle' });

  const html = await page.content();

  const outputPath = path.join(outputDir, `${name}.html`);
  await fs.mkdir(outputDir, { recursive: true });
  await fs.writeFile(outputPath, html);

  await browser.close();
  console.log(`Saved (rendered): ${outputPath}`);
}
```
{% endif %}

## Output Structure

```
tests/
└── fixtures/
    ├── product-listing.html          # Main page
    ├── product-listing_assets/       # Assets (if --assets)
    │   ├── style.css
    │   ├── main.js
    │   └── images/
    │       ├── logo.png
    │       └── product-1.jpg
    ├── product-detail.html
    └── search-results.html
```

## Best Practices

1. **Name descriptively** - Use meaningful names for easy identification
2. **Include timestamps** - For change tracking over time
3. **Use --render sparingly** - Slower, only for JS-dependent pages
4. **Organize by page type** - Group similar pages together
5. **Document source URLs** - Add comments with original URLs

## Self-Verification

After cloning, verify:

- [ ] HTML file saved correctly
- [ ] Assets downloaded (if requested)
- [ ] Relative paths work locally
- [ ] JavaScript-rendered content captured (if --render)
- [ ] File can be opened in browser
- [ ] Selectors work on local copy
