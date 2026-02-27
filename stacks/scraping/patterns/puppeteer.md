# Puppeteer Patterns (Node.js)

## Basic Page Scraping

```javascript
// scrapers/example.js
const puppeteer = require("puppeteer");

async function scrapeArticles(url) {
  const browser = await puppeteer.launch({ headless: "new" });
  const page = await browser.newPage();

  await page.setViewport({ width: 1280, height: 720 });
  await page.goto(url, { waitUntil: "networkidle2" });

  const articles = await page.evaluate(() => {
    return Array.from(document.querySelectorAll("article.post")).map((el) => ({
      title: el.querySelector("h2")?.textContent?.trim(),
      url: el.querySelector("a")?.href,
      summary: el.querySelector("p.summary")?.textContent?.trim(),
    }));
  });

  await browser.close();
  return articles;
}
```

## Waiting for Content

```javascript
// Wait for specific elements
await page.waitForSelector(".results-loaded", { timeout: 10000 });

// Wait for network to be idle
await page.goto(url, { waitUntil: "networkidle0" });

// Wait for a function to return true
await page.waitForFunction(
  () => document.querySelectorAll(".item").length > 10
);

// Custom wait with polling
await page.waitForFunction(
  (selector) => {
    const el = document.querySelector(selector);
    return el && el.textContent.trim() !== "";
  },
  { polling: 500, timeout: 10000 },
  ".dynamic-content"
);
```

## Form Interaction

```javascript
// Login flow
async function login(page, username, password) {
  await page.type("#username", username, { delay: 50 });
  await page.type("#password", password, { delay: 50 });
  await page.click("#login-button");
  await page.waitForNavigation({ waitUntil: "networkidle2" });
}

// Search and scrape
async function search(page, query) {
  await page.type("input[name='q']", query);
  await page.keyboard.press("Enter");
  await page.waitForSelector(".search-results");
}
```

## Pagination

```javascript
async function scrapeAllPages(startUrl) {
  const browser = await puppeteer.launch({ headless: "new" });
  const page = await browser.newPage();
  const allResults = [];

  await page.goto(startUrl, { waitUntil: "networkidle2" });

  while (true) {
    const pageResults = await page.evaluate(() => {
      return Array.from(document.querySelectorAll(".item")).map((el) => ({
        title: el.querySelector("h3")?.textContent?.trim(),
        price: el.querySelector(".price")?.textContent?.trim(),
      }));
    });

    allResults.push(...pageResults);

    const nextButton = await page.$("a.next-page");
    if (!nextButton) break;

    await nextButton.click();
    await page.waitForNavigation({ waitUntil: "networkidle2" });
  }

  await browser.close();
  return allResults;
}
```

## Intercepting Requests

```javascript
// Block images and CSS for faster scraping
await page.setRequestInterception(true);
page.on("request", (req) => {
  if (["image", "stylesheet", "font"].includes(req.resourceType())) {
    req.abort();
  } else {
    req.continue();
  }
});

// Capture API responses
page.on("response", async (response) => {
  if (response.url().includes("/api/data")) {
    const data = await response.json();
    console.log("Captured API data:", data);
  }
});
```

## Screenshot and PDF

```javascript
// Full-page screenshot
await page.screenshot({ path: "page.png", fullPage: true });

// Element screenshot
const element = await page.$(".chart-container");
await element.screenshot({ path: "chart.png" });

// PDF generation
await page.pdf({
  path: "page.pdf",
  format: "A4",
  printBackground: true,
});
```

## Browser Context and Cookies

```javascript
// Persistent session with cookies
const cookies = await page.cookies();
fs.writeFileSync("cookies.json", JSON.stringify(cookies));

// Restore cookies
const savedCookies = JSON.parse(fs.readFileSync("cookies.json", "utf8"));
await page.setCookie(...savedCookies);

// Incognito context
const context = await browser.createBrowserContext();
const page = await context.newPage();
```

## Anti-Detection

```javascript
// Stealth settings
const puppeteer = require("puppeteer-extra");
const StealthPlugin = require("puppeteer-extra-plugin-stealth");
puppeteer.use(StealthPlugin());

// Custom user agent
await page.setUserAgent(
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
);

// Override navigator properties
await page.evaluateOnNewDocument(() => {
  Object.defineProperty(navigator, "webdriver", { get: () => false });
});
```

## Error Handling

```javascript
async function safeScrape(url, retries = 3) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    const browser = await puppeteer.launch({ headless: "new" });
    try {
      const page = await browser.newPage();
      page.setDefaultTimeout(30000);

      const response = await page.goto(url, { waitUntil: "networkidle2" });
      if (!response.ok()) {
        throw new Error(`HTTP ${response.status()}`);
      }

      return await page.evaluate(() => {
        // ... extract data
      });
    } catch (err) {
      console.error(`Attempt ${attempt} failed: ${err.message}`);
      if (attempt === retries) throw err;
      await new Promise((r) => setTimeout(r, 2000 * attempt));
    } finally {
      await browser.close();
    }
  }
}
```

## Key Rules

1. Always close the browser in a `finally` block
2. Use `waitForSelector` or `waitForNavigation` before extracting data
3. Set reasonable timeouts (10-30s) to avoid hanging
4. Block unnecessary resources (images, fonts) for faster scraping
5. Use `page.evaluate()` for DOM extraction (runs in browser context)
6. Implement retry logic with exponential backoff
7. Respect rate limits — add delays between requests
8. Use `headless: "new"` for the latest headless mode
