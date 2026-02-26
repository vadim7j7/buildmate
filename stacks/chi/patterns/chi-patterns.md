# Chi Router Patterns

Reference patterns for Chi web development. Agents should read this file
before writing code to ensure consistency across the codebase.

---

## 1. Sub-Router Pattern

Use `r.Route()` for grouping routes with a shared prefix.

```go
r.Route("/api/v1", func(r chi.Router) {
	r.Route("/users", func(r chi.Router) {
		r.Get("/", h.User.List)
		r.Post("/", h.User.Create)
		r.Route("/{id}", func(r chi.Router) {
			r.Get("/", h.User.Get)
			r.Put("/", h.User.Update)
			r.Delete("/", h.User.Delete)
		})
	})
})
```

### Rules
- Nest routes with `r.Route()` for clean URL hierarchies
- Use `{param}` syntax for URL parameters
- Version API routes under `/api/v1/`

---

## 2. Middleware Stack Pattern

Chi uses standard `func(http.Handler) http.Handler` middleware.

```go
func RequestLogger(logger *slog.Logger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()

			ww := middleware.NewWrapResponseWriter(w, r.ProtoMajor)
			next.ServeHTTP(ww, r)

			logger.Info("request",
				"method", r.Method,
				"path", r.URL.Path,
				"status", ww.Status(),
				"duration", time.Since(start),
			)
		})
	}
}
```

### Rules
- Standard `http.Handler` middleware signature
- Call `next.ServeHTTP(w, r)` to continue chain
- Don't call `next` to abort
- Use Chi's `middleware.NewWrapResponseWriter` for status capture

---

## 3. Route Parameters

Access URL parameters with `chi.URLParam()`.

```go
func (h *UserHandler) Get(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	user, err := h.svc.GetUser(r.Context(), id)
	if err != nil {
		handleError(w, err)
		return
	}
	respondJSON(w, http.StatusOK, user)
}
```

### Rules
- Use `chi.URLParam(r, "name")` for path parameters
- Use `r.URL.Query().Get("name")` for query parameters
- Parse and validate at the handler level

---

## 4. Resource Pattern

Encapsulate related routes in a struct with a `Routes()` method.

```go
type ArticleResource struct {
	svc service.ArticleService
}

func (rs *ArticleResource) Routes() chi.Router {
	r := chi.NewRouter()

	r.Get("/", rs.List)
	r.Post("/", rs.Create)
	r.Route("/{articleID}", func(r chi.Router) {
		r.Use(rs.ArticleCtx)
		r.Get("/", rs.Get)
		r.Put("/", rs.Update)
		r.Delete("/", rs.Delete)
	})

	return r
}

// Mount: r.Mount("/articles", articleResource.Routes())
```

### Rules
- Each resource gets its own struct and `Routes()` method
- Mount with `r.Mount()` in the main router
- Use resource-scoped middleware (e.g., `ArticleCtx`) for shared lookups

---

## 5. Context Values Pattern

Pass data between middleware and handlers using context.

```go
type contextKey string

const userIDKey contextKey = "userID"

// Middleware sets context value
func AuthMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		userID := extractUserID(r)
		ctx := context.WithValue(r.Context(), userIDKey, userID)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// Handler reads context value
func (h *Handler) Get(w http.ResponseWriter, r *http.Request) {
	userID, ok := r.Context().Value(userIDKey).(string)
	if !ok {
		respondError(w, http.StatusUnauthorized, "unauthorized")
		return
	}
	// use userID...
}
```

### Rules
- Define typed context keys (unexported `contextKey` type)
- Type-assert context values with comma-ok pattern
- Set values with `context.WithValue`, read with `r.Context().Value()`

---

## 6. Testing Pattern

Test Chi handlers with `httptest` and standard Go testing.

```go
func TestUserHandler_Get(t *testing.T) {
	svc := &mockUserService{
		users: []User{{ID: "1", Name: "Alice"}},
	}
	h := NewUserHandler(svc)

	r := chi.NewRouter()
	r.Get("/users/{id}", h.Get)

	req := httptest.NewRequest(http.MethodGet, "/users/1", nil)
	w := httptest.NewRecorder()

	r.ServeHTTP(w, req)

	require.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Body.String(), "Alice")
}
```

### Rules
- Create a Chi router in tests for proper URL param parsing
- Use `httptest.NewRequest` and `httptest.NewRecorder`
- Call `r.ServeHTTP(w, req)` instead of calling handler directly
- Table-driven tests for multiple scenarios
