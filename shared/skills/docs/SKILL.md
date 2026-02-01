---
name: docs
description: Generate or update documentation for changed and new files
---

# /docs

## What This Does

Delegates to the documentation-specialist agent to generate or update
documentation for files that have changed. Ensures that new APIs, components,
and modules are properly documented.

## Usage

```
/docs                     # Generate docs for all changed files
/docs path/to/file.ts     # Generate docs for a specific file
/docs --update            # Update existing docs only (no new files)
```

## How It Works

1. **Identify changed files.** Run `git diff --name-only` against the base
   branch to find files that have been added or modified.

2. **Classify documentation needs.** For each changed file, determine what
   documentation is needed:
   - **New file:** Generate full documentation (purpose, API, usage examples)
   - **Modified file:** Update existing documentation to reflect changes
   - **Deleted file:** Flag documentation that references the removed file

3. **Delegate to the documentation-specialist agent.** Use the Task tool to
   invoke the sub-agent with:
   - The full content of each changed file
   - Existing documentation files that may need updating
   - The project's documentation conventions (if a docs/ directory exists)
   - Pipeline context from `.agent-pipeline/` (implementation notes, etc.)

4. **Generate documentation.** The documentation-specialist produces:
   - **Inline documentation:** JSDoc, docstrings, or language-appropriate
     comments for exported functions, classes, and types
   - **API documentation:** For new endpoints, document method, path,
     parameters, request/response types, and error codes
   - **Component documentation:** For UI components, document props, usage
     examples, and accessibility notes
   - **Module documentation:** For new modules, document purpose, exports,
     and dependencies

5. **Report results.** The documentation-specialist returns:

   ```
   ## Documentation Report

   **Files Documented:** 5
   **New Docs Created:** 2
   **Docs Updated:** 3

   ### Changes
   - src/api/users.ts -- Added JSDoc for 3 new functions
   - src/components/UserCard.tsx -- Updated props documentation
   - docs/api/users.md -- Created API reference for /users endpoints
   ```

6. **Write pipeline artefact.** Save to `.agent-pipeline/docs.md` if running
   in a sequential pipeline.

## Documentation Standards

The documentation-specialist follows these conventions:

- Use the project's existing documentation style if one is established
- Write in clear, concise English
- Include code examples for non-obvious APIs
- Document error conditions and edge cases
- Keep documentation close to the code it describes (prefer inline docs)
- Use the project's language for type annotations in examples

## Error Handling

- If no changed files are found, report that there is nothing to document.
- If existing documentation cannot be located, create new documentation
  rather than failing.
- The documentation-specialist does not modify production code. It only
  creates or updates documentation files and inline comments.
