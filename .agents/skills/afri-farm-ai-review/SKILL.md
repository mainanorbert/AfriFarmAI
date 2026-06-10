---
name: afri-farm-ai-review
description: Review AfriFarmAI changes before a commit, pull request, merge, or handoff. Use for code-review requests, broad diffs, agricultural AI safety checks, privacy and logging checks, architecture compliance, and verification planning in the AfriFarmAI project.
---

# AfriFarmAI Code Review

Review AfriFarmAI changes with a code-review stance: findings first, ordered by severity, with concrete file and line references where possible.

## Workflow

1. Read the nearest `AGENTS.md`, before reviewing.
2. Inspect repository state with `git status --short`.
3. Inspect staged and unstaged changes with `git diff --stat`, `git diff --cached --stat`, and targeted diffs.
4. Verify every new file is placed according to `PROJECT_STRUCTURE.md`.
5. Prioritize bugs, regressions, privacy risks, unsafe agricultural guidance, missing tests, and project-rule violations.
6. Keep unrelated user changes intact; do not revert or rewrite unrelated work.

## Review Checklist

- Verify no `.env`, secret, token, password, credential, or provider key values are printed, summarized, logged, committed, or exposed.
- Verify logs exclude PII, precise user locations, raw prompts, transcripts, uploaded media, model output, and provider payloads.
- Verify failed required-service connections use an appropriate severity and are logged at `CRITICAL` when they prevent the application from operating.
- Verify AI diagnoses use cautious language, include low-confidence fallbacks, and recommend professional help for severe, urgent, uncertain, or worsening cases.
- Verify treatment guidance does not recommend banned, unsafe, or unverified products or practices.
- Verify user-facing responses support clear multilingual and low-literacy use where relevant.
- Verify user and session data remain ephemeral and no persistent database or new personal-data collection was added without approval.
- Verify FastAPI, Gradio, service-client, core, data, and test changes follow the boundaries in `PROJECT_STRUCTURE.md`.
- Verify medium or complex functions and classes have docstrings; simple functions should have a one-line comment only when helpful.
- Verify provider responses, uploads, coordinates, and structured model output are validated at system boundaries.
- Verify relevant focused tests exist and cover changed success, failure, timeout, and low-confidence paths.

## Verification

- Run the smallest relevant checks first, then the full checks documented by the repository.
- Use `pytest -q` for the full Python test suite when test configuration is available and no different command is documented.
- Do not claim a command passed unless it was actually run.
- Record skipped checks and explain why they were skipped.

## Output Format

Return:

1. Findings: severity, file/line, issue, impact, and suggested fix.
2. Open questions or assumptions.
3. Brief change summary only after findings.
4. Verification commands run or recommended, including skipped checks.

If no issues are found, say that clearly and mention residual risks or test gaps.
