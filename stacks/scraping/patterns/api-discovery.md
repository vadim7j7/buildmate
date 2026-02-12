# API Discovery Pattern

Patterns for discovering and mapping API endpoints from websites.

## Network Analysis

### Intercept API Calls

```javascript
// Override fetch to capture API calls
const originalFetch = window.fetch;
const apiCalls = [];

window.fetch = async (...args) => {
  const [url, options = {}] = args;
  const method = options.method || 'GET';

  const response = await originalFetch(...args);

  // Clone response to read body
  const clone = response.clone();
  let body = null;
  try {
    body = await clone.json();
  } catch {}

  apiCalls.push({
    url: typeof url === 'string' ? url : url.url,
    method,
    requestBody: options.body ? JSON.parse(options.body) : null,
    responseBody: body,
    status: response.status,
    timestamp: Date.now(),
  });

  return response;
};

// Also intercept XMLHttpRequest
const originalXHR = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function(method, url) {
  this._apiData = { method, url };
  return originalXHR.apply(this, arguments);
};
```

### Playwright Network Interception

```typescript
import { chromium } from 'playwright';

async function captureAPICalls(url: string) {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  const apiCalls: ApiCall[] = [];

  // Intercept all requests
  page.on('request', request => {
    const url = request.url();
    if (url.includes('/api/') || url.includes('/graphql')) {
      apiCalls.push({
        url,
        method: request.method(),
        headers: request.headers(),
        postData: request.postData(),
      });
    }
  });

  // Capture responses
  page.on('response', async response => {
    const url = response.url();
    if (url.includes('/api/') || url.includes('/graphql')) {
      const call = apiCalls.find(c => c.url === url);
      if (call) {
        try {
          call.response = await response.json();
          call.status = response.status();
        } catch {}
      }
    }
  });

  await page.goto(url, { waitUntil: 'networkidle' });

  // Trigger interactions to discover more endpoints
  await triggerInteractions(page);

  await browser.close();
  return apiCalls;
}

async function triggerInteractions(page: Page) {
  // Click buttons that might load data
  const buttons = await page.$$('button:not([type="submit"])');
  for (const button of buttons.slice(0, 5)) {
    try {
      await button.click();
      await page.waitForTimeout(500);
    } catch {}
  }

  // Scroll to trigger lazy loading
  await page.evaluate(async () => {
    for (let i = 0; i < 5; i++) {
      window.scrollBy(0, window.innerHeight);
      await new Promise(r => setTimeout(r, 500));
    }
  });
}
```

## Endpoint Analysis

### Parse REST Endpoints

```typescript
interface RestEndpoint {
  method: string;
  path: string;
  params: PathParam[];
  queryParams: QueryParam[];
  requestBody: Schema | null;
  responseBody: Schema;
}

function analyzeEndpoint(call: ApiCall): RestEndpoint {
  const url = new URL(call.url);
  const pathParts = url.pathname.split('/').filter(Boolean);

  // Identify path parameters (UUIDs, numbers, slugs)
  const params: PathParam[] = [];
  const normalizedPath = pathParts.map((part, i) => {
    if (isUUID(part)) {
      params.push({ name: `${pathParts[i - 1]}Id`, type: 'uuid', position: i });
      return ':id';
    }
    if (/^\d+$/.test(part)) {
      params.push({ name: `${pathParts[i - 1]}Id`, type: 'number', position: i });
      return ':id';
    }
    return part;
  });

  // Parse query parameters
  const queryParams: QueryParam[] = [];
  url.searchParams.forEach((value, key) => {
    queryParams.push({
      name: key,
      type: inferType(value),
      example: value,
    });
  });

  return {
    method: call.method,
    path: '/' + normalizedPath.join('/'),
    params,
    queryParams,
    requestBody: call.requestBody ? inferSchema(call.requestBody) : null,
    responseBody: inferSchema(call.response),
  };
}

function isUUID(str: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(str);
}
```

### Infer Schema from Response

```typescript
interface Schema {
  type: 'object' | 'array' | 'string' | 'number' | 'boolean' | 'null';
  properties?: Record<string, Schema>;
  items?: Schema;
  required?: string[];
}

function inferSchema(data: unknown): Schema {
  if (data === null) return { type: 'null' };
  if (Array.isArray(data)) {
    if (data.length === 0) return { type: 'array', items: { type: 'object' } };
    return { type: 'array', items: inferSchema(data[0]) };
  }
  if (typeof data === 'object') {
    const properties: Record<string, Schema> = {};
    const required: string[] = [];

    for (const [key, value] of Object.entries(data)) {
      properties[key] = inferSchema(value);
      if (value !== null && value !== undefined) {
        required.push(key);
      }
    }

    return { type: 'object', properties, required };
  }
  if (typeof data === 'number') return { type: 'number' };
  if (typeof data === 'boolean') return { type: 'boolean' };
  return { type: 'string' };
}

function inferType(value: string): string {
  if (/^\d+$/.test(value)) return 'integer';
  if (/^\d+\.\d+$/.test(value)) return 'number';
  if (value === 'true' || value === 'false') return 'boolean';
  if (isUUID(value)) return 'uuid';
  return 'string';
}
```

## Form Analysis

### Extract Form Endpoints

```javascript
function analyzeForm(form) {
  const action = form.action || window.location.href;
  const method = form.method?.toUpperCase() || 'POST';

  const fields = [];
  form.querySelectorAll('input, select, textarea').forEach(input => {
    if (input.name) {
      fields.push({
        name: input.name,
        type: input.type || 'text',
        required: input.required,
        pattern: input.pattern,
        validation: extractValidation(input),
      });
    }
  });

  return {
    action,
    method,
    fields,
    endpoint: deriveEndpoint(action, method),
  };
}

function extractValidation(input) {
  const rules = [];

  if (input.required) rules.push('required');
  if (input.minLength) rules.push(`minLength:${input.minLength}`);
  if (input.maxLength) rules.push(`maxLength:${input.maxLength}`);
  if (input.min) rules.push(`min:${input.min}`);
  if (input.max) rules.push(`max:${input.max}`);
  if (input.pattern) rules.push(`pattern:${input.pattern}`);
  if (input.type === 'email') rules.push('email');
  if (input.type === 'url') rules.push('url');

  return rules;
}
```

## GraphQL Detection

### Detect GraphQL Endpoint

```javascript
function detectGraphQL() {
  // Check for common GraphQL endpoints
  const graphqlPaths = ['/graphql', '/api/graphql', '/gql'];
  const found = [];

  // Check if any scripts reference GraphQL
  document.querySelectorAll('script').forEach(script => {
    const content = script.textContent || '';
    if (content.includes('graphql') || content.includes('__schema')) {
      found.push({ type: 'inline_script', content: content.slice(0, 200) });
    }
  });

  // Check for Apollo Client
  if (window.__APOLLO_CLIENT__) {
    found.push({
      type: 'apollo',
      cache: window.__APOLLO_CLIENT__.cache.extract(),
    });
  }

  return found;
}
```

### Extract GraphQL Operations

```typescript
// From network interception
function parseGraphQLOperation(request: ApiCall) {
  if (!request.requestBody?.query) return null;

  const query = request.requestBody.query;
  const variables = request.requestBody.variables;

  // Parse operation type and name
  const match = query.match(/(query|mutation|subscription)\s+(\w+)?/);
  if (!match) return null;

  return {
    type: match[1],
    name: match[2] || 'anonymous',
    query,
    variables,
    response: request.response,
  };
}
```

## Data Model Inference

### Build Data Models from API Responses

```typescript
interface DataModel {
  name: string;
  fields: Field[];
  relationships: Relationship[];
}

function inferDataModels(endpoints: RestEndpoint[]): DataModel[] {
  const models = new Map<string, DataModel>();

  endpoints.forEach(endpoint => {
    // Extract model name from path
    const pathParts = endpoint.path.split('/').filter(p => p && !p.startsWith(':'));
    const resourceName = pathParts[pathParts.length - 1];
    const modelName = singularize(capitalize(resourceName));

    // Get schema from response
    const schema = endpoint.responseBody;
    if (schema.type === 'object') {
      mergeModel(models, modelName, schema);
    } else if (schema.type === 'array' && schema.items?.type === 'object') {
      mergeModel(models, modelName, schema.items);
    }
  });

  return [...models.values()];
}

function mergeModel(models: Map<string, DataModel>, name: string, schema: Schema) {
  if (!models.has(name)) {
    models.set(name, { name, fields: [], relationships: [] });
  }

  const model = models.get(name)!;

  for (const [key, value] of Object.entries(schema.properties || {})) {
    // Check if field already exists
    if (model.fields.some(f => f.name === key)) continue;

    // Detect relationships
    if (value.type === 'object' && key !== name.toLowerCase()) {
      model.relationships.push({
        name: key,
        type: 'belongsTo',
        model: capitalize(key),
      });
    } else if (value.type === 'array' && value.items?.type === 'object') {
      model.relationships.push({
        name: key,
        type: 'hasMany',
        model: singularize(capitalize(key)),
      });
    } else {
      model.fields.push({
        name: key,
        type: mapSchemaType(value),
        required: schema.required?.includes(key) || false,
      });
    }
  }
}
```

## Output Format

### API Documentation

```json
{
  "baseUrl": "https://api.example.com",
  "version": "v1",
  "authentication": {
    "type": "bearer",
    "header": "Authorization"
  },
  "endpoints": [
    {
      "method": "GET",
      "path": "/api/products",
      "description": "List all products",
      "queryParams": [
        {"name": "page", "type": "integer", "required": false},
        {"name": "limit", "type": "integer", "required": false},
        {"name": "category", "type": "string", "required": false}
      ],
      "response": {
        "type": "array",
        "items": {"$ref": "#/models/Product"}
      }
    },
    {
      "method": "GET",
      "path": "/api/products/:id",
      "description": "Get single product",
      "pathParams": [
        {"name": "id", "type": "uuid", "required": true}
      ],
      "response": {"$ref": "#/models/Product"}
    },
    {
      "method": "POST",
      "path": "/api/cart",
      "description": "Add item to cart",
      "authentication": true,
      "requestBody": {
        "productId": {"type": "uuid", "required": true},
        "quantity": {"type": "integer", "required": true}
      },
      "response": {"$ref": "#/models/Cart"}
    }
  ],
  "models": {
    "Product": {
      "fields": [
        {"name": "id", "type": "uuid"},
        {"name": "name", "type": "string"},
        {"name": "price", "type": "number"},
        {"name": "image", "type": "string"},
        {"name": "inStock", "type": "boolean"}
      ],
      "relationships": [
        {"name": "category", "type": "belongsTo", "model": "Category"}
      ]
    },
    "Category": {
      "fields": [
        {"name": "id", "type": "uuid"},
        {"name": "name", "type": "string"},
        {"name": "slug", "type": "string"}
      ]
    }
  }
}
```

## Best Practices

1. **Trigger all interactions** - Click buttons, submit forms, scroll to load more
2. **Respect rate limits** - Add delays between requests
3. **Handle authentication** - Note which endpoints require auth
4. **Capture error responses** - Understand error formats
5. **Look for patterns** - REST naming, pagination, filtering
6. **Check for GraphQL** - Many modern sites use GraphQL
7. **Analyze WebSocket** - Check for real-time connections
8. **Document thoroughly** - Include examples of requests/responses
