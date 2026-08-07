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

| FILE | FUNCTION |
| --- | --- |
| main.py | entry point, just boots uvicorn |
| app/api.py | HTTP Layer (FastAPI routes) |
| app/models.py | data shapes (Pydantic) |
| app/storage.py | data layer (in-memory dict, stands in for a DB |
| app/utils.py | pure helper functions (sorting, filtering, search) |
