# Go Pitfalls

Mistakes that compile, pass a quick test, and fail in production. Check new code
against this list; reviewers flag these.

---

## 1. Goroutine Leaks

A goroutine blocked forever on a channel is never collected.

```go
// BAD: if ctx is cancelled first, nobody reads ch and the goroutine blocks forever
ch := make(chan result)
go func() { ch <- slowCall() }()
select {
case r := <-ch:
	return r, nil
case <-ctx.Done():
	return result{}, ctx.Err()
}

// GOOD: buffered, so the send always completes
ch := make(chan result, 1)
```

- Every `go` statement has a clear end: context cancellation, a closed channel, or a
  `sync.WaitGroup` / `errgroup.Group` someone waits on
- Prefer `errgroup.WithContext` for fan-out: first error cancels the rest
- Tickers: `defer t.Stop()`; background loops `select` on `ctx.Done()`
- Detect in tests with `go.uber.org/goleak` (`defer goleak.VerifyNone(t)`) if the project uses it

---

## 2. Nil Maps, Nil Slices, Nil Interfaces

```go
var m map[string]int
m["a"] = 1 // panic: assignment to entry in nil map; use make(map[string]int)

var users []User          // encodes as JSON null
users := []User{}         // encodes as []; use this for API responses

func find() error {
	var err *MyErr = nil
	return err            // non-nil error interface holding a nil pointer!
}
// return nil explicitly when there is no error
```

- Reading a nil map is fine; writing panics. Struct fields that are maps need a constructor
- `errors.As` targets must be a pointer to the error type: `var e *MyErr; errors.As(err, &e)`

---

## 3. Loop Variables (fixed in Go 1.22)

Since Go 1.22 each iteration has its own loop variable, so closures and goroutines
capturing `v` are safe. This depends on the `go` line in `go.mod` (>= 1.22), not on the
installed toolchain. Do not add `v := v` copies in new code; remove them when touching old
code. Still true: taking `&v` of a range value points at a copy, not the slice element;
use `&items[i]` to modify in place.

---

## 4. Context Propagation

- Pass the request's `ctx` down every call that does I/O; never `context.Background()`
  or `context.TODO()` inside a request path
- `ctx` is the first parameter; never store it in a struct
- Always `defer cancel()` after `context.WithTimeout` / `WithCancel`
- Work that must outlive the request (send email after responding): `context.WithoutCancel(ctx)`
  (keeps values such as the request ID) plus its own timeout, and run it in a tracked goroutine
  or a job queue, never a bare `go`
- Check `ctx.Err()` in long loops; database drivers and `http.Client` respect the context

---

## 5. Slices and Strings

```go
a := make([]int, 3, 10)
b := append(a, 4) // shares a's backing array
c := append(a, 5) // overwrites b[3]: b and c both see 5
```

- Copy before keeping a sub-slice of a large buffer (`slices.Clone`, `bytes.Clone`)
- `for i, r := range s` over a string yields runes, `s[i]` bytes; `len(s)` counts bytes

---

## 6. Concurrency

- Maps are not safe for concurrent writes: `sync.Mutex` around them or `sync.Map` for
  append-mostly caches. Run `go test -race ./...`
- Do not copy a struct that contains a `sync.Mutex` (pass pointers; `go vet` catches it)
- A `sync.WaitGroup.Add` happens before `go`, not inside the goroutine (or use `wg.Go`, Go 1.25+)

---

## 7. Resources and Errors

- `defer resp.Body.Close()` after checking the error of `http.Do`; `defer rows.Close()`
  and check `rows.Err()`
- `defer` inside a loop runs at function end, not per iteration: move the body into a
  function
- The default `http.Client` has no timeout: create one with `Timeout` set
- `json.Unmarshal` into `any` turns numbers into `float64`; decode into typed structs
- Shadowed `err` (`:=` in an inner scope) silently drops errors; `go vet` / golangci-lint
  catch most
- `time.Time` comparison: use `t.Equal(u)`, not `==` (location and monotonic clock differ)
