#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# evals/scorer.sh — LLM-as-judge scoring for eval results
#
# Takes runner output and uses Claude to score each case against its rubric.
# Scoring formula:
#   30% Correctness + 15% Code Quality + 25% Security + 20% Performance + 10% Test Coverage
#
# Thresholds:
#   >= 0.9   Excellent
#   0.7-0.89 Acceptable
#   < 0.7    Needs fixes
#
# Usage:
#   ./evals/scorer.sh <results-dir>
#
# Examples:
#   ./evals/scorer.sh /tmp/eval-results-20240101-120000
# =============================================================================

# --- Constants ---------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Scoring weights
W_CORRECTNESS=0.30
W_CODE_QUALITY=0.15
W_SECURITY=0.25
W_PERFORMANCE=0.20
W_TEST_COVERAGE=0.10

# Verdict thresholds
THRESHOLD_EXCELLENT=0.9
THRESHOLD_ACCEPTABLE=0.7

# --- Color helpers -----------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# --- Usage -------------------------------------------------------------------
usage() {
    cat <<EOF
${BOLD}evals/scorer.sh${NC} — LLM-as-judge scoring for eval results

${BOLD}USAGE${NC}
    ./evals/scorer.sh <results-dir>

${BOLD}ARGUMENTS${NC}
    <results-dir>       Path to the eval results directory produced by runner.sh
                        (e.g., /tmp/eval-results-20240101-120000)

${BOLD}SCORING FORMULA${NC}
    Weighted score = 30% Correctness
                   + 15% Code Quality
                   + 25% Security
                   + 20% Performance
                   + 10% Test Coverage

${BOLD}VERDICTS${NC}
    >= 0.90   Excellent
    0.70-0.89 Acceptable
    < 0.70    Needs fixes

${BOLD}OUTPUT${NC}
    For each case, writes a score file: <id>.score.json
    containing dimension scores, weighted total, verdict, and notes.

${BOLD}EXAMPLES${NC}
    ./evals/scorer.sh /tmp/eval-results-20240101-120000
EOF
    exit "${1:-0}"
}

# --- Logging helpers ---------------------------------------------------------
log_info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_err()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# --- Argument parsing --------------------------------------------------------
if [[ $# -lt 1 ]] || [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    usage 0
fi

RESULTS_DIR="$1"

# --- Validation --------------------------------------------------------------
if [[ ! -d "$RESULTS_DIR" ]]; then
    log_err "Results directory not found: $RESULTS_DIR"
    exit 1
fi

if [[ ! -f "$RESULTS_DIR/manifest.json" ]]; then
    log_warn "No manifest.json found in $RESULTS_DIR — are you sure this is a runner output directory?"
fi

if ! command -v jq &>/dev/null; then
    log_err "jq is required but not installed. Install it with: brew install jq"
    exit 1
fi

if ! command -v claude &>/dev/null; then
    log_err "claude CLI is required but not found in PATH."
    exit 1
fi

# --- Discover cases to score -------------------------------------------------
# Find all .meta.json files — each represents one eval case
META_FILES=()
while IFS= read -r f; do
    META_FILES+=("$f")
done < <(find "$RESULTS_DIR" -name '*.meta.json' -not -name 'manifest.json' | sort)

TOTAL=${#META_FILES[@]}

if [[ $TOTAL -eq 0 ]]; then
    log_err "No .meta.json files found in $RESULTS_DIR"
    exit 1
fi

log_info "Found ${BOLD}${TOTAL}${NC} case(s) to score in ${RESULTS_DIR}"
echo ""

# --- Build the judge prompt template -----------------------------------------
# This prompt instructs Claude to act as an evaluator and return structured JSON.
build_judge_prompt() {
    local case_id="$1"
    local original_prompt="$2"
    local agent_output="$3"
    local expected_behavior="$4"
    local rubric="$5"

    cat <<JUDGE_PROMPT
You are an expert code review evaluator. Your job is to score an AI agent's response
against a rubric. Be rigorous and fair.

## Original Prompt Given to the Agent
${original_prompt}

## Agent's Response
${agent_output}

## Expected Behavior
${expected_behavior}

## Rubric
${rubric}

## Scoring Instructions
Score each dimension from 0.0 to 1.0:

1. **Correctness** (weight: 30%): Did the agent identify the right issues? Are suggestions accurate?
2. **Code Quality** (weight: 15%): Are code suggestions clean, idiomatic, and well-structured?
3. **Security** (weight: 25%): Did the agent catch security vulnerabilities? Are fixes appropriate?
4. **Performance** (weight: 20%): Did the agent identify performance issues? Are optimizations sound?
5. **Test Coverage** (weight: 10%): Did the agent suggest or consider testing? Are edge cases noted?

## Response Format
You MUST respond with ONLY a valid JSON object (no markdown fences, no extra text):
{
  "case_id": "${case_id}",
  "scores": {
    "correctness": <0.0-1.0>,
    "code_quality": <0.0-1.0>,
    "security": <0.0-1.0>,
    "performance": <0.0-1.0>,
    "test_coverage": <0.0-1.0>
  },
  "weighted_score": <0.0-1.0>,
  "notes": "<Brief explanation of the score — what was good, what was missed>"
}

Calculate weighted_score as:
  (correctness * 0.30) + (code_quality * 0.15) + (security * 0.25) + (performance * 0.20) + (test_coverage * 0.10)

Be precise with scores. Only give 1.0 for truly perfect performance in that dimension.
JUDGE_PROMPT
}

# --- Helper: determine verdict from score ------------------------------------
get_verdict() {
    local score="$1"
    # Use awk for floating-point comparison
    awk -v s="$score" -v exc="$THRESHOLD_EXCELLENT" -v acc="$THRESHOLD_ACCEPTABLE" '
    BEGIN {
        if (s >= exc) print "Excellent"
        else if (s >= acc) print "Acceptable"
        else print "Needs fixes"
    }'
}

# --- Score each case ---------------------------------------------------------
scored=0
score_errors=0

for meta_file in "${META_FILES[@]}"; do
    case_id="$(jq -r '.id' "$meta_file")"
    idx=$((scored + score_errors + 1))

    echo -e "${BOLD}[${idx}/${TOTAL}]${NC} Scoring case: ${CYAN}${case_id}${NC}"

    # Check case status — skip errored/timed-out cases
    case_status="$(jq -r '.status' "$meta_file")"
    if [[ "$case_status" != "completed" ]]; then
        log_warn "Skipping ${case_id}: status is '${case_status}'"

        # Write a zero-score for non-completed cases
        jq -n \
            --arg id "$case_id" \
            --arg status "$case_status" \
            '{
                case_id: $id,
                scores: { correctness: 0, code_quality: 0, security: 0, performance: 0, test_coverage: 0 },
                weighted_score: 0,
                verdict: "Needs fixes",
                notes: ("Case did not complete: " + $status),
                judge_status: "skipped"
            }' > "${RESULTS_DIR}/${case_id}.score.json"

        score_errors=$((score_errors + 1))
        echo ""
        continue
    fi

    # Load the case files
    prompt_file="${RESULTS_DIR}/${case_id}.prompt.txt"
    output_file="${RESULTS_DIR}/${case_id}.output.txt"

    if [[ ! -f "$prompt_file" ]] || [[ ! -f "$output_file" ]]; then
        log_err "Missing prompt or output file for ${case_id}"
        score_errors=$((score_errors + 1))
        echo ""
        continue
    fi

    original_prompt="$(cat "$prompt_file")"
    agent_output="$(cat "$output_file")"
    expected_behavior="$(jq -r '.expected_behavior' "$meta_file")"
    rubric="$(jq -r '.rubric' "$meta_file")"

    # Build the judge prompt
    judge_prompt="$(build_judge_prompt "$case_id" "$original_prompt" "$agent_output" "$expected_behavior" "$rubric")"

    # Send to Claude for scoring
    score_raw=""
    if score_raw="$(echo "$judge_prompt" | claude -p 2>&1)"; then
        # Try to parse the JSON response — Claude may wrap it in markdown fences
        score_json=""

        # First try: direct parse
        if echo "$score_raw" | jq empty 2>/dev/null; then
            score_json="$score_raw"
        else
            # Second try: extract JSON from markdown code fences
            extracted="$(echo "$score_raw" | sed -n '/^[{]/,/^[}]/p' | head -50)"
            if echo "$extracted" | jq empty 2>/dev/null; then
                score_json="$extracted"
            else
                # Third try: grep for the JSON block
                extracted="$(echo "$score_raw" | grep -Pzo '\{[\s\S]*\}' 2>/dev/null | tr '\0' '\n' || true)"
                if [[ -n "$extracted" ]] && echo "$extracted" | jq empty 2>/dev/null; then
                    score_json="$extracted"
                fi
            fi
        fi

        if [[ -n "$score_json" ]]; then
            # Calculate verdict from weighted score
            weighted_score="$(echo "$score_json" | jq -r '.weighted_score // 0')"
            verdict="$(get_verdict "$weighted_score")"

            # Enrich the score JSON with verdict and save
            echo "$score_json" | jq \
                --arg verdict "$verdict" \
                --arg judge_status "completed" \
                '. + { verdict: $verdict, judge_status: $judge_status }' \
                > "${RESULTS_DIR}/${case_id}.score.json"

            # Color the verdict for terminal output
            case "$verdict" in
                "Excellent")    verdict_colored="${GREEN}${verdict}${NC}" ;;
                "Acceptable")   verdict_colored="${YELLOW}${verdict}${NC}" ;;
                *)              verdict_colored="${RED}${verdict}${NC}" ;;
            esac

            log_ok "Score: ${BOLD}${weighted_score}${NC} — ${verdict_colored}"
            scored=$((scored + 1))
        else
            log_err "Failed to parse judge response for ${case_id}"
            log_err "Raw response (first 200 chars): ${score_raw:0:200}"

            # Write error score
            jq -n \
                --arg id "$case_id" \
                --arg raw "${score_raw:0:500}" \
                '{
                    case_id: $id,
                    scores: { correctness: 0, code_quality: 0, security: 0, performance: 0, test_coverage: 0 },
                    weighted_score: 0,
                    verdict: "Needs fixes",
                    notes: "Judge response could not be parsed",
                    judge_status: "parse_error",
                    raw_response: $raw
                }' > "${RESULTS_DIR}/${case_id}.score.json"

            score_errors=$((score_errors + 1))
        fi
    else
        log_err "Claude judge call failed for ${case_id}"

        jq -n \
            --arg id "$case_id" \
            '{
                case_id: $id,
                scores: { correctness: 0, code_quality: 0, security: 0, performance: 0, test_coverage: 0 },
                weighted_score: 0,
                verdict: "Needs fixes",
                notes: "Judge invocation failed",
                judge_status: "error"
            }' > "${RESULTS_DIR}/${case_id}.score.json"

        score_errors=$((score_errors + 1))
    fi

    echo ""
done

# --- Summary -----------------------------------------------------------------
echo -e "${BOLD}========================================${NC}"
echo -e "${BOLD}Scoring Complete${NC}"
echo -e "${BOLD}========================================${NC}"
echo -e "  Total cases:   ${TOTAL}"
echo -e "  Scored:        ${GREEN}${scored}${NC}"
echo -e "  Errors:        ${RED}${score_errors}${NC}"
echo -e "  Results dir:   ${BOLD}${RESULTS_DIR}${NC}"
echo ""
echo -e "Next step: generate the report with:"
echo -e "  ${CYAN}./evals/reporter.sh ${RESULTS_DIR}${NC}"
