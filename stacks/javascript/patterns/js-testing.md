# Testing TypeScript with Vitest

Read this when writing or fixing tests for TypeScript code (libraries, CLIs, Node
services). Framework stacks add their own testing pattern on top (HTTP, components).
A project already on Jest keeps Jest: the API is nearly the same (`vi` → `jest`).

## Setup

```bash
npm i -D vitest @vitest/coverage-v8
npm pkg set scripts.test="vitest run" scripts.test:watch="vitest"
```

Config: see "Tests (Vitest defaults)" in `styles/typescript.md` (node environment,
`restoreMocks: true`, v8 coverage). Tests sit next to the code: `parse.ts` →
`parse.test.ts`.

## Shape of a Test

```typescript
import { describe, it, expect } from 'vitest';
import { parseDuration } from './parse-duration';

describe('parseDuration', () => {
  it.each([
    ['90s', 90_000],
    ['2m', 120_000],
    ['1h30m', 5_400_000],
  ])('parses %s', (input, expected) => {
    expect(parseDuration(input)).toBe(expected);
  });

  it('rejects an unknown unit', () => {
    expect(() => parseDuration('5y')).toThrow(/unit/);
  });

  it('rejects empty input', () => {
    expect(() => parseDuration('')).toThrow();
  });
});
```

- One behaviour per test; the name says what happens (`'rejects an unknown unit'`).
- Arrange / act / assert; no logic (loops, ifs) in tests: use `it.each`.
- Test through the exported API, not private helpers.
- Cover: happy path, each error the code throws, boundaries (empty, max, unicode,
  negative, very large), and for bugs a test that failed before the fix.

## Async

```typescript
it('retries once on a timeout', async () => {
  const fetchJson = vi.fn()
    .mockRejectedValueOnce(new TimeoutError())
    .mockResolvedValueOnce({ ok: true });

  await expect(withRetry(fetchJson)).resolves.toEqual({ ok: true });
  expect(fetchJson).toHaveBeenCalledTimes(2);
});

it('gives up after the last attempt', async () => {
  const fetchJson = vi.fn().mockRejectedValue(new TimeoutError());
  await expect(withRetry(fetchJson, { attempts: 3 })).rejects.toThrow(TimeoutError);
});
```

Always `await` the `expect(...).resolves/rejects`; a missing `await` makes the test pass
without checking anything.

## Mocks: Only at the Edges

| Edge | Tool |
|---|---|
| A function passed in (dependency injection) | `vi.fn()` (preferred: no module mocking) |
| One function of a module | `vi.spyOn(module, 'fn').mockResolvedValue(...)` |
| A whole module (SDK, mailer) | `vi.mock('./mailer', () => ({ send: vi.fn() }))` (hoisted to the top) |
| Network | `vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(body)))` |
| Time | `vi.useFakeTimers(); vi.setSystemTime(new Date('2026-01-01'))`, `vi.advanceTimersByTimeAsync(ms)` |
| Env vars | `vi.stubEnv('API_URL', 'http://test')` (restored with `vi.unstubAllEnvs()`) |

Don't mock the code under test or plain data helpers; prefer real objects. With
`restoreMocks: true` spies are restored after each test; fake timers need
`vi.useRealTimers()` in `afterEach`.

## Files and Processes

- Filesystem: write to a temp dir (`await mkdtemp(join(tmpdir(), 'x-'))`), remove it in
  `afterEach`; never touch the repo or home directory.
- CLIs: export a `run(argv, io)` function and test it directly; keep one smoke test that
  spawns the real binary (`execFile`) if packaging matters.

## Types

Type-level behaviour (overloads, generics of a public API) can be checked with
`expectTypeOf`:

```typescript
import { expectTypeOf } from 'vitest';
expectTypeOf(parseConfig).returns.toEqualTypeOf<Config>();
```

## Running

```bash
npm test                          # all, once (CI)
npx vitest run src/parse          # a folder or file
npx vitest run -t "rejects"       # by test name
npx vitest run --coverage         # coverage report
```

No sleeps, no real network, no order dependence: tests run in parallel across files.
