# Gin Framework Patterns

Reference patterns for Gin web development. Agents should read this file
before writing code to ensure consistency across the codebase.

---

## 1. Router Group Pattern

Organize routes into logical groups with shared middleware.

```go
func SetupRouter(h *handler.Handler, mw *middleware.Middleware) *gin.Engine {
	r := gin.Default()

	api := r.Group("/api/v1")
	{
		auth := api.Group("/auth")
		{
			auth.POST("/login", h.Auth.Login)
			auth.POST("/register", h.Auth.Register)
		}

		users := api.Group("/users")
		users.Use(mw.Auth())
		{
			users.GET("", h.User.List)
			users.GET("/:id", h.User.Get)
			users.POST("", h.User.Create)
			users.PUT("/:id", h.User.Update)
			users.DELETE("/:id", h.User.Delete)
		}
	}

	return r
}
```

### Rules
- Group related routes under a shared prefix
- Apply middleware at the group level
- Use RESTful route naming conventions
- Version API routes (`/api/v1/`)

---

## 2. Middleware Pattern

Write middleware as functions returning `gin.HandlerFunc`.

```go
func RateLimiter(maxRequests int, window time.Duration) gin.HandlerFunc {
	limiter := rate.NewLimiter(rate.Every(window/time.Duration(maxRequests)), maxRequests)

	return func(c *gin.Context) {
		if !limiter.Allow() {
			c.AbortWithStatusJSON(http.StatusTooManyRequests, gin.H{
				"error": "rate limit exceeded",
			})
			return
		}
		c.Next()
	}
}

func CORS() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Header("Access-Control-Allow-Headers", "Content-Type, Authorization")

		if c.Request.Method == http.MethodOptions {
			c.AbortWithStatus(http.StatusNoContent)
			return
		}
		c.Next()
	}
}
```

### Rules
- Use `c.Next()` to proceed to the next handler
- Use `c.Abort()` or `c.AbortWithStatusJSON()` to stop the chain
- Set values with `c.Set()`, retrieve with `c.Get()` or `c.MustGet()`

---

## 3. Handler Pattern

Handlers receive `*gin.Context` and delegate to services.

```go
func (h *UserHandler) List(c *gin.Context) {
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	perPage, _ := strconv.Atoi(c.DefaultQuery("per_page", "25"))

	users, total, err := h.svc.ListUsers(c.Request.Context(), page, perPage)
	if err != nil {
		handleError(c, err)
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"data":  toUserResponses(users),
		"total": total,
		"page":  page,
	})
}
```

### Rules
- Parse and validate input at the handler level
- Delegate business logic to the service layer
- Use `c.Request.Context()` to pass context downstream
- Return consistent JSON response structures

---

## 4. Request Binding Pattern

Use struct tags for request validation.

```go
type CreateUserRequest struct {
	Name     string `json:"name" binding:"required,min=2,max=100"`
	Email    string `json:"email" binding:"required,email"`
	Password string `json:"password" binding:"required,min=8"`
	Role     string `json:"role" binding:"omitempty,oneof=admin user moderator"`
}

type UpdateUserRequest struct {
	Name  *string `json:"name" binding:"omitempty,min=2,max=100"`
	Email *string `json:"email" binding:"omitempty,email"`
}

type ListUsersQuery struct {
	Page    int    `form:"page" binding:"omitempty,min=1"`
	PerPage int    `form:"per_page" binding:"omitempty,min=1,max=100"`
	Sort    string `form:"sort" binding:"omitempty,oneof=name email created_at"`
}
```

### Rules
- Use `binding` tag for validation rules
- Use `ShouldBindJSON` for body, `ShouldBindQuery` for query params
- Use pointer fields for optional update fields
- Provide converter methods to service-layer input types

---

## 5. Error Handling Middleware

Centralized error handling for consistent responses.

```go
func ErrorHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Next()

		if len(c.Errors) > 0 {
			err := c.Errors.Last().Err
			handleError(c, err)
		}
	}
}

func handleError(c *gin.Context, err error) {
	var appErr *apperror.AppError
	if errors.As(err, &appErr) {
		c.JSON(appErr.HTTPStatus(), gin.H{
			"error": appErr.Message,
			"code":  appErr.Code,
		})
		return
	}

	switch {
	case errors.Is(err, apperror.ErrNotFound):
		c.JSON(http.StatusNotFound, gin.H{"error": "resource not found"})
	case errors.Is(err, apperror.ErrValidation):
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
	case errors.Is(err, apperror.ErrUnauthorized):
		c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
	default:
		slog.Error("unhandled error", "err", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal server error"})
	}
}
```

---

## 6. Response Helpers

Consistent response formatting.

```go
// Success sends a success response with data.
func Success(c *gin.Context, status int, data any) {
	c.JSON(status, gin.H{"data": data})
}

// SuccessWithMeta sends a paginated response.
func SuccessWithMeta(c *gin.Context, data any, meta PaginationMeta) {
	c.JSON(http.StatusOK, gin.H{
		"data": data,
		"meta": meta,
	})
}

// Error sends an error response.
func Error(c *gin.Context, status int, message string) {
	c.JSON(status, gin.H{"error": message})
}

type PaginationMeta struct {
	Page    int `json:"page"`
	PerPage int `json:"per_page"`
	Total   int `json:"total"`
}
```
