# Security in Nuxt 4

Read this when a task adds a server route, a form, user-generated content, runtime
config, or third-party scripts. Auth details: `nuxt-auth.md`.

## Server Routes Are Public Endpoints

Anything under `server/api/` can be called by anyone with any input.

- **Authenticate** in the handler (`requireUserSession(event)`), not only in page middleware.
- **Authorize** the specific record: scope queries by owner/tenant.
- **Validate** every input with Zod: `readValidatedBody`, `getValidatedQuery`,
  `getValidatedRouterParams`. Never spread a raw body into a DB write (mass assignment):
  pick fields through the schema.
- **Return only what the client needs**: map DB rows to DTOs; never return password
  hashes, tokens or internal ids of other tenants.
- Error responses carry a generic `statusMessage`; log details on the server.

## Secrets and Runtime Config

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  runtimeConfig: {
    apiSecret: '',            // server-only; set via NUXT_API_SECRET
    public: {
      apiBase: '/api',        // exposed to the browser: never put secrets here
    },
  },
});
```

- Server code reads `useRuntimeConfig(event).apiSecret`; client code only sees `public`.
- Don't import from `server/` into `app/`; server-only helpers stay in `server/utils/`.
- `.env` is not committed; production values come from the platform's env vars.

## XSS

- Vue escapes `{{ }}` interpolation. `v-html` does not: only use it with content
  sanitized on the server (e.g. DOMPurify / sanitize-html with an allow-list).
- Never bind user input to `:href` / `:src` without checking the scheme
  (`javascript:` URLs); allow `http:`, `https:`, `mailto:` only.
- `useHead({ script: [{ innerHTML }] })` with user data is XSS; serialize with
  `JSON.stringify` and only for trusted data.

## Security Headers, CSRF, Rate Limiting

The `nuxt-security` module covers the common set (CSP, HSTS, `X-Frame-Options`,
CSRF via `nuxt-csurf`, a basic rate limiter, request size limits):

```bash
npx nuxi module add security
```

```ts
export default defineNuxtConfig({
  modules: ['nuxt-security'],
  security: {
    rateLimiter: { tokensPerInterval: 150, interval: 300000 },
    headers: {
      contentSecurityPolicy: { 'img-src': ["'self'", 'data:', 'https:'] },
    },
  },
});
```

- Session cookies are `httpOnly`, `secure`, `sameSite=lax` (nuxt-auth-utils defaults);
  state-changing requests are POST/PUT/PATCH/DELETE, never GET.
- Put a stricter per-route limit on login, sign-up, password reset and contact forms.
- Behind a proxy, rate limiting and IP logging need the real client IP
  (`getRequestIP(event, { xForwardedFor: true })` only when the proxy is trusted).

## Outbound Requests (SSRF)

A server route that fetches a URL the user supplied can reach internal services.
Allow-list hosts, reject private IP ranges, and set a timeout:
`$fetch(url, { timeout: 5000 })`.

## Checklist

- [ ] Every private server route checks the session and scopes by owner/tenant
- [ ] All input parsed with Zod; DB writes use parsed fields only
- [ ] No secrets in `runtimeConfig.public` or client bundles
- [ ] No unsanitized `v-html`; user URLs checked for scheme
- [ ] Auth endpoints rate-limited
- [ ] Responses mapped to DTOs (no hashes/tokens)
