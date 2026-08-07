# **ARCHITECTURE**
+ PromptLab is a "Postman for Prompts" - a backend-only REST API for storing, organizing, and managing AI prompt templates. It;s a Python/FastAPI applicaiton with a deliberately simple flat architecture

```
HTTP Request
    └── FastAPI (api.py)
            ├── Pydantic validation (models.py)
            ├── Business logic / utilities (utils.py)
            └── In-memory storage (storage.py)
```

+ There is no database, no auth, no frontend, and no async I/O - it is a synchronous CRUD API.
+ The config.taml is not consumed by the backend at all
+ This is a standard 3-layer split: routes -> business logic/helpers -> storage
	+ This pattern will still be here when swapping the storage layer for a real database - the whole point of separating it out.

| FILE | FUNCTION |
| --- | --- |
| main.py | entry point, just boots uvicorn |
| app/api.py | HTTP Layer (FastAPI routes) |
| app/models.py | data shapes (Pydantic) |
| app/storage.py | data layer (in-memory dict, stands in for a DB |
| app/utils.py | pure helper functions (sorting, filtering, search) |

# **ENTRY POINTS**
+ The server starts in the backend/main.py file via uvicorn on 0.0.0.0:8000.
+ 11 routes registered in backend/app/api.py

| METHOD | PATH | STATUS |
| --- | --- | --- |
| GET | /health | Works |
| GET | /prompts | Works (sorting bug) |
| GET | /prompts/{id} | Bug 1: 500 on missing ID instead of 404 |
| POST | /prompts |  Works | 
| PUT | /prompts/{id} | Bug 2: updated_at not refreshed |
| PATCH | /prompts/{id} | Missing - noted in comment but not implemented |
| DELETE | /prompts/{id} | Works |
| GET | /collections | Works |
| GET | /collections/{id} | Works |
| POST | /collections | Works |
| DELETE | /collections/{id} | Bug 4: orphans child prompts |

# **DATA FLOW**
A request travels this path:
```mermaid
flowchart TD
    A[**HTTP IN**] -- FastAPI router in api.py matches the path and method --> B[**PYDANTIC VALIDATION**] -- The request body (if any) is deserialized and validated against a model in models.py. Invalid payloads are rejected with 422 before any route handler code runs --> C[**ROUTE HANDLER**] -- Calls storage.* methods, optionally calls utils.* helpers for filtering/sorting/search --> D[**STORAGE**] -- storage.py reads/writes the in-memory Python dicts --> E[**PYDANTIC SERIALIZATION**] -- The returned model is serialized back to JSON via the response_model annotation --> F[**HTTP OUT**] --- FastAPI sends the response
```

