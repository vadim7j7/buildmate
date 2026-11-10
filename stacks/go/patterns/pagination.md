# Pagination

Two shapes: **offset** (page numbers, total count; fine for admin lists and small tables)
and **keyset / cursor** (stable and fast on large or fast-changing tables, infinite
scroll, public APIs). Use what the project's existing list endpoints use.

---

## 1. Parsing and Clamping Parameters

Never trust `per_page`: clamp it, so one request cannot pull the whole table.

```go
const (
	defaultPerPage = 25
	maxPerPage     = 100
)

type PageParams struct {
	Page    int
	PerPage int
}

func (p PageParams) Offset() int { return (p.Page - 1) * p.PerPage }

// ParsePage reads ?page=&per_page= with defaults and bounds.
func ParsePage(q url.Values) PageParams {
	page, err := strconv.Atoi(q.Get("page"))
	if err != nil || page < 1 {
		page = 1
	}
	perPage, err := strconv.Atoi(q.Get("per_page"))
	if err != nil || perPage < 1 {
		perPage = defaultPerPage
	}
	return PageParams{Page: page, PerPage: min(perPage, maxPerPage)}
}
```

Gin: `ParsePage(c.Request.URL.Query())`; Fiber: bind a query struct with
`validate:"omitempty,min=1,max=100"`, then apply the same defaults.

---

## 2. Offset Pagination

```sql
SELECT id, name, email, created_at FROM users
ORDER BY created_at DESC, id DESC   -- always a unique tiebreaker
LIMIT $1 OFFSET $2;

SELECT count(*) FROM users;
```

Response:

```json
{"data": [...], "meta": {"page": 2, "per_page": 25, "total": 312}}
```

- `ORDER BY` must be deterministic (end with the primary key), or rows repeat or vanish
  across pages
- Large `OFFSET` scans and discards rows; past a few thousand rows switch to keysets
- `count(*)` on big tables is slow: drop `total` or cache it if it shows up in profiles

---

## 3. Keyset (Cursor) Pagination

The cursor encodes the sort key of the last row returned; the next page starts after it.
It is opaque to clients (base64 JSON), so the format can change.

```go
type Cursor struct {
	CreatedAt time.Time `json:"c"`
	ID        int64     `json:"i"`
}

func EncodeCursor(c Cursor) string {
	b, _ := json.Marshal(c) // cannot fail for this struct
	return base64.RawURLEncoding.EncodeToString(b)
}

func DecodeCursor(s string) (Cursor, error) {
	var c Cursor
	b, err := base64.RawURLEncoding.DecodeString(s)
	if err != nil {
		return c, fmt.Errorf("decode cursor: %w", ErrValidation)
	}
	if err := json.Unmarshal(b, &c); err != nil {
		return c, fmt.Errorf("decode cursor: %w", ErrValidation)
	}
	return c, nil
}
```

```sql
-- first page: no WHERE; next pages:
SELECT id, name, created_at FROM users
WHERE (created_at, id) < ($1, $2)          -- row comparison: PostgreSQL, MySQL 8, SQLite 3.15+
ORDER BY created_at DESC, id DESC
LIMIT $3;                                   -- pass per_page + 1
```

Fetch `per_page + 1` rows: if you got the extra row, there is a next page; drop it and
encode the cursor from the last row you return.

```json
{"data": [...], "meta": {"next_cursor": "eyJjIjoi...", "has_more": true}}
```

- Index exactly the sort columns: `CREATE INDEX ON users (created_at DESC, id DESC)`
- An invalid cursor is a 400 (`ErrValidation`), not a 500
- MongoDB: sort on `{created_at: -1, _id: -1}` and filter with `$or` on the same pair,
  or on `_id` alone when it is the only sort key

---

## Rules

- Every list endpoint is paginated, with a server-side maximum page size
- Deterministic `ORDER BY` ending in a unique column
- Same envelope everywhere: `data` plus `meta`
- Filters and sort fields come from allowlists, never interpolated into SQL
