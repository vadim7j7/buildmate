---
name: new-cli
description: Generate a Thor command-line interface (executable, commands, options) with specs
---

# /new-cli

## What This Does

Adds a command-line interface built on Thor: an executable in `exe/` (gem) or
`bin/` (app), a `CLI` class with one method per command, and specs that run
commands in-process. Commands stay thin and call services.

## Usage

```
/new-cli mytool                  # exe/mytool + lib/mytool/cli.rb
/new-cli mytool import export    # with the import and export commands
```

## How It Works

### 1. Check the setup

```bash
grep -n "thor" Gemfile *.gemspec 2>/dev/null
ls exe bin 2>/dev/null
```

Add Thor if missing: `spec.add_dependency "thor", "~> 1.3"` in a gemspec, or
`bundle add thor` in an app.

### 2. The CLI class

```ruby
# lib/mytool/cli.rb
# frozen_string_literal: true

require "thor"

module Mytool
  class CLI < Thor
    # Non-zero exit status when a command fails (Thor's default is 0)
    def self.exit_on_failure? = true

    class_option :verbose, type: :boolean, aliases: "-v", desc: "Print debug output"

    desc "import FILE", "Import records from a CSV file"
    method_option :dry_run, type: :boolean, default: false, desc: "Validate without writing"
    method_option :batch_size, type: :numeric, default: 500
    def import(file)
      raise Thor::Error, "File not found: #{file}" unless File.exist?(file)

      result = Importer.new(path: file, dry_run: options[:dry_run], batch_size: options[:batch_size]).call
      say "Imported #{result.count} records", :green
    end

    desc "version", "Print the version"
    map %w[-V --version] => :version
    def version
      say Mytool::VERSION
    end
  end
end
```

### 3. The executable

```ruby
#!/usr/bin/env ruby
# exe/mytool
# frozen_string_literal: true

require "mytool"

Mytool::CLI.start(ARGV)
```

```bash
chmod +x exe/mytool
```

In a gem, list it in the gemspec (`spec.executables = ["mytool"]`, `spec.bindir = "exe"`).

### 4. Specs

```ruby
# spec/mytool/cli_spec.rb
RSpec.describe Mytool::CLI do
  it "imports a file" do
    importer = instance_double(Mytool::Importer, call: double(count: 3))
    allow(Mytool::Importer).to receive(:new).and_return(importer)

    expect { described_class.start(["import", "spec/fixtures/users.csv"]) }
      .to output(/Imported 3 records/).to_stdout
  end

  it "fails on a missing file" do
    # exit_on_failure? => Thor prints the error and exits 1
    expect { described_class.start(["import", "nope.csv"]) }
      .to raise_error(SystemExit).and output(/File not found/).to_stderr
  end
end
```

### 5. Run it

```bash
bundle exec exe/mytool help
bundle exec exe/mytool import data.csv --dry-run
```

## Rules

- `exit_on_failure?` returns true; report user errors with `raise Thor::Error` (message, exit 1), not a backtrace
- Every command and option has a `desc`; `help` must explain the tool without reading code
- Commands parse input and print; logic lives in services that are specced on their own
- Output for humans goes through `say`; machine-readable output (`--json`) goes to stdout only, logs to stderr
- Subcommand groups (`mytool users list`) use `subcommand "users", Mytool::Users`
