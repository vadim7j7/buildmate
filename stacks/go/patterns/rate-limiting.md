# Rate Limiting

Limit requests per client (IP, user ID or API key). Framework wiring is in the
framework's auth pattern (`gin-auth.md`, `fiber-auth.md`, `chi-auth.md`); Fiber and Chi
have ready-made middleware, Gin uses the store below.

---

## 1. Choosing the Store

- **In memory** (below): one instance, or limits that may be per-instance. Simple, no
  dependency; each replica counts separately
- **Redis** (shared): several replicas that must share one limit, e.g. login attempts.
  Use an existing library for your Redis client (e.g. `github.com/go-redis/redis_rate`)
  rather than hand-written Lua

---

## 2. In-Memory Per-Key Limiter (`golang.org/x/time/rate`)

A token bucket per key, with idle keys evicted so the map does not grow forever.

```go
package ratelimit

import (
	"context"
	"sync"
	"time"

	"golang.org/x/time/rate"
)

type entry struct {
	lim  *rate.Limiter
	seen time.Time
}

// Store hands out one token bucket per key.
type Store struct {
	mu    sync.Mutex
	keys  map[string]*entry
	rps   rate.Limit
	burst int
}

// NewStore allows rps requests per second per key, with bursts up to burst.
// Eviction stops when ctx is cancelled (pass the server's lifetime context).
func NewStore(ctx context.Context, rps rate.Limit, burst int) *Store {
	s := &Store{keys: make(map[string]*entry), rps: rps, burst: burst}
	go s.evict(ctx, 10*time.Minute)
	return s
}

// Allow reports whether the request for key may proceed.
func (s *Store) Allow(key string) bool {
	s.mu.Lock()
	e, ok := s.keys[key]
	if !ok {
		e = &entry{lim: rate.NewLimiter(s.rps, s.burst)}
		s.keys[key] = e
	}
	e.seen = time.Now()
	s.mu.Unlock()
	return e.lim.Allow() // Limiter is safe for concurrent use
}

func (s *Store) evict(ctx context.Context, idle time.Duration) {
	t := time.NewTicker(time.Minute)
	defer t.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case now := <-t.C:
			s.mu.Lock()
			for k, e := range s.keys {
				if now.Sub(e.seen) > idle {
					delete(s.keys, k)
				}
			}
			s.mu.Unlock()
		}
	}
}
```

Example limits: `NewStore(ctx, rate.Every(time.Second), 20)` for general API traffic
(1/s sustained, bursts of 20); `rate.Every(12*time.Second), 5` for login (5 per minute).

---

## 3. Choosing the Key

- Anonymous endpoints (login, sign-up, password reset): client IP, and for login also
  the submitted email, so one attacker cannot spread guesses over many IPs
- Authenticated endpoints: the user ID from verified claims (run after auth middleware)
- Client IP only from a trusted source: configure the framework's trusted proxies; never
  read `X-Forwarded-For` directly

---

## Rules

- Respond `429 Too Many Requests` with a fixed JSON body and a `Retry-After` header
- A global limiter (one bucket for everyone) is not a per-client limit: avoid it
- Tighter limits on auth endpoints than on reads
- The eviction goroutine must stop with the server (context), or tests leak it
