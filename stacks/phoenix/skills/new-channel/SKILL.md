---
name: new-channel
description: Generate a Phoenix channel with join, handle_in, and tests
---

# /new-channel

## What This Does

Generates a Phoenix channel module with join/3, handle_in/3 callbacks,
and a corresponding ChannelCase test file.

## Usage

```
/new-channel Chat              # Creates ChatChannel
/new-channel Notifications     # Creates NotificationsChannel
/new-channel Game              # Creates GameChannel
```

## How It Works

1. **Read reference patterns** from `patterns/phoenix-patterns.md`.
2. **Determine channel name** and topic from argument.
3. **Generate channel** with:
   - `use MyAppWeb, :channel`
   - `join/3` callback with authorization
   - `handle_in/3` for incoming messages
   - `broadcast!/3` for outgoing messages
4. **Register channel** in the socket handler.
5. **Generate ChannelCase test** for join and message handling.
6. **Run quality checks**: `mix format`, `mix credo --strict`, `mix test`.

## Generated Files

```
lib/my_app_web/channels/<name>_channel.ex
test/my_app_web/channels/<name>_channel_test.exs
```
