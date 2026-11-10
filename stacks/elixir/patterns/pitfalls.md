# Elixir / OTP Pitfalls

Mistakes that compile and pass a quick test, then fail under load or in production.
Check new code against this list; reviewers flag these.

---

## 1. Atoms From User Input

Atoms are never garbage-collected and the atom table has a fixed limit (about 1M by
default). Creating atoms from input lets anyone crash the node.

```elixir
# BAD
String.to_atom(params["sort"])
Jason.decode!(body, keys: :atoms)

# GOOD: allowlist
case params["sort"] do
  "name" -> :name
  "inserted_at" -> :inserted_at
  _ -> :inserted_at
end

# or only atoms that already exist
String.to_existing_atom(value)   # raises ArgumentError for unknown values: rescue or allowlist
```

Same for `:erlang.binary_to_term/1` on untrusted data: use `binary_to_term(bin, [:safe])`,
or better, don't deserialize terms from clients at all.

---

## 2. Process State and Bottlenecks

- A GenServer handles one message at a time. Funnelling every request through one named
  GenServer serializes the whole app; read-heavy shared data belongs in ETS
  (`read_concurrency: true`) or `:persistent_term` (rarely written)
- Do not use a GenServer just to organise code: plain modules and functions are the default
- State lives only as long as the process: a crash and restart loses it. Persist what
  must survive, or rebuild it in `init/1`
- Slow work in `init/1` blocks the supervisor and app start: return
  `{:ok, state, {:continue, :load}}` and do it in `handle_continue/2`
- `GenServer.call/3` times out after 5 s by default and crashes the caller; long work
  goes in a Task or a job queue, not a blocking call

---

## 3. Supervision

- Every long-running process is started under a supervisor; never a bare `spawn/1` or
  `Task.start/1` for work that matters. Use `Task.Supervisor.start_child/2` (fire and
  forget) or `Task.Supervisor.async_nolink/2` (await and handle failure)
- Pick the strategy deliberately: `:one_for_one` (independent children), `:rest_for_one`
  (later children depend on earlier), `:one_for_all` (all-or-nothing)
- A child that crashes in a loop hits `max_restarts` and takes its supervisor (and maybe
  the app) down: fix the crash, do not raise the limits
- Dynamic per-entity processes: `DynamicSupervisor` + `Registry` with `{:via, Registry, ...}`
  names; never create atom names per entity
- Children start in list order and stop in reverse: put the Repo and PubSub before
  anything that uses them

---

## 4. Large Messages and Binaries

- Messages are copied between processes (except large binaries, which are reference
  counted). Sending a big map or list to a GenServer on every call copies it every time:
  send IDs, let the receiver fetch
- A process that touches many large binaries can hold them alive long after use
  (refc binary leak); long-lived processes that pass binaries through should keep only
  what they need (`:binary.copy/1` for a small slice of a big binary) or hibernate
- Unbounded mailboxes: a GenServer receiving faster than it processes grows until the node
  runs out of memory. Watch `Process.info(pid, :message_queue_len)`; add back-pressure
  (call instead of cast, GenStage/Broadway, or a job queue)
- Never `send` to a process you do not monitor and expect a reply; use `call` or monitor

---

## 5. Data and Ecto

- Strings vs charlists: `"abc"` is a binary, `~c"abc"` a charlist; Erlang APIs often
  want charlists
- Maps from JSON have string keys; changeset `cast/4` handles them, don't convert to atoms
- N+1 queries: `Repo.preload/2` or `preload:` in the query, not `Repo.get` inside `Enum.map`
- `Repo.all` on an unbounded query loads everything: paginate or `Repo.stream/2` in a
  transaction
- Money and exact quantities: `Decimal`, never floats
- Time: `DateTime` in UTC (`:utc_datetime_usec` columns); `NaiveDateTime` has no zone

---

## 6. Errors and Control Flow

- Let it crash for unexpected errors, but return `{:ok, _} | {:error, _}` for expected ones
  (not found, invalid input), and handle them with `with`
- `with` without an `else` passes the non-matching value through: make sure callers
  handle every shape it can return
- Never `rescue` broadly (`rescue _ ->`): it hides bugs and swallows exits
- `try/catch :exit` around a `GenServer.call` only where a timeout is an expected outcome
