# AfriFarmAI – Project Structure (documentation-only)

Root name: AfriFarmAI
Root path: /home/nober/codex-study/codex_scafold/AfriFarmAI


## Design principles for this one-off prototype

- Simple first: single-process FastAPI + Gradio, minimal dependencies, no DB.
- Clear boundaries: UI, API, service clients, core orchestration, and data contracts are separated.
- Ephemeral by default: no persistent user data; only in-memory session state.
- Scalable-enough naming: paths align with common Python/Gradio practices for future extension without refactors.

## Repository tree (ASCII, documentation-only)

AfriFarmAI/
├─ backend/                               # Backend (FastAPI) – API routers, services, core orchestration
│  ├─ api/                            # HTTP endpoints and error/middleware surface
│  │  ├─ stt.py                       # /api/stt – Cohere Transcribe bridge (request/response shaping)
│  │  ├─ translate.py                 # /api/translate – Tiny Aya 3B translation
│  │  ├─ vision.py                    # /api/vision – MiniCPM-V 4.6 image analysis
│  │  ├─ reason.py                    # /api/reason – Nemotron 30B reasoning
│  │  ├─ tts.py                       # /api/tts – TTS REST proxy (sw/en)
│  │  ├─ dealers.py                   # /api/dealers/find – dynamic Google Places lookup
│  │  ├─ analyze.py                   # /api/analyze – end-to-end orchestration
│  │  ├─ errors.py                    # Error taxonomy -> HTTP mapping
│  │  └─ middleware.py                # Timeouts, logging, rate limiting
│  ├─ services/                       # Thin clients for external/hosted models and providers
│  │  ├─ cohere_transcribe_client.py  # STT client (timeouts, retries, confidence handling)
│  │  ├─ tiny_aya_client.py           # Translation client with small LRU cache
│  │  ├─ minicpmv_client.py           # Vision client (image prep, prompt)
│  │  ├─ nemotron_client.py           # Reasoning client (JSON-only enforcement)
│  │  ├─ openai_vision_client.py       # GPT-5.4 image-diagnosis fallback
│  │  ├─ tts_client.py                # Pluggable REST TTS
│  │  └─ google_places.py             # Required nearby-agrovet search tool
│  ├─ core/                           # Cross-cutting app logic, schemas, prompts, safety, utils
│  │  ├─ config.py                    # Env var loader and validation (read-once)
│  │  ├─ models.py                    # Pydantic schemas (requests/responses/shared)
│  │  ├─ prompts.py                   # Prompt templates (vision/reason) – compact, deterministic
│  │  ├─ safety.py                    # Post-processing, safety filters, coercions
│  │  ├─ cache.py                     # Short-string translation cache (LRU), session helpers
│  │  ├─ distance.py                  # Haversine distance calculation
│  │  └─ geolocation.py               # Browser-coordinate resolution
│  └─ __init__.py                     # Package marker (if needed by tooling)
├─ frontend/                          # Gradio frontend (Blocks layout, components, strings plan)
│  ├─ app_ui.py                       # One-screen layout and wiring to API endpoints
│  ├─ components.py                   # Reusable UI pieces (badges, panels, modals)
│  └─ strings.py                      # Localized UI keys (sw/en) – loaded, not generated
├─ tests/                             # Documentation-first test plans and intents
│  ├─ test_smoke_stt.py               # STT smoke (spec-only until implemented)
│  ├─ test_smoke_translate.py
│  ├─ test_smoke_vision.py
│  ├─ test_smoke_reason.py
│  ├─ test_smoke_tts.py
│  ├─ test_google_places.py
│  ├─ test_geolocation.py
│  ├─ test_distance.py
│  ├─ test_end_to_end.py
│  └─ fixtures/                       # Described sample media/data (references only)
│     └─ README.md
├─ docs/                              # Specifications and operational notes (authoritative)
│  ├─ REQUIREMENTS.md                 # Product goals and constraints (given)
│  ├─ PROJECT_SPEC.md                 # Implementation spec (contracts, flows)
│  ├─ PROMPT_GUIDE.md                 # Prompt intents and JSON contract notes
│  ├─ OPERATIONS_NOTES.md             # Health checks, timeouts, privacy, rate limits
│  ├─ DECISIONS.md                    # PM final scope/providers/copy approvals
│  ├─ UI_WIREFRAMES.md                # Designer one-screen Blocks layout
│  ├─ UX_COPY.md                      # Localized strings (sw/en)
│  ├─ ACCESSIBILITY_NOTES.md          # Low-end screen guidance
│  ├─ OPS_CHECKLIST.md                # Provisioning and SLOs
│  └─ (links to AGENT_TASKS.md)       # Role-based deliverables
├─ app/ api/ services/ core/          # (reiterated for clarity – see above)
├─ .env.example                       # All env vars with placeholders and comments
├─ README.md                          # Purpose, quickstart (docs-only), how to run locally
└─ AGENT_TASKS.md                     # Role task plan and gates

Note: Folder duplication above is illustrative; only one app/ exists. This tree is descriptive only; do not create directories from this document.

## Purpose notes (major folders)

- backend/: Backend source boundary. Keeps API routers (transport concerns) separate from services (providers) and core (domain glue: prompts, safety, config, schemas). Enables quick stubbing and integration swaps (e.g., hosted vs local models).
- frontend/: Gradio-only concerns. Keeps layout and component composition independent of backend details, referencing API contracts from docs.
- tests/: Test intent and smoke coverage aligned to acceptance criteria. Focused on step latencies, safety rules, and error paths.
- docs/: Single source of truth for requirements, specs, prompts, operations, and role gates. Coding agents implement to these docs, not vice versa.
- scripts/: Operational helpers to validate data and assist dev flows; not required at runtime.
- .env.example: Centralizes configuration per PROJECT_SPEC Section 7; read once at startup.
