# **FIRST PROMPT**
+ I am using a vscode setup predominantly switching between Claude Code and Copilot. The first prompt I made was to claude code from vscode and went as follows:
> You are a developer that just inherited this baserepo. Please explore this repo and discuss the following:
> - Architecture. What doe this codebase do and how is it put together?
> - Entry Points. Identify every route the application exposes.
> - Data Flow. How does a request travel from route to storage and back?
> - Models and Relationships. How do prompts and collections relate?
> - Storage layer. How does it work and what are its limitations?
> - External dependencies. What external depnendcies does this codebase rely on?

## **First Response**
+ This was a decent response, and certainly gave me a high level overview of the codebase and pointed out where the bugs lie that I will have to resolve in the future. 
+ Some of the most useful parts were the quick Architecture diagram it put together and the table of entry points you can see below:

> ```
> HTTP Request
>     └── FastAPI (api.py)
>             ├── Pydantic validation (models.py)
>             ├── Business logic / utilities (utils.py)
>             └── In-memory storage (storage.py)
> ```

> | METHOD | PATH | STATUS |
> | --- | --- | --- |
> | GET | /health | Works |
> | GET | /prompts | Works (sorting bug) |
> | GET | /prompts/{id} | Bug 1: 500 on missing ID instead of 404 |
> | POST | /prompts |  Works |
> | PUT | /prompts/{id} | Bug 2: updated_at not refreshed |
> | PATCH | /prompts/{id} | Missing - noted in comment but not implemented |
> | DELETE | /prompts/{id} | Works |
> | GET | /collections | Works |
> | GET | /collections/{id} | Works |
> | POST | /collections | Works |
> | DELETE | /collections/{id} | Bug 4: orphans child prompts |
