#!/usr/bin/env bash
# Post-edit hook: Run RSpec tests related to edited files
#
# This hook runs after an agent edits Ruby files. It determines the
# corresponding spec files and runs them. If a spec file itself was
# edited, it runs that spec directly.
#
# Mapping logic:
#   app/models/profile.rb       -> spec/models/profile_spec.rb
#   app/services/users/sync.rb  -> spec/services/users/sync_spec.rb
#   app/controllers/profiles_controller.rb -> spec/requests/profiles_spec.rb
#   app/presenters/profile_presenter.rb    -> spec/presenters/profile_presenter_spec.rb
#   app/jobs/sync/import_job.rb -> spec/jobs/sync/import_job_spec.rb
#   spec/**/*_spec.rb           -> run directly
#
# Usage: Called automatically by the agent system after file edits.
#        Can also be run manually:
#        ./hooks/post-edit-test.sh path/to/file.rb [path/to/other.rb ...]

set -euo pipefail

# Collect spec files to run
spec_files=()

for file in "$@"; do
  # Skip non-Ruby files
  if [[ "$file" != *.rb ]]; then
    continue
  fi

  # If it is already a spec file, add it directly
  if [[ "$file" == *_spec.rb ]]; then
    if [[ -f "$file" ]]; then
      spec_files+=("$file")
    fi
    continue
  fi

  # Map source file to spec file
  spec_file=""

  if [[ "$file" == app/models/* ]]; then
    # app/models/profile.rb -> spec/models/profile_spec.rb
    relative="${file#app/models/}"
    spec_file="spec/models/${relative%.rb}_spec.rb"

  elif [[ "$file" == app/services/* ]]; then
    # app/services/users/sync_service.rb -> spec/services/users/sync_service_spec.rb
    relative="${file#app/services/}"
    spec_file="spec/services/${relative%.rb}_spec.rb"

  elif [[ "$file" == app/controllers/* ]]; then
    # app/controllers/api/v1/profiles_controller.rb -> spec/requests/api/v1/profiles_spec.rb
    relative="${file#app/controllers/}"
    relative="${relative%_controller.rb}"
    spec_file="spec/requests/${relative}_spec.rb"

  elif [[ "$file" == app/presenters/* ]]; then
    # app/presenters/profile_presenter.rb -> spec/presenters/profile_presenter_spec.rb
    relative="${file#app/presenters/}"
    spec_file="spec/presenters/${relative%.rb}_spec.rb"

  elif [[ "$file" == app/jobs/* ]]; then
    # app/jobs/sync/import_job.rb -> spec/jobs/sync/import_job_spec.rb
    relative="${file#app/jobs/}"
    spec_file="spec/jobs/${relative%.rb}_spec.rb"

  elif [[ "$file" == app/mailers/* ]]; then
    # app/mailers/user_mailer.rb -> spec/mailers/user_mailer_spec.rb
    relative="${file#app/mailers/}"
    spec_file="spec/mailers/${relative%.rb}_spec.rb"

  elif [[ "$file" == lib/* ]]; then
    # lib/utils/parser.rb -> spec/lib/utils/parser_spec.rb
    relative="${file#lib/}"
    spec_file="spec/lib/${relative%.rb}_spec.rb"
  fi

  # Add the spec file if it exists
  if [[ -n "$spec_file" && -f "$spec_file" ]]; then
    spec_files+=("$spec_file")
  fi
done

# Remove duplicates
if [[ ${#spec_files[@]} -gt 0 ]]; then
  mapfile -t spec_files < <(printf '%s\n' "${spec_files[@]}" | sort -u)
fi

# Exit early if no spec files found
if [[ ${#spec_files[@]} -eq 0 ]]; then
  echo "==> No matching spec files found for edited files. Skipping test run."
  exit 0
fi

echo "==> Running ${#spec_files[@]} spec file(s)..."
for f in "${spec_files[@]}"; do
  echo "    - $f"
done
echo ""

# Run the matched spec files
if bundle exec rspec "${spec_files[@]}" --format documentation; then
  echo ""
  echo "==> All specs passed."
else
  exit_code=$?
  echo ""
  echo "==> Some specs FAILED. Review the output above."
  exit $exit_code
fi
