#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# evals/reporter.sh — Markdown report generator for scored eval results
#
# Takes a scored results directory and generates a structured markdown report
# with summary table, per-case details, and overall statistics.
#
# Usage:
#   ./evals/reporter.sh <results-dir>
#
# Examples:
#   ./evals/reporter.sh /tmp/eval-results-20240101-120000
# =============================================================================

# --- Constants ---------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORTS_DIR="${SCRIPT_DIR}/reports"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

# Verdict thresholds (for highlighting)
THRESHOLD_NEEDS_FIXES=0.7

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
${BOLD}evals/reporter.sh${NC} — Generate markdown report from scored eval results

${BOLD}USAGE${NC}
    ./evals/reporter.sh <results-dir>

${BOLD}ARGUMENTS${NC}
    <results-dir>       Path to the eval results directory that has been scored
                        (must contain .score.json files from scorer.sh)

${BOLD}OUTPUT${NC}
    Writes a markdown report to:
      evals/reports/<timestamp>.md

    Report includes:
      - Summary statistics (total, pass rate, average score)
      - Results table with per-case scores and verdicts
      - Flagged cases (below ${THRESHOLD_NEEDS_FIXES} threshold)
      - Dimension breakdown (correctness, security, etc.)

${BOLD}EXAMPLES${NC}
    ./evals/reporter.sh /tmp/eval-results-20240101-120000
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

if ! command -v jq &>/dev/null; then
    log_err "jq is required but not installed. Install it with: brew install jq"
    exit 1
fi

# Ensure reports directory exists
mkdir -p "$REPORTS_DIR"

# --- Discover scored cases ---------------------------------------------------
SCORE_FILES=()
while IFS= read -r f; do
    SCORE_FILES+=("$f")
done < <(find "$RESULTS_DIR" -name '*.score.json' | sort)

TOTAL=${#SCORE_FILES[@]}

if [[ $TOTAL -eq 0 ]]; then
    log_err "No .score.json files found in $RESULTS_DIR"
    log_err "Did you run scorer.sh first?"
    exit 1
fi

log_info "Found ${BOLD}${TOTAL}${NC} scored case(s)"

# --- Collect data for the report ---------------------------------------------
# Arrays to accumulate values
declare -a CASE_IDS=()
declare -a CASE_STACKS=()
declare -a CASE_SCORES=()
declare -a CASE_VERDICTS=()
declare -a CASE_NOTES=()
declare -a CASE_CORRECTNESS=()
declare -a CASE_CODE_QUALITY=()
declare -a CASE_SECURITY=()
declare -a CASE_PERFORMANCE=()
declare -a CASE_TEST_COVERAGE=()
declare -a FLAGGED_CASES=()

for score_file in "${SCORE_FILES[@]}"; do
    cid="$(jq -r '.case_id' "$score_file")"
    wscore="$(jq -r '.weighted_score // 0' "$score_file")"
    verdict="$(jq -r '.verdict // "Unknown"' "$score_file")"
    notes="$(jq -r '.notes // "N/A"' "$score_file")"

    # Get dimension scores
    correctness="$(jq -r '.scores.correctness // 0' "$score_file")"
    code_quality="$(jq -r '.scores.code_quality // 0' "$score_file")"
    security="$(jq -r '.scores.security // 0' "$score_file")"
    performance="$(jq -r '.scores.performance // 0' "$score_file")"
    test_coverage="$(jq -r '.scores.test_coverage // 0' "$score_file")"

    # Try to get stack from meta file
    meta_file="${RESULTS_DIR}/${cid}.meta.json"
    if [[ -f "$meta_file" ]]; then
        stack="$(jq -r '.stack // "unknown"' "$meta_file")"
    else
        stack="unknown"
    fi

    CASE_IDS+=("$cid")
    CASE_STACKS+=("$stack")
    CASE_SCORES+=("$wscore")
    CASE_VERDICTS+=("$verdict")
    CASE_NOTES+=("$notes")
    CASE_CORRECTNESS+=("$correctness")
    CASE_CODE_QUALITY+=("$code_quality")
    CASE_SECURITY+=("$security")
    CASE_PERFORMANCE+=("$performance")
    CASE_TEST_COVERAGE+=("$test_coverage")

    # Flag cases below threshold
    is_below="$(awk -v s="$wscore" -v t="$THRESHOLD_NEEDS_FIXES" 'BEGIN { print (s < t) ? "1" : "0" }')"
    if [[ "$is_below" == "1" ]]; then
        FLAGGED_CASES+=("$cid")
    fi
done

# --- Calculate aggregate statistics -----------------------------------------
calc_average() {
    local -n arr=$1
    local sum=0
    local count=${#arr[@]}
    for val in "${arr[@]}"; do
        sum="$(awk -v a="$sum" -v b="$val" 'BEGIN { printf "%.4f", a + b }')"
    done
    awk -v s="$sum" -v c="$count" 'BEGIN { printf "%.2f", s / c }'
}

avg_score="$(calc_average CASE_SCORES)"
avg_correctness="$(calc_average CASE_CORRECTNESS)"
avg_code_quality="$(calc_average CASE_CODE_QUALITY)"
avg_security="$(calc_average CASE_SECURITY)"
avg_performance="$(calc_average CASE_PERFORMANCE)"
avg_test_coverage="$(calc_average CASE_TEST_COVERAGE)"

# Count verdicts
excellent_count=0
acceptable_count=0
needs_fixes_count=0
for v in "${CASE_VERDICTS[@]}"; do
    case "$v" in
        "Excellent")    excellent_count=$((excellent_count + 1)) ;;
        "Acceptable")   acceptable_count=$((acceptable_count + 1)) ;;
        *)              needs_fixes_count=$((needs_fixes_count + 1)) ;;
    esac
done

# Determine overall verdict
overall_verdict="$(awk -v s="$avg_score" 'BEGIN {
    if (s >= 0.9) print "Excellent"
    else if (s >= 0.7) print "Acceptable"
    else print "Needs fixes"
}')"

# --- Load manifest info if available -----------------------------------------
cases_file="unknown"
run_timestamp="unknown"
if [[ -f "${RESULTS_DIR}/manifest.json" ]]; then
    cases_file="$(jq -r '.cases_file // "unknown"' "${RESULTS_DIR}/manifest.json")"
    run_timestamp="$(jq -r '.timestamp // "unknown"' "${RESULTS_DIR}/manifest.json")"
fi

# --- Generate the markdown report --------------------------------------------
REPORT_FILE="${REPORTS_DIR}/${TIMESTAMP}.md"

log_info "Generating report: ${BOLD}${REPORT_FILE}${NC}"

{
    # Header
    cat <<HEADER
# Eval Report — ${TIMESTAMP}

**Source:** \`${cases_file}\`
**Run timestamp:** ${run_timestamp}
**Report generated:** $(date -u +%Y-%m-%dT%H:%M:%SZ)
**Results directory:** \`${RESULTS_DIR}\`

---

## Summary

| Metric | Value |
|--------|-------|
| Total cases | ${TOTAL} |
| Average score | **${avg_score}** |
| Overall verdict | **${overall_verdict}** |
| Excellent (>= 0.9) | ${excellent_count} |
| Acceptable (0.7-0.89) | ${acceptable_count} |
| Needs fixes (< 0.7) | ${needs_fixes_count} |

---

## Results

| Case ID | Stack | Score | Verdict | Notes |
|---------|-------|-------|---------|-------|
HEADER

    # Table rows
    for i in "${!CASE_IDS[@]}"; do
        cid="${CASE_IDS[$i]}"
        stack="${CASE_STACKS[$i]}"
        score="${CASE_SCORES[$i]}"
        verdict="${CASE_VERDICTS[$i]}"
        notes="${CASE_NOTES[$i]}"

        # Truncate notes for the table (keep first 80 chars)
        if [[ ${#notes} -gt 80 ]]; then
            notes_short="${notes:0:77}..."
        else
            notes_short="$notes"
        fi

        # Escape pipe characters in notes for markdown table
        notes_short="${notes_short//|/\\|}"

        # Add warning emoji for flagged cases
        flag=""
        is_below="$(awk -v s="$score" -v t="$THRESHOLD_NEEDS_FIXES" 'BEGIN { print (s < t) ? "1" : "0" }')"
        if [[ "$is_below" == "1" ]]; then
            flag=" [!]"
        fi

        echo "| ${cid} | ${stack} | ${score}${flag} | ${verdict} | ${notes_short} |"
    done

    # Dimension breakdown
    cat <<DIMENSIONS

---

## Dimension Averages

| Dimension | Weight | Average Score |
|-----------|--------|---------------|
| Correctness | 30% | ${avg_correctness} |
| Code Quality | 15% | ${avg_code_quality} |
| Security | 25% | ${avg_security} |
| Performance | 20% | ${avg_performance} |
| Test Coverage | 10% | ${avg_test_coverage} |

DIMENSIONS

    # Flagged cases section
    if [[ ${#FLAGGED_CASES[@]} -gt 0 ]]; then
        cat <<FLAGGED
---

## Flagged Cases (Below ${THRESHOLD_NEEDS_FIXES})

The following cases scored below the acceptable threshold and require attention:

FLAGGED

        for cid in "${FLAGGED_CASES[@]}"; do
            # Find the index for this case
            for i in "${!CASE_IDS[@]}"; do
                if [[ "${CASE_IDS[$i]}" == "$cid" ]]; then
                    echo "### ${cid} (${CASE_STACKS[$i]})"
                    echo ""
                    echo "- **Score:** ${CASE_SCORES[$i]}"
                    echo "- **Verdict:** ${CASE_VERDICTS[$i]}"
                    echo "- **Notes:** ${CASE_NOTES[$i]}"
                    echo "- **Dimensions:** Correctness=${CASE_CORRECTNESS[$i]}, Code Quality=${CASE_CODE_QUALITY[$i]}, Security=${CASE_SECURITY[$i]}, Performance=${CASE_PERFORMANCE[$i]}, Test Coverage=${CASE_TEST_COVERAGE[$i]}"
                    echo ""
                    break
                fi
            done
        done
    else
        cat <<NO_FLAGS

---

## Flagged Cases

No cases scored below the ${THRESHOLD_NEEDS_FIXES} threshold. All cases are within acceptable range.

NO_FLAGS
    fi

    # Footer
    cat <<FOOTER

---

## Scoring Formula

\`\`\`
Weighted Score = (Correctness * 0.30) + (Code Quality * 0.15) + (Security * 0.25) + (Performance * 0.20) + (Test Coverage * 0.10)
\`\`\`

| Verdict | Threshold |
|---------|-----------|
| Excellent | >= 0.90 |
| Acceptable | 0.70 - 0.89 |
| Needs fixes | < 0.70 |

---

*Generated by evals/reporter.sh*
FOOTER

} > "$REPORT_FILE"

# --- Terminal summary --------------------------------------------------------
echo ""
echo -e "${BOLD}========================================${NC}"
echo -e "${BOLD}Report Generated${NC}"
echo -e "${BOLD}========================================${NC}"
echo -e "  Report file:    ${BOLD}${REPORT_FILE}${NC}"
echo -e "  Total cases:    ${TOTAL}"
echo -e "  Average score:  ${BOLD}${avg_score}${NC}"
echo -e "  Overall:        ${BOLD}${overall_verdict}${NC}"
echo -e "  Excellent:      ${GREEN}${excellent_count}${NC}"
echo -e "  Acceptable:     ${YELLOW}${acceptable_count}${NC}"
echo -e "  Needs fixes:    ${RED}${needs_fixes_count}${NC}"

if [[ ${#FLAGGED_CASES[@]} -gt 0 ]]; then
    echo ""
    echo -e "  ${RED}${BOLD}Flagged cases (< ${THRESHOLD_NEEDS_FIXES}):${NC}"
    for cid in "${FLAGGED_CASES[@]}"; do
        echo -e "    - ${RED}${cid}${NC}"
    done
fi

echo ""
echo -e "View the report:"
echo -e "  ${CYAN}cat ${REPORT_FILE}${NC}"
