---
name: afri-farm-commit
description: Prepare, commit, and optionally push AfriFarmAI changes. Use when the user asks to commit changes, create a commit message, prepare a PR-ready diff, run final verification, or push changes in the FastAPI, Gradio, Python 3.12, hosted-model, and CSV-based AfriFarmAI prototype.
---

# AfriFarmAI Commit Prep

Prepare a clean, verified commit that follows AfriFarmAI's current prototype architecture. Commit or push only when the user explicitly requests it.

## Project Context

- Read the nearest `AGENTS.md`, `PROJECT_SPEC.md`, and `PROJECT_STRUCTURE.md`.
- Treat `PROJECT_STRUCTURE.md` as authoritative for the current stack and file placement.
- Expect a Python 3.12 FastAPI backend, a Python Gradio frontend, Pydantic contracts, thin hosted-model/provider clients, CSV dealer data, and in-memory session state.
- Expect dependencies to be managed with `pip` and a project-root `requirements.txt`, using a project-root `.venv`.
- Do not assume Next.js, npm, PostgreSQL, SQLAlchemy persistence, or separate frontend tooling unless those files and commands actually exist in the repository.
- Do not introduce or use `uv`.
- Verify every newly added file is placed according to `PROJECT_STRUCTURE.md`.

## Guardrails

- Never commit or push `.env`, secrets, tokens, passwords, credentials, raw user content, uploaded media, or generated files that should remain ignored.
- Never include secret or sensitive values in summaries, commit messages, logs, or final responses.
- Never revert, rewrite, stage, or commit unrelated user changes.
- Do not add or commit persistent user data, diagnosis history, precise user locations, or provider payloads.
- Do not push unless the user explicitly asks.
- If the user requests a commit but not a push, stop after committing and report the commit hash.

## Workflow

1. Inspect repository state with `git status --short`.
2. Inspect staged and unstaged changes with `git diff --stat`, `git diff --cached --stat`, and targeted diffs.
3. Confirm the intended files match the requested task and current project structure.
4. Check changes for exposed secrets, unsafe agricultural guidance, sensitive logging, persistent-data additions, and unrelated edits.
5. Activate `.venv` and discover additional verification commands from `README.md`, `requirements.txt`, Docker files, CI configuration, or `scripts/`.
6. Run focused checks first, then all documented checks relevant to the changed surfaces.
7. Summarize the intended diff and verification outcome.
8. Stage only the intended files and review the staged diff.
9. Create a concise imperative commit message that reflects the staged diff.
10. Commit only after the staged diff and verification results are understood.

## Verification Guidance

- Create `.venv` with `python3 -m venv .venv` when it does not exist and environment setup is required.
- Activate it on Linux or WSL with `source .venv/bin/activate`.
- Install dependencies with `python -m pip install -r requirements.txt` when installation is required.
- For Python backend or core changes, run focused tests followed by `python -m pytest -q` when pytest is available.
- For Gradio frontend changes, run relevant Python tests and any documented application smoke or launch checks.
- For FastAPI route changes, verify request and response validation, error paths, and relevant route tests.
- For provider-client changes, verify timeout, retry, malformed-response, and low-confidence behavior without calling paid or live services unless explicitly approved.
- For dealer CSV or geolocation changes, run schema validation and dealer-distance tests when available.
- For Docker or Hugging Face Spaces changes, run documented build or configuration checks when available.
- Do not invent npm, lint, typecheck, build, database migration, or deployment commands that the repository has not configured.
- Do not claim a check passed unless it was actually run. Report unavailable or skipped checks with the reason.

## Commit Message Rules

- Start every commit message with a lowercase prefix followed by a colon and one space.
- Use `add:` for new features, routes, provider clients, UI capabilities, tests, or files.
- Use `fix:` for bugs, regressions, unsafe behavior, broken workflows, or failing tests.
- Use `update:` for documentation, prompts, configuration, copy, dependencies, or non-behavioral improvements.
- Use `refactor:` for internal restructuring that should not change behavior.
- Use `test:` for test-only changes.
- Use `chore:` for maintenance that does not fit another category.
- Keep the summary specific, imperative, and no longer than 72 characters when practical.
- Choose the prefix for the user-visible or highest-risk change when a commit spans categories.
- Avoid vague messages such as `update: changes`, `fix: bug`, or `add: stuff`.

## Push Workflow

Push only when the user explicitly requests it.

1. Confirm the current branch with `git branch --show-current`.
2. Confirm the intended remote with `git remote -v`.
3. Confirm the commit with `git log -1 --oneline`.
4. Push the current branch to the intended remote.
5. Report the remote, branch, and push result without exposing credentials.

## Output Format

Return:

1. Files committed.
2. Verification commands run and their results.
3. Commit hash and message.
4. Push result only when requested.
5. Skipped checks, reasons, and remaining risks.
