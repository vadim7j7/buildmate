# Fiber Framework Patterns

Reference patterns for Fiber v3 web development (`github.com/gofiber/fiber/v3`).
Agents should read this file before writing code to ensure consistency across
the codebase. If the project's `go.mod` still uses `fiber/v2`, follow the v2
API there (`*fiber.Ctx`, `c.BodyParser`, `c.UserContext()`) and do not mix majors.

---

## 1. Server Entry Point

`cmd/server/main.go` reads `PORT` (default `8080`), serves `GET /health`, and
shuts down gracefully. The dev server is `PORT=8080 go run ./cmd/server`.

```go
func run() error {
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	app := fiber.New(fiber.Config{
		ErrorHandler:    handler.ErrorHandler,
		StructValidator: structValidator{v: validator.New()},
	})
	app.Use(requestid.New(), logger.New(), recoverer.New())
	app.Get("/health", func(c fiber.Ctx) error {
		return c.JSON(fiber.Map{"status": "ok"})
	})
	router.SetupRoutes(app, h, mw)

	errCh := make(chan error, 1)
	go func() { errCh <- app.Listen(":"+port, fiber.ListenConfig{DisableStartupMessage: true}) }()

	select {
	case err := <-errCh:
		return err
	case <-ctx.Done():
	}

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	return app.ShutdownWithContext(shutdownCtx)
}
```

### Rules
- `GET /health` returns `200` with a JSON body, outside auth middleware
- `signal.NotifyContext` + `app.ShutdownWithContext` with a timeout
- Import `recover` middleware under an alias (`recoverer`) so it does not shadow the builtin

---

## 2. Route Group Pattern

Organize routes with shared prefix and middleware.

```go
func SetupRoutes(app *fiber.App, h *handler.Handler, mw *middleware.Middleware) {
	api := app.Group("/api/v1")

	auth := api.Group("/auth")
	auth.Post("/login", h.Auth.Login)
	auth.Post("/register", h.Auth.Register)

	users := api.Group("/users", mw.Auth())
	users.Get("/", h.User.List)
	users.Get("/:id", h.User.Get)
	users.Post("/", h.User.Create)
	users.Put("/:id", h.User.Update)
	users.Delete("/:id", h.User.Delete)
}
```

### Rules
- Use `app.Group()` with prefix and optional middleware
- RESTful naming conventions
- Version API routes

---

## 3. Middleware Pattern

Middleware returns `fiber.Handler`, which is `func(fiber.Ctx) error` in v3.
Prefer the built-in `requestid`, `logger`, `recover`, `cors` middleware; write
your own only for app concerns such as auth.

```go
func (m *Middleware) Auth() fiber.Handler {
	return func(c fiber.Ctx) error {
		claims, err := m.tokenService.Validate(c.Get("Authorization"))
		if err != nil {
			return fiber.NewError(fiber.StatusUnauthorized, "invalid token")
		}
		fiber.Locals[string](c, "user_id", claims.UserID)
		return c.Next()
	}
}
```

### Rules
- Return `fiber.Handler`
- Call `c.Next()` to continue chain
- Return an error (e.g. `fiber.NewError`) to abort, or respond early with `c.Status().JSON()`
- Store/read values with the typed `fiber.Locals[T](c, key[, value])`
- Read built-in middleware data with its helper, e.g. `requestid.FromContext(c)`

---

## 4. Ctx Handler Pattern

All handlers take `c fiber.Ctx` (an interface, not a pointer) and return `error`.

```go
func (h *UserHandler) List(c fiber.Ctx) error {
	page := fiber.Query[int](c, "page", 1)
	perPage := fiber.Query[int](c, "per_page", 25)

	// fiber.Ctx implements context.Context.
	users, total, err := h.svc.ListUsers(c, page, perPage)
	if err != nil {
		return handleError(c, err)
	}

	return c.JSON(fiber.Map{
		"data":  toUserResponses(users),
		"total": total,
		"page":  page,
	})
}
```

### Rules
- Always return `error` from handlers
- Use `c.Bind().Body(&in)` for request bodies (also `Bind().Query`, `Bind().URI`)
- Use `c.Params()`, `c.Query()`, `fiber.Params[T]`, `fiber.Query[T]` for URL params
- Pass `c` as the `context.Context` to services (`UserContext()` is gone in v3)

---

## 5. Zero-Copy Values

Fiber (v2 and v3) is built on fasthttp and reuses request buffers. Strings and
byte slices returned by `c.Params()`, `c.Query()`, `c.Get()`, `c.Body()`,
`c.FormValue()` are **only valid until the handler returns**.

```go
// BAD - the value may change after the handler returns
h.cache.Set(c.Params("id"), user)
go audit(c.Query("ref"))

// GOOD - copy before it escapes the handler
id := strings.Clone(c.Params("id"))
h.cache.Set(id, user)
```

### Rules
- Copy with `strings.Clone` / `bytes.Clone` (or `utils.CopyString`) before storing a value
  in a struct, map, cache, channel or goroutine
- Or set `fiber.Config{Immutable: true}` app-wide (small performance cost)
- Never keep `c` itself after the handler returns

---

## 6. Error Handler Pattern

Custom error handler for the Fiber app.

```go
func ErrorHandler(c fiber.Ctx, err error) error {
	code := fiber.StatusInternalServerError

	var e *fiber.Error
	if errors.As(err, &e) {
		code = e.Code
	}

	return c.Status(code).JSON(fiber.Map{
		"error": err.Error(),
	})
}
```

---

## 7. Config Pattern

```go
app := fiber.New(fiber.Config{
	StrictRouting:   true,
	CaseSensitive:   true,
	ReadTimeout:     cfg.ReadTimeout,
	WriteTimeout:    cfg.WriteTimeout,
	ErrorHandler:    ErrorHandler,
	StructValidator: structValidator{v: validator.New()},
})
```

### Rules
- Set timeouts for read and write
- Enable `StrictRouting` and `CaseSensitive`
- Set custom `ErrorHandler` and `StructValidator`
- Prefork (`fiber.ListenConfig{EnablePrefork: true}`) only when you know you need it:
  it forks processes, which breaks in-process state and complicates graceful shutdown

---

## 8. Validation Pattern

Use go-playground/validator through Fiber's `StructValidator` hook so that
`c.Bind()` validates automatically.

```go
import "github.com/go-playground/validator/v10"

type structValidator struct{ v *validator.Validate }

func (s structValidator) Validate(out any) error { return s.v.Struct(out) }

type CreateUserRequest struct {
	Name  string `json:"name" validate:"required,min=2,max=100"`
	Email string `json:"email" validate:"required,email"`
}

func (h *UserHandler) Create(c fiber.Ctx) error {
	var input CreateUserRequest
	if err := c.Bind().Body(&input); err != nil { // parse + validate
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": formatValidationErrors(err),
		})
	}

	// proceed with service call...
}
```

### Rules
- Use `validate` struct tags (not `binding` like Gin)
- Register the validator once in `fiber.Config.StructValidator`
- Return formatted validation errors
