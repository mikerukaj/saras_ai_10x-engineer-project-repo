# **ARCHITECTURE**
+ PromptLab is a "Postman for Prompts" - a backend-only REST API for storing, organizing, and managing AI prompt templates. It;s a Python/FastAPI applicaiton with a deliberately simple flat architecture

```mermaid
graph TD;
	A[HTTP Request] --> B[FastAPI (api.py)];
	C -- Pydantic validation (models.py);
	C -- Business logic / utilities (utils.py);
	C -- In-memory storage (storage.py);
	D --> E[End];
```

+ There is no database, no auth, no frontend, and no async I/O - it is a synchronous CRUD API.
+ The config.taml is not consumed by the backend at all

| FILE | FUNCTION |
| main.py | entry point, just boots uvicorn |
| app/api.py | HTTP Layer (FastAPI routes) |
| app/models.py | data shapes (Pydantic) |
| app/storage.py | data layer (in-memory dict, stands in for a DB |
| app/utils.py | pure helper functions (sorting, filtering, search) |
