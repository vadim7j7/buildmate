#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# evals/runner.sh — Cross-stack evaluation runner for agent quality testing
#
# Runs eval cases through headless Claude (`claude -p`) and captures output.
# Each case in the JSONL input contains: id, prompt, expected_behavior, stack, rubric.
#
# Usage:
#   ./evals/runner.sh <cases.jsonl> [--stack <stack>] [--max <n>] [--timeout <seconds>]
#
# Examples:
#   ./evals/runner.sh evals/shared-cases/code-review-quality.jsonl
#   ./evals/runner.sh evals/shared-cases/code-review-quality.jsonl --stack rails --max 5
#   ./evals/runner.sh evals/shared-cases/test-generation-quality.jsonl --timeout 120
# =============================================================================

# --- Constants ---------------------------------------------------------------
DEFAULT_TIMEOUT=90      # seconds per case
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

# --- Color helpers -----------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# --- Usage -------------------------------------------------------------------
usage() {
    cat <<EOF
${BOLD}evals/runner.sh${NC} — Run eval cases through headless Claude

${BOLD}USAGE${NC}
    ./evals/runner.sh <cases.jsonl> [OPTIONS]

${BOLD}ARGUMENTS${NC}
    <cases.jsonl>       Path to a JSONL file containing eval cases.
                        Each line must be a JSON object with fields:
                          id, prompt, expected_behavior, stack, rubric

${BOLD}OPTIONS${NC}
    --stack <stack>     Filter cases to only run those matching this stack
                        (e.g., rails, react, typescript, python)
    --max <n>           Maximum number of cases to run
    --timeout <secs>    Timeout per case in seconds (default: ${DEFAULT_TIMEOUT})
    -h, --help          Show this help message

${BOLD}EXAMPLES${NC}
    ./evals/runner.sh evals/shared-cases/code-review-quality.jsonl
    ./evals/runner.sh evals/shared-cases/code-review-quality.jsonl --stack rails --max 5
    ./evals/runner.sh evals/shared-cases/test-generation-quality.jsonl --timeout 120

${BOLD}OUTPUT${NC}
    Results are written to /tmp/eval-results-<timestamp>/
    Each case produces:
      - <id>.prompt.txt       The prompt sent to Claude
      - <id>.output.txt       Claude's raw response
      - <id>.meta.json        Metadata (id, stack, expected_behavior, rubric, timing)
EOF
    exit "${1:-0}"
}

# --- Logging helpers ---------------------------------------------------------
log_info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_err()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# --- Argument parsing --------------------------------------------------------
CASES_FILE=""
STACK_FILTER=""
MAX_CASES=""
TIMEOUT="${DEFAULT_TIMEOUT}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage 0
            ;;
        --stack)
            [[ $# -lt 2 ]] && { log_err "--stack requires a value"; usage 1; }
            STACK_FILTER="$2"
            shift 2
            ;;
        --max)
            [[ $# -lt 2 ]] && { log_err "--max requires a value"; usage 1; }
            MAX_CASES="$2"
            shift 2
            ;;
        --timeout)
            [[ $# -lt 2 ]] && { log_err "--timeout requires a value"; usage 1; }
            TIMEOUT="$2"
            shift 2
            ;;
        -*)
            log_err "Unknown option: $1"
            usage 1
            ;;
        *)
            if [[ -z "$CASES_FILE" ]]; then
                CASES_FILE="$1"
            else
                log_err "Unexpected argument: $1"
                usage 1
            fi
            shift
            ;;
    esac
done

# --- Validation --------------------------------------------------------------
if [[ -z "$CASES_FILE" ]]; then
    log_err "Missing required argument: <cases.jsonl>"
    usage 1
fi

if [[ ! -f "$CASES_FILE" ]]; then
    log_err "Cases file not found: $CASES_FILE"
    exit 1
fi

# Check that jq is available (required for JSON parsing)
if ! command -v jq &>/dev/null; then
    log_err "jq is required but not installed. Install it with: brew install jq"
    exit 1
fi

# Check that claude CLI is available
if ! command -v claude &>/dev/null; then
    log_err "claude CLI is required but not found in PATH."
    log_err "Install it from: https://docs.anthropic.com/en/docs/claude-cli"
    exit 1
fi

# --- Prepare output directory ------------------------------------------------
RESULTS_DIR="/tmp/eval-results-${TIMESTAMP}"
mkdir -p "$RESULTS_DIR"
log_info "Results will be written to: ${BOLD}${RESULTS_DIR}${NC}"

# --- Load and filter cases ---------------------------------------------------
# Read all cases into an array, applying filters
CASES=()
line_num=0

while IFS= read -r line; do
    line_num=$((line_num + 1))

    # Skip empty lines
    [[ -z "${line// /}" ]] && continue

    # Validate JSON
    if ! echo "$line" | jq empty 2>/dev/null; then
        log_warn "Skipping invalid JSON on line $line_num"
        continue
    fi

    # Extract fields for filtering
    case_id="$(echo "$line" | jq -r '.id // empty')"
    case_stack="$(echo "$line" | jq -r '.stack // empty')"

    if [[ -z "$case_id" ]]; then
        log_warn "Skipping line $line_num: missing 'id' field"
        continue
    fi

    # Apply stack filter if specified
    if [[ -n "$STACK_FILTER" && "$case_stack" != "$STACK_FILTER" ]]; then
        continue
    fi

    CASES+=("$line")

    # Apply max limit if specified
    if [[ -n "$MAX_CASES" && ${#CASES[@]} -ge $MAX_CASES ]]; then
        break
    fi
done < "$CASES_FILE"

TOTAL=${#CASES[@]}

if [[ $TOTAL -eq 0 ]]; then
    log_warn "No cases matched the given filters."
    if [[ -n "$STACK_FILTER" ]]; then
        log_warn "Stack filter was: --stack $STACK_FILTER"
    fi
    exit 0
fi

log_info "Loaded ${BOLD}${TOTAL}${NC} case(s) from ${CASES_FILE}"
[[ -n "$STACK_FILTER" ]] && log_info "Stack filter: ${BOLD}${STACK_FILTER}${NC}"
[[ -n "$MAX_CASES" ]]    && log_info "Max cases: ${BOLD}${MAX_CASES}${NC}"
echo ""

# --- Run each case -----------------------------------------------------------
passed=0
failed=0
errored=0

for i in "${!CASES[@]}"; do
    case_json="${CASES[$i]}"
    idx=$((i + 1))

    # Extract case fields
    case_id="$(echo "$case_json" | jq -r '.id')"
    case_prompt="$(echo "$case_json" | jq -r '.prompt')"
    case_expected="$(echo "$case_json" | jq -r '.expected_behavior')"
    case_stack="$(echo "$case_json" | jq -r '.stack')"
    case_rubric="$(echo "$case_json" | jq -r '.rubric')"

    echo -e "${BOLD}[${idx}/${TOTAL}]${NC} Running case: ${CYAN}${case_id}${NC} (stack: ${case_stack})"

    # Write prompt to file
    prompt_file="${RESULTS_DIR}/${case_id}.prompt.txt"
    echo "$case_prompt" > "$prompt_file"

    # Record start time
    start_time="$(date +%s)"

    # Run through headless Claude with timeout
    output_file="${RESULTS_DIR}/${case_id}.output.txt"
    exit_code=0

    if timeout "${TIMEOUT}" claude -p "$case_prompt" > "$output_file" 2>&1; then
        end_time="$(date +%s)"
        duration=$((end_time - start_time))
        log_ok "Case ${case_id} completed in ${duration}s"
        status="completed"
        passed=$((passed + 1))
    else
        exit_code=$?
        end_time="$(date +%s)"
        duration=$((end_time - start_time))

        if [[ $exit_code -eq 124 ]]; then
            # Timeout
            log_warn "Case ${case_id} timed out after ${TIMEOUT}s"
            echo "[TIMEOUT] Case exceeded ${TIMEOUT}s limit" >> "$output_file"
            status="timeout"
            errored=$((errored + 1))
        else
            log_err "Case ${case_id} failed with exit code ${exit_code} (${duration}s)"
            status="error"
            errored=$((errored + 1))
        fi
    fi

    # Write metadata JSON
    meta_file="${RESULTS_DIR}/${case_id}.meta.json"
    jq -n \
        --arg id "$case_id" \
        --arg stack "$case_stack" \
        --arg expected "$case_expected" \
        --arg rubric "$case_rubric" \
        --arg status "$status" \
        --argjson duration "$duration" \
        --argjson exit_code "$exit_code" \
        --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        '{
            id: $id,
            stack: $stack,
            expected_behavior: $expected,
            rubric: $rubric,
            status: $status,
            duration_seconds: $duration,
            exit_code: $exit_code,
            timestamp: $timestamp
        }' > "$meta_file"

    echo ""
done

# --- Summary -----------------------------------------------------------------
echo -e "${BOLD}========================================${NC}"
echo -e "${BOLD}Eval Run Complete${NC}"
echo -e "${BOLD}========================================${NC}"
echo -e "  Total cases:  ${TOTAL}"
echo -e "  Completed:    ${GREEN}${passed}${NC}"
echo -e "  Errors:       ${RED}${errored}${NC}"
echo -e "  Results dir:  ${BOLD}${RESULTS_DIR}${NC}"
echo ""
echo -e "Next step: score the results with:"
echo -e "  ${CYAN}./evals/scorer.sh ${RESULTS_DIR}${NC}"

# Write a manifest file for downstream tools
jq -n \
    --arg cases_file "$CASES_FILE" \
    --arg stack_filter "${STACK_FILTER:-all}" \
    --argjson total "$TOTAL" \
    --argjson passed "$passed" \
    --argjson errored "$errored" \
    --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{
        cases_file: $cases_file,
        stack_filter: $stack_filter,
        total_cases: $total,
        completed: $passed,
        errors: $errored,
        timestamp: $timestamp
    }' > "${RESULTS_DIR}/manifest.json"
