---
name: review
description: Delegate to the mobile-code-reviewer agent for React Native code review
---

# /review -- React Native Code Review

## What This Does

Identifies changed files in the current branch, delegates a code review to the
`mobile-code-reviewer` agent, and reports findings categorised as blockers,
warnings, or suggestions. Enforces React Native architecture conventions,
state management boundaries, and performance best practices.

## Usage

```
/review                   # Review all changed files vs base branch
/review path/to/file.tsx  # Review a specific file
/review --staged          # Review only staged changes
```

## How It Works

### 1. Identify Changed Files

Run `git diff --name-only` against the base branch (typically `main` or `master`)
to build the list of files to review. If `--staged` is passed, use
`git diff --cached --name-only` instead. If a specific file is provided, review
only that file.

### 2. Gather Context

Read each changed file in full. Also read:
- `.agent-pipeline/implement.md` if it exists (implementation notes)
- `.agent-pipeline/test.md` if it exists (test results)
- The relevant feature file from `.claude/context/features/`
- `constants/` files for theme reference
- `queries/queryKeys.ts` for query key conventions

### 3. Delegate to mobile-code-reviewer

Use the Task tool to invoke the `mobile-code-reviewer` sub-agent with:
- The list of changed files and their full contents
- The diff for each file
- Any gathered pipeline context
- The project's TypeScript and linting configuration

### 4. Architecture Enforcement

The reviewer checks for automatic BLOCKERs:

| Rule | Violation |
|------|-----------|
| Zustand for UI state only | Server data or DB records in Zustand store |
| React Query for data | Direct API calls or DB queries in components |
| Drizzle queries in db/queries/ | DB queries scattered outside db/queries/ |
| FlashList for long lists | ScrollView + map() or FlatList for 20+ items |
| StyleSheet.create | Inline style objects |
| Theme constants | Hardcoded colours, spacing, or font sizes |
| expo-router | Direct React Navigation usage |

### 5. Collect and Report Results

```markdown
## Code Review Results

**Verdict:** APPROVE | REQUEST_CHANGES

### Blockers (must fix)
- [file:line] Description of the architecture violation

### Warnings (should fix)
- [file:line] Description of the concern

### Suggestions (nice to have)
- [file:line] Description of the improvement

### Quality Gate Status
- TypeScript: PASS / FAIL / NOT RUN
- Lint: PASS / FAIL / NOT RUN
- Tests: PASS / FAIL / NOT RUN
```

### 6. Write Pipeline Artefact

If running as part of a sequential pipeline, write results to
`.agent-pipeline/review.md`.

## Review Focus Areas

### State Management (CRITICAL)
See `references/rn-performance.md` for performance patterns and
`references/rn-platform.md` for platform-specific patterns.

1. Zustand stores must contain ONLY UI state
2. React Query must be used for ALL data fetching
3. Drizzle queries must live in `db/queries/`
4. Query keys must use the centralised factory

### Performance
1. FlashList with estimatedItemSize for lists
2. React.memo on list item components
3. useCallback for event handlers passed to children
4. No anonymous functions in renderItem
5. expo-image instead of Image

### Platform
1. Platform.OS checks where iOS/Android differ
2. SafeAreaView or useSafeAreaInsets
3. iOS header buttons, Android FABs
4. KeyboardAvoidingView behaviour per platform

### TypeScript
1. No `any` usage
2. No unsafe `as` casts
3. Exported interfaces for props
4. Strict null handling

## Verdicts

| Verdict          | Meaning                                              |
|------------------|------------------------------------------------------|
| APPROVE          | No blockers. Warnings and suggestions are advisory.  |
| REQUEST_CHANGES  | At least one blocker must be resolved before merge.  |

## Error Handling

- If no changed files are found, report that there is nothing to review
- If the diff is too large (>200 files), suggest splitting into smaller PRs
  and review only the first 50 files
