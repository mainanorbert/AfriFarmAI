# AfriFarmAI Codex Instructions

## Setup
- Read `PROJECT_SPEC.md` before work; before creating files, read `./docs/PROJECT_STRUCTURE.md` and use its documented location.
- Follow `./docs/PROJECT_STRUCTURE.md` for architecture/file placement and `PROJECT_SPEC.md` for product goals; do not create directories from illustrative entries.
- Stack: Python 3.12, single-process FastAPI backend, Gradio frontend, Pydantic, CSV dealer data, and in-memory sessions.
- Create and activate the project-root environment: `python3 -m venv .venv && source .venv/bin/activate`.
- Install dependencies with `python -m pip install -r requirements.txt`; use `pip`.
- Never expose or commit `.env` values, secrets, tokens, or credentials; `.env.example` must contain placeholders only.
- Everytime 

## Testing
- Add focused tests for changed behavior and error paths; run focused checks before full checks.
- Run tests from `.venv` with `python -m pytest -q` unless the repository documents another command.
- When relevant, cover text, voice, image, multimodal, low-confidence, timeout, invalid-input, translation, and dealer-distance paths.
- Never claim a check passed unless it was run.

## Style
- Build clear, low-bandwidth Swahili/Dholuo agricultural support for smallholder farmers in Kenya.
- Use cautious, practical diagnoses with severity/confidence, treatment, prevention, dealer guidance, and low-confidence fallbacks.
- Prefer simple Python, explicit data flow, Pydantic contracts, replaceable provider clients, and validated system boundaries.
- Add docstrings for medium/complex functions and classes; comment simple functions only when their purpose is unclear.

## Review
- For broad or architecture-changing work, present a short plan and wait for approval.
- Keep diffs scoped; do not perform unrelated rebrands, dependency changes, or refactors.
- Check every new file against `PROJECT_STRUCTURE.md` before creation and final handoff.
- Report changed files, verification commands, skipped checks, and known risks.

## Logging
- Use structured logs with severity, component, operation, and request/correlation IDs when available.
- Never log PII, secrets, precise locations, raw prompts/transcripts, uploaded media, model output, or provider payloads.
- Log failures without request content; use `CRITICAL` only when a required-service failure prevents operation.
- Use the OpenAI developer documentation MCP server for OpenAI API, ChatGPT Apps SDK, Codex, or related work.

## Repo Map
- `PROJECT_SPEC.md`: product goals and capabilities; `PROJECT_STRUCTURE.md`: authoritative architecture and file placement.
- `backend/api/`: routes/errors/middleware; `backend/services/`: provider clients; `backend/core/`: schemas/orchestration/safety/config.
- `frontend/`: Gradio UI/localization; `data/`: approved dealer reference data; `tests/`: tests; `scripts/`: development helpers.
- `requirements.txt`: pip dependencies; `.venv/`: local environment, never commit; `.env.example`: placeholders only.
- Everytime you successfully install a new package to this project add the project and exact version to `requirements.txt`

## Definition Of Done
- Changes match the request, `PROJECT_SPEC.md`, and `PROJECT_STRUCTURE.md`.
- Relevant tests pass; output is cautious, practical, localized where required, and handles low confidence.
- No secrets, raw user content, uploaded media, precise locations, or provider payloads are exposed or logged.
- Final handoff lists changed files, checks run, skipped checks, and remaining risks.

## Extra Guardrails
- Do not expose contact details except approved dealer phones in dealer data/results.
- Treat AI output as decision support; escalate severe, urgent, uncertain, or worsening cases to professionals.
- Do not recommend banned, unsafe, or unverified treatments; include safe-handling guidance when relevant.