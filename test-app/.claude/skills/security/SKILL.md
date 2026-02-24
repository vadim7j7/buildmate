---
name: security
description: Run a security audit scanning for OWASP Top 10 vulnerabilities
---

# /security

## What This Does

Delegates to the security-auditor agent to perform a comprehensive security
audit of the codebase. Scans for OWASP Top 10 vulnerabilities and reports
findings with severity levels.

## Usage

```
/security                     # Audit all changed files
/security path/to/file.ts     # Audit a specific file
/security --full              # Audit the entire codebase
```

## How It Works

1. **Identify scope.** Determine which files to audit:
   - Changed files vs the base branch (default)
   - A specific file if one was provided
   - The entire codebase if `--full` was passed

2. **Delegate to the security-auditor agent.** Use the Task tool to invoke
   the security-auditor sub-agent with:
   - The full content of each file in scope
   - The project's dependency manifest (package.json, requirements.txt, etc.)
   - Any pipeline context from `.agent-pipeline/`

3. **Scan for OWASP Top 10 categories.** The security-auditor checks for:

   | ID   | Category                          | Examples                        |
   |------|-----------------------------------|---------------------------------|
   | A01  | Broken Access Control             | Missing auth checks, IDOR       |
   | A02  | Cryptographic Failures            | Weak hashing, plain-text secrets|
   | A03  | Injection                         | SQL, NoSQL, OS command, XSS     |
   | A04  | Insecure Design                   | Missing rate limiting, no CSRF  |
   | A05  | Security Misconfiguration         | Default creds, verbose errors   |
   | A06  | Vulnerable Components             | Known CVEs in dependencies      |
   | A07  | Auth Failures                     | Weak passwords, missing MFA     |
   | A08  | Data Integrity Failures           | Unsigned updates, insecure CI   |
   | A09  | Logging & Monitoring Failures     | Missing audit logs              |
   | A10  | Server-Side Request Forgery       | Unvalidated URLs, SSRF          |

4. **Classify findings by severity.** Each finding is assigned a severity:

   | Severity | Meaning                                                   |
   |----------|-----------------------------------------------------------|
   | CRITICAL | Exploitable vulnerability with severe impact. Fix now.    |
   | HIGH     | Significant risk. Fix before merging.                     |
   | MEDIUM   | Moderate risk. Should be addressed in this sprint.        |
   | LOW      | Minor risk. Address when convenient.                      |
   | INFO     | Observation or best-practice suggestion. No immediate risk.|

5. **Produce the report.** The security-auditor returns:

   ```
   ## Security Audit Report

   **Status:** PASS | FAIL
   **Date:** 2026-02-01
   **Files Audited:** 12
   **Findings:** 3 (1 HIGH, 1 MEDIUM, 1 LOW)

   ### Findings

   #### [HIGH] SQL Injection in getUserById (A03)
   **File:** src/db/users.ts:45
   **Description:** User input interpolated directly into SQL query.
   **Remediation:** Use parameterised queries or an ORM.

   #### [MEDIUM] Missing CSRF Protection (A04)
   **File:** src/routes/api.ts:12
   **Description:** POST endpoint lacks CSRF token validation.
   **Remediation:** Add CSRF middleware to state-changing routes.

   #### [LOW] Verbose Error Messages (A05)
   **File:** src/middleware/error.ts:8
   **Description:** Stack traces returned to client in production.
   **Remediation:** Return generic error messages in production mode.
   ```

6. **Write results.** Save to `.agent-pipeline/security.md` if running in a
   sequential pipeline.

## Pass / Fail Criteria

| Result | Condition                                                    |
|--------|--------------------------------------------------------------|
| PASS   | Zero CRITICAL or HIGH findings.                              |
| FAIL   | One or more CRITICAL or HIGH findings.                       |

## Error Handling

- If no files are in scope, report that there is nothing to audit.
- If dependency manifests are missing, skip the dependency check and note it
  in the report.
- The security-auditor does not fix issues. It reports them for the
  implementer to address.
