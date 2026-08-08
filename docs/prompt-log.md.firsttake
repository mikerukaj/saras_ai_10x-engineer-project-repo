1.1
Prompt:
You are a developer that just inherited this baserepo. Please explore this repo and discuss the following:
- Architecture. What doe this codebase do and how is it put together?
- Entry Points. Identify every route the application exposes.
- Data Flow. How does a request travel from route to storage and back?
- Models and Relationships. How do prompts and collections relate?
- Storage layer. How does it work and what are its limitations?
- External dependencies. What external depnendcies does this codebase rely on?

ARCHITECTURE
HTTP Request
    └── FastAPI (api.py)
            ├── Pydantic validation (models.py)
            ├── Business logic / utilities (utils.py)
            └── In-memory storage (storage.py)

ENTRY POINTS
The server starts in backend/main.py via uvicorn on 0.0.0.0:8000. All 11 routes are registered in backend/app/api.py:

Method	Path			Status
GET	/health			Works
GET	/prompts		Works (sorting bug)
GET	/prompts/{id}		Bug #1: 500 on missing ID instead of 404
POST	/prompts		Works
PUT	/prompts/{id}		Bug #2: updated_at not refreshed
PATCH	/prompts/{id}		Missing — noted in comment but not implemented
DELETE	/prompts/{id}		Works
GET	/collections		Works
GET	/collections/{id}	Works
POST	/collections		Works
DELETE	/collections/{id}	Bug #4: orphans child prompts
FastAPI auto-generates interactive docs at /docs (Swagger UI).

DATA FLOW
A request travels this path:

HTTP in → FastAPI router in api.py matches the path and method
Pydantic validation → the request body (if any) is deserialized and validated against a model in models.py. Invalid payloads are rejected with 422 before any route handler code runs.
Route handler → calls storage.* methods, optionally calls utils.* helpers for filtering/sorting/search
Storage → storage.py reads/writes the in-memory Python dicts
Pydantic serialization → the returned model is serialized back to JSON via the response_model annotation
HTTP out → FastAPI sends the response

There is no middleware beyond CORS (wildcard * on all origins, methods, headers).

MODELS AND RELATIONSHIPS
Defined in models.py:

Prompt
- id: UUID (auto-generated)
- title: str (1–200 chars, required)
- content: str (min 1 char, required) — the actual prompt text, supports {{variable}} template syntax
- description: optional str (max 500 chars)
- collection_id: optional str — foreign key by convention only, no referential integrity enforced
- created_at / updated_at: UTC datetimes (auto-set at creation)

Collection
- id: UUID (auto-generated)
- name: str (1–100 chars, required)
- description: optional str (max 500 chars)
- created_at: UTC datetime

Relationship: A Prompt optionally belongs to one Collection via collection_id. This is a soft reference — there is no join table, no cascade, and no enforcement. Deleting a collection leaves its prompts with a dangling collection_id (Bug #4). The storage.get_prompts_by_collection() method exists but is not called by any route.

There are three model tiers per resource: *Base (shared fields) → *Create (input, no id/timestamps) → * (full response, with id/timestamps). PromptUpdate is identical to PromptCreate and requires all fields on every PUT (no partial update / PATCH support).

STORAGE LAYER
storage.py is a module-level singleton (storage = Storage()) backed by two plain Python dicts: _prompts: Dict[str, Prompt] and _collections: Dict[str, Collection], keyed by UUID string.

What this means in practice:
- Zero persistence — every restart wipes all data
- No concurrency safety — no locks; race conditions possible under load (FastAPI can run threaded workers)
- Unbounded memory growth — no eviction, no pagination at storage level
- No query capability — filtering/search is done by loading all records into memory and iterating (see utils.py)
- The clear() method is used by test fixtures to reset state between test runs, which is the one good design choice here
- get_prompts_by_collection() is implemented but unused — dead code

The README explicitly calls this out as a known limitation and invites swapping it for a real DB

KNOWN BUGS
Known Bugs (annotated in code)
#	Location	Issue
1	api.py:73	GET /prompts/{id} calls .id on None → 500 instead of 404
2	api.py:110	PUT /prompts/{id} preserves old updated_at instead of calling get_current_time()
3	utils.py:14	sort_prompts_by_date() ignores the descending parameter — always sorts oldest-first
4	api.py:158	DELETE /collections/{id} deletes collection but leaves child prompts with a dangling collection_id

EXTERNAL DEPENDENCIES
All defined in requirements.txt:

Package	Version	Role
- fastapi	0.109.0	Web framework + routing + OpenAPI docs generation
- uvicorn	0.27.0	ASGI server (runs FastAPI)
- pydantic	2.5.3	Request/response validation and serialization
- pytest	7.4.4	Test runner
- pytest-cov	4.1.0	Test coverage reporting
- httpx	0.26.0	HTTP client used by FastAPI's TestClient in tests
No database drivers, no auth libraries, no task queues, no caching layer, no external service calls. The config.yaml references OpenRouter with placeholder API keys — that's tooling config for the developer's IDE, not consumed by the application itself.

Bottom line: This is a clean, minimal skeleton with clearly flagged bugs and intentional gaps. The four bugs are all shallow fixes. The bigger gaps are the missing PATCH endpoint, no persistence, no auth, and no frontend — all of which the README acknowledges as Week 1–4 work.
