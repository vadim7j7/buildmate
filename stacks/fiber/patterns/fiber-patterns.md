# Fiber Framework Patterns

Reference patterns for Fiber web development. Agents should read this file
before writing code to ensure consistency across the codebase.

---

## 1. Route Group Pattern

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

## 2. Middleware Pattern

Middleware returns `fiber.Handler` which is `func(*fiber.Ctx) error`.

```go
func RequestID() fiber.Handler {
	return func(c *fiber.Ctx) error {
		id := c.Get("X-Request-ID")
		if id == "" {
			id = uuid.New().String()
		}
		c.Locals("request_id", id)
		c.Set("X-Request-ID", id)
		return c.Next()
	}
}
```

### Rules
- Return `fiber.Handler`
- Call `c.Next()` to continue chain
- Return error to abort (or use early `c.Status().JSON()`)
- Store values with `c.Locals()`, retrieve with `c.Locals()`

---

## 3. Ctx Handler Pattern

All handlers work with `*fiber.Ctx` and return `error`.

```go
func (h *UserHandler) List(c *fiber.Ctx) error {
	page := c.QueryInt("page", 1)
	perPage := c.QueryInt("per_page", 25)

	users, total, err := h.svc.ListUsers(c.UserContext(), page, perPage)
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
- Use `c.BodyParser()` for request bodies
- Use `c.Params()`, `c.Query()`, `c.QueryInt()` for URL params
- Use `c.UserContext()` to pass context to services

---

## 4. Error Handler Pattern

Custom error handler for the Fiber app.

```go
func CustomErrorHandler(c *fiber.Ctx, err error) error {
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

## 5. Config / Prefork Pattern

Production Fiber configuration with prefork.

```go
app := fiber.New(fiber.Config{
	Prefork:       cfg.Environment == "production",
	StrictRouting: true,
	CaseSensitive: true,
	ReadTimeout:   cfg.ReadTimeout,
	WriteTimeout:  cfg.WriteTimeout,
	ErrorHandler:  CustomErrorHandler,
})
```

### Rules
- Enable `Prefork` in production for multi-core utilization
- Set timeouts for read and write
- Enable `StrictRouting` and `CaseSensitive`
- Set custom `ErrorHandler`

---

## 6. Validation Pattern

Use go-playground/validator for struct validation.

```go
package handler

import "github.com/go-playground/validator/v10"

var validate = validator.New()

type CreateUserRequest struct {
	Name  string `json:"name" validate:"required,min=2,max=100"`
	Email string `json:"email" validate:"required,email"`
}

func (h *UserHandler) Create(c *fiber.Ctx) error {
	var input CreateUserRequest
	if err := c.BodyParser(&input); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "invalid request body",
		})
	}

	if err := validate.Struct(&input); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": formatValidationErrors(err),
		})
	}

	// proceed with service call...
}
```

### Rules
- Use `validate` struct tags (not `binding` like Gin)
- Parse body first with `c.BodyParser()`, then validate with `validate.Struct()`
- Return formatted validation errors
