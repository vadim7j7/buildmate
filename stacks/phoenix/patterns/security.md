# Phoenix Security

What Phoenix gives you, what you must not turn off, and what is still on you.
Authentication and scopes: `auth.md`.

---

## 1. Input: Changesets and Params

- All external input goes through a changeset: `cast/4` with an explicit field list is the
  allowlist. Never cast `:user_id`, `:role`, `:admin`, `:org_id` from params; set them
  from the scope or in a separate admin-only changeset
- Validate lengths and formats (`validate_length/3`, `validate_format/3`,
  `validate_inclusion/3`); mirror DB constraints (`unique_constraint/3`)
- Non-schema input (filters, search forms): a schemaless changeset
  (`{%{}, types} |> cast(params, Map.keys(types))`) instead of reading `params` raw
- Never `String.to_atom/1` on params (see `pitfalls.md`); sort/filter fields from an
  allowlist map

---

## 2. Queries

- Ecto queries are parameterized: interpolate only with `^value`
- `fragment/1` with user input: pass it as a parameter (`fragment("lower(?)", ^term)`),
  never build the SQL string. `Ecto.Adapters.SQL.query/3` likewise takes params
- `LIKE` searches: escape `%` and `_` in the user's term
- Every query for owned data filters on the scope (`where: p.user_id == ^scope.user.id`);
  a record of another user is a 404, not a 403

---

## 3. Output and Templates

- HEEx escapes everything by default. `raw/1` and `Phoenix.HTML.raw` on user content is an
  XSS hole; if you must render user HTML, sanitize it first (e.g. `html_sanitize_ex`)
- Links from user input: allow only `http`/`https` schemes before rendering `href`
- JSON views list fields explicitly; never `Jason.encode!(struct)` with all fields
  (`@derive {Jason.Encoder, only: [...]}` if you encode schemas)

---

## 4. Browser Protections (keep them on)

- `:protect_from_forgery` in the `:browser` pipeline (CSRF); LiveView forms carry the token
  automatically. Do not move state-changing routes into a pipeline without it
- `:put_secure_browser_headers`; add a Content-Security-Policy that fits your assets
- Session cookie: signed (`signing_salt`), `same_site: "Lax"`; set `secure: true` and
  `force_ssl: [hsts: true]` in production
- CORS for an API: an explicit origin list (e.g. `cors_plug` with `origin: [...]`), never `*`
  with credentials
- WebSockets: `check_origin` stays enabled in production (`config :my_app, MyAppWeb.Endpoint,
  check_origin: ["https://example.com"]`)

---

## 5. Secrets and Config

- Secrets come from the environment in `config/runtime.exs` (`System.fetch_env!/1`), never
  in `config/*.exs` compiled into the release or committed
- `secret_key_base` from `mix phx.gen.secret`, per environment
- Keep `:password`, tokens and other secrets in `config :phoenix, :filter_parameters`
  so they are not logged
- `Logger` metadata and error reports: no tokens, no full params

---

## 6. Rate Limiting and Abuse

- Throttle login, registration, password reset and magic-link requests per IP and per
  email. A plug with a library such as `hammer` is the usual choice; check its current
  API before adding it
- Behind a proxy, read the client IP with `remote_ip` (or a plug configured with your
  proxy list); never trust `x-forwarded-for` from everyone

---

## 7. Dependencies

```bash
mix hex.audit                 # retired packages
mix deps.unlock --check-unused
```

`mix_audit` (`mix deps.audit`) and `sobelow` (Phoenix-specific static analysis,
`mix sobelow --config`) are worth adding to CI if the project uses them.

---

## Rules

- Changeset `cast` lists are allowlists; ownership fields come from the scope
- Never `raw/1` user content; never disable CSRF or `check_origin` to "fix" a bug
- Secrets only in `runtime.exs` via env vars, filtered from logs
