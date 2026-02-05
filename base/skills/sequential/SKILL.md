---
name: sequential
description: Run tasks through a pipeline where each stage feeds context to the next
---

# /sequential

## What This Does

Runs a series of stages in a defined order, where each stage writes its output
to `.agent-pipeline/` and the next stage reads that output as context. This is
the standard execution mode for the implement-test-review pipeline.

## Usage

```
/sequential implement test review         # Run three stages in order
/sequential implement test review eval docs  # Full pipeline
/sequential --from test                   # Resume pipeline from the test stage
```

## How It Works

1. **Parse stages.** Extract the ordered list of stages from the input. Valid
   stage names are:

   | Stage      | Agent                    | Artefact                        |
   |------------|--------------------------|---------------------------------|
   | implement  | implementer              | `.agent-pipeline/implement.md`  |
   | test       | tester                   | `.agent-pipeline/test.md`       |
   | review     | reviewer                 | `.agent-pipeline/review.md`     |
   | eval       | eval-agent               | `.agent-pipeline/eval.md`       |
   | security   | security-auditor         | `.agent-pipeline/security.md`   |
   | docs       | documentation-specialist | `.agent-pipeline/docs.md`       |

2. **Initialise pipeline directory.** Run `scripts/run-pipeline.sh init` to
   create `.agent-pipeline/` and write `pipeline.json` with the stage list
   and initial status.

3. **Execute stages in order.** For each stage:
   a. Mark the stage as `in_progress` in `pipeline.json`.
   b. Gather context from all previous stages' artefacts.
   c. Delegate to the appropriate agent via the Task tool, passing:
      - The task description
      - All previous stage artefacts as context
      - The feature file from `.claude/context/features/` if applicable
   d. The agent writes its output to the corresponding artefact file.
   e. Mark the stage as `completed` in `pipeline.json`.

4. **Handle failures.** If a stage fails:
   - Mark it as `failed` in `pipeline.json`.
   - **Stop the pipeline immediately.** Do not proceed to subsequent stages.
   - Report which stage failed, the error details, and which stages were
     skipped.

5. **Resume support.** If `--from <stage>` is passed:
   - Skip all stages before the specified one.
   - Read existing artefacts from previous stages as context.
   - Continue execution from the specified stage.

6. **Report summary:**

   ```
   ## Pipeline Report

   **Stages:** 5
   **Completed:** 5
   **Failed:** 0

   | Stage     | Status    | Duration |
   |-----------|-----------|----------|
   | implement | COMPLETED | 30s      |
   | test      | COMPLETED | 15s      |
   | review    | COMPLETED | 20s      |
   | eval      | COMPLETED | 10s      |
   | docs      | COMPLETED | 12s      |

   **Total Duration:** 87s
   ```

## Pipeline State

The pipeline state is tracked in `.agent-pipeline/pipeline.json`:

```json
{
  "started_at": "2026-02-01T12:00:00Z",
  "stages": [
    { "name": "implement", "status": "completed", "duration_ms": 30000 },
    { "name": "test", "status": "completed", "duration_ms": 15000 },
    { "name": "review", "status": "in_progress", "duration_ms": null }
  ]
}
```

## Error Handling

- If no stages are provided, default to the full pipeline:
  `implement test review eval security docs`.
- If an invalid stage name is given, report the error and list valid stages.
- If `.agent-pipeline/` already exists and `--from` is not used, prompt
  whether to overwrite or resume.
- On failure, the pipeline can be resumed with `/sequential --from <stage>`.
