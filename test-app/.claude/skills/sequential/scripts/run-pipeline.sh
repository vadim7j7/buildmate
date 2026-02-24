#!/usr/bin/env bash
# run-pipeline.sh -- Manage the sequential agent pipeline.
#
# Usage:
#   ./run-pipeline.sh init [stage1 stage2 ...]    Initialise a new pipeline
#   ./run-pipeline.sh status                      Show current pipeline status
#   ./run-pipeline.sh stage-start <stage>         Mark a stage as in_progress
#   ./run-pipeline.sh stage-complete <stage>      Mark a stage as completed
#   ./run-pipeline.sh stage-fail <stage> [reason] Mark a stage as failed
#
# Exit codes:
#   0  Success
#   1  Invalid arguments or operation failed

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PIPELINE_DIR=".agent-pipeline"
PIPELINE_STATE="${PIPELINE_DIR}/pipeline.json"
VALID_STAGES=("implement" "test" "review" "eval" "security" "docs")
DEFAULT_STAGES=("implement" "test" "review" "eval" "security" "docs")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

timestamp() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

epoch_ms() {
  # macOS and Linux compatible millisecond timestamp
  if command -v gdate &>/dev/null; then
    gdate +%s%3N
  elif date +%s%N &>/dev/null 2>&1; then
    echo $(( $(date +%s%N) / 1000000 ))
  else
    echo $(( $(date +%s) * 1000 ))
  fi
}

is_valid_stage() {
  local stage="$1"
  for valid in "${VALID_STAGES[@]}"; do
    if [[ "${stage}" == "${valid}" ]]; then
      return 0
    fi
  done
  return 1
}

ensure_pipeline_exists() {
  if [[ ! -f "${PIPELINE_STATE}" ]]; then
    echo "Error: Pipeline not initialised. Run '$0 init' first." >&2
    exit 1
  fi
}

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

cmd_init() {
  local stages=("${@}")

  # Use default stages if none provided
  if [[ ${#stages[@]} -eq 0 ]]; then
    stages=("${DEFAULT_STAGES[@]}")
  fi

  # Validate all stages
  for stage in "${stages[@]}"; do
    if ! is_valid_stage "${stage}"; then
      echo "Error: Invalid stage '${stage}'. Valid stages: ${VALID_STAGES[*]}" >&2
      exit 1
    fi
  done

  # Create pipeline directory
  mkdir -p "${PIPELINE_DIR}"

  # Build the stages JSON array
  local stages_json="["
  local first=true
  for stage in "${stages[@]}"; do
    if [[ "${first}" == "true" ]]; then
      first=false
    else
      stages_json="${stages_json},"
    fi
    stages_json="${stages_json}{\"name\":\"${stage}\",\"status\":\"pending\",\"started_at\":null,\"completed_at\":null,\"duration_ms\":null}"
  done
  stages_json="${stages_json}]"

  # Write pipeline state
  cat > "${PIPELINE_STATE}" <<EOF
{
  "started_at": "$(timestamp)",
  "completed_at": null,
  "status": "running",
  "stages": ${stages_json}
}
EOF

  echo "Pipeline initialised with stages: ${stages[*]}"
  echo "State written to: ${PIPELINE_STATE}"
}

cmd_status() {
  ensure_pipeline_exists

  echo "## Pipeline Status"
  echo ""

  # Parse status using basic tools (no jq dependency)
  local pipeline_status
  pipeline_status="$(grep '"status"' "${PIPELINE_STATE}" | head -1 | sed 's/.*: *"//' | sed 's/".*//')"
  echo "**Pipeline Status:** ${pipeline_status}"
  echo ""
  echo "| Stage | Status | Duration |"
  echo "|-------|--------|----------|"

  # Extract stage info line by line
  local in_stage=false
  local stage_name=""
  local stage_status=""
  local stage_duration=""

  while IFS= read -r line; do
    if echo "${line}" | grep -q '"name"'; then
      stage_name="$(echo "${line}" | sed 's/.*: *"//' | sed 's/".*//')"
    fi
    if echo "${line}" | grep -q '"status"' && [[ -n "${stage_name}" ]]; then
      stage_status="$(echo "${line}" | sed 's/.*: *"//' | sed 's/".*//')"
    fi
    if echo "${line}" | grep -q '"duration_ms"'; then
      stage_duration="$(echo "${line}" | sed 's/.*: *//' | sed 's/[,}].*//' | tr -d ' ')"
      if [[ "${stage_duration}" == "null" ]]; then
        stage_duration="-"
      else
        stage_duration="${stage_duration}ms"
      fi
      echo "| ${stage_name} | ${stage_status} | ${stage_duration} |"
      stage_name=""
      stage_status=""
      stage_duration=""
    fi
  done < "${PIPELINE_STATE}"
}

cmd_stage_start() {
  local stage="$1"
  ensure_pipeline_exists

  if ! is_valid_stage "${stage}"; then
    echo "Error: Invalid stage '${stage}'." >&2
    exit 1
  fi

  # Record start timestamp for duration tracking
  echo "$(epoch_ms)" > "${PIPELINE_DIR}/.${stage}-start-time"

  # Update the stage status in the JSON (basic sed replacement)
  # This is a simplified approach -- for production use, consider using jq
  local temp_file="${PIPELINE_STATE}.tmp"
  local found=false
  local in_target_stage=false

  while IFS= read -r line; do
    if echo "${line}" | grep -q "\"name\":\"${stage}\""; then
      in_target_stage=true
      found=true
    fi
    if [[ "${in_target_stage}" == "true" ]] && echo "${line}" | grep -q '"status"'; then
      line="$(echo "${line}" | sed "s/\"pending\"/\"in_progress\"/" | sed "s/\"failed\"/\"in_progress\"/")"
      in_target_stage=false
    fi
    echo "${line}"
  done < "${PIPELINE_STATE}" > "${temp_file}"

  mv "${temp_file}" "${PIPELINE_STATE}"

  if [[ "${found}" == "true" ]]; then
    echo "Stage '${stage}' marked as in_progress."
  else
    echo "Warning: Stage '${stage}' not found in pipeline." >&2
  fi
}

cmd_stage_complete() {
  local stage="$1"
  ensure_pipeline_exists

  if ! is_valid_stage "${stage}"; then
    echo "Error: Invalid stage '${stage}'." >&2
    exit 1
  fi

  # Calculate duration
  local duration="null"
  local start_file="${PIPELINE_DIR}/.${stage}-start-time"
  if [[ -f "${start_file}" ]]; then
    local start_ms
    start_ms="$(cat "${start_file}")"
    local end_ms
    end_ms="$(epoch_ms)"
    duration=$(( end_ms - start_ms ))
    rm -f "${start_file}"
  fi

  # Update the stage status
  local temp_file="${PIPELINE_STATE}.tmp"
  local in_target_stage=false

  while IFS= read -r line; do
    if echo "${line}" | grep -q "\"name\":\"${stage}\""; then
      in_target_stage=true
    fi
    if [[ "${in_target_stage}" == "true" ]] && echo "${line}" | grep -q '"status"'; then
      line="$(echo "${line}" | sed "s/\"in_progress\"/\"completed\"/")"
    fi
    if [[ "${in_target_stage}" == "true" ]] && echo "${line}" | grep -q '"duration_ms"'; then
      line="$(echo "${line}" | sed "s/\"duration_ms\":null/\"duration_ms\":${duration}/")"
      in_target_stage=false
    fi
    echo "${line}"
  done < "${PIPELINE_STATE}" > "${temp_file}"

  mv "${temp_file}" "${PIPELINE_STATE}"

  echo "Stage '${stage}' completed (${duration}ms)."
}

cmd_stage_fail() {
  local stage="$1"
  local reason="${2:-"No reason provided"}"
  ensure_pipeline_exists

  if ! is_valid_stage "${stage}"; then
    echo "Error: Invalid stage '${stage}'." >&2
    exit 1
  fi

  # Update the stage status to failed
  local temp_file="${PIPELINE_STATE}.tmp"
  local in_target_stage=false

  while IFS= read -r line; do
    if echo "${line}" | grep -q "\"name\":\"${stage}\""; then
      in_target_stage=true
    fi
    if [[ "${in_target_stage}" == "true" ]] && echo "${line}" | grep -q '"status"'; then
      line="$(echo "${line}" | sed "s/\"in_progress\"/\"failed\"/")"
      in_target_stage=false
    fi
    echo "${line}"
  done < "${PIPELINE_STATE}" > "${temp_file}"

  mv "${temp_file}" "${PIPELINE_STATE}"

  # Write failure details
  cat > "${PIPELINE_DIR}/${stage}-failure.md" <<EOF
# Stage Failure: ${stage}

**Failed At:** $(timestamp)
**Reason:** ${reason}
EOF

  # Mark pipeline as failed
  sed -i.bak 's/"status":"running"/"status":"failed"/' "${PIPELINE_STATE}" 2>/dev/null || \
    sed -i '' 's/"status":"running"/"status":"failed"/' "${PIPELINE_STATE}"
  rm -f "${PIPELINE_STATE}.bak"

  echo "Stage '${stage}' failed: ${reason}"
  echo "Pipeline halted. Resume with: /sequential --from ${stage}"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <command> [args...]" >&2
  echo "Commands: init, status, stage-start, stage-complete, stage-fail" >&2
  exit 1
fi

COMMAND="$1"
shift

case "${COMMAND}" in
  init)
    cmd_init "$@"
    ;;
  status)
    cmd_status
    ;;
  stage-start)
    if [[ $# -lt 1 ]]; then
      echo "Usage: $0 stage-start <stage>" >&2
      exit 1
    fi
    cmd_stage_start "$1"
    ;;
  stage-complete)
    if [[ $# -lt 1 ]]; then
      echo "Usage: $0 stage-complete <stage>" >&2
      exit 1
    fi
    cmd_stage_complete "$1"
    ;;
  stage-fail)
    if [[ $# -lt 1 ]]; then
      echo "Usage: $0 stage-fail <stage> [reason]" >&2
      exit 1
    fi
    cmd_stage_fail "$@"
    ;;
  *)
    echo "Error: Unknown command '${COMMAND}'." >&2
    echo "Valid commands: init, status, stage-start, stage-complete, stage-fail" >&2
    exit 1
    ;;
esac
