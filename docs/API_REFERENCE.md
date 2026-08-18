# PromptLab API Reference

REST API for storing, organizing, and managing AI prompt templates and the collections that group them.

- **Base URL**: `http://localhost:8000` (default when run via `python main.py`)
- **Format**: JSON request/response bodies (`Content-Type: application/json`)
- **Interactive docs**: FastAPI auto-generates Swagger UI at `/docs` and the raw OpenAPI schema at `/openapi.json`

## Authentication

**None.** PromptLab currently has no authentication, authorization, API keys, or session/cookie handling — every endpoint is open to anyone who can reach the server. CORS is configured to allow all origins, methods, and headers (`backend/app/api.py`, `CORSMiddleware`). This is a single-user/trusted-environment tool; do not expose it on an untrusted network without adding an auth layer in front of it.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Report API health status and version |
| GET | `/prompts` | List prompts, optionally filtered by collection and/or search text |
| GET | `/prompts/{prompt_id}` | Retrieve a single prompt by id |
| POST | `/prompts` | Create a new prompt |
| PUT | `/prompts/{prompt_id}` | Replace a prompt's title, content, description, and collection |
| PATCH | `/prompts/{prompt_id}` | Partially update a prompt (only the fields provided) |
| DELETE | `/prompts/{prompt_id}` | Delete a prompt |
| GET | `/collections` | List all collections |
| GET | `/collections/{collection_id}` | Retrieve a single collection by id |
| POST | `/collections` | Create a new collection |
| DELETE | `/collections/{collection_id}` | Delete a collection (unassigns its prompts rather than deleting them) |

---

## Health

### `GET /health`

Reports the API's current health status and running version.

**curl**

```bash
curl http://localhost:8000/health
```

**fetch**

```javascript
const res = await fetch("http://localhost:8000/health");
const data = await res.json();
```

**Sample response — `200 OK`**

```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

---

## Prompts

### `GET /prompts`

Lists prompts, optionally filtered by collection and/or a search term matched against `title` and `description` (case-insensitive). Results are sorted by creation date, newest first.

| Query param | Type | Required | Description |
|---|---|---|---|
| `collection_id` | string | No | Only include prompts belonging to this collection |
| `search` | string | No | Only include prompts whose title or description contain this text |

**curl**

```bash
curl "http://localhost:8000/prompts?search=email&collection_id=3fa85f64-5717-4562-b3fc-2c963f66afa6"
```

**fetch**

```javascript
const params = new URLSearchParams({ search: "email" });
const res = await fetch(`http://localhost:8000/prompts?${params}`);
const data = await res.json();
```

**Sample response — `200 OK`**

```json
{
  "prompts": [
    {
      "id": "b7f1c9a0-1234-4a9e-9c7b-1a2b3c4d5e6f",
      "title": "Marketing Email Draft",
      "content": "Write a promotional email about {{product_name}} for {{audience}}.",
      "description": "Generates a first-draft marketing email",
      "collection_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "created_at": "2026-08-15T10:30:00Z",
      "updated_at": "2026-08-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

---

### `GET /prompts/{prompt_id}`

Retrieves a single prompt by its id.

**curl**

```bash
curl http://localhost:8000/prompts/b7f1c9a0-1234-4a9e-9c7b-1a2b3c4d5e6f
```

**fetch**

```javascript
const res = await fetch(`http://localhost:8000/prompts/${promptId}`);
const data = await res.json();
```

**Sample response — `200 OK`**

```json
{
  "id": "b7f1c9a0-1234-4a9e-9c7b-1a2b3c4d5e6f",
  "title": "Marketing Email Draft",
  "content": "Write a promotional email about {{product_name}} for {{audience}}.",
  "description": "Generates a first-draft marketing email",
  "collection_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "created_at": "2026-08-15T10:30:00Z",
  "updated_at": "2026-08-15T10:30:00Z"
}
```

**Sample response — `404 Not Found`**

```json
{ "detail": "Prompt not found" }
```

---

### `POST /prompts`

Creates a new prompt. `title` and `content` are required; `description` and `collection_id` are optional.

| Field | Type | Constraints |
|---|---|---|
| `title` | string | Required, 1–200 characters |
| `content` | string | Required, min 1 character |
| `description` | string \| null | Optional, max 500 characters |
| `collection_id` | string \| null | Optional; must reference an existing collection if provided |

**curl**

```bash
curl -X POST http://localhost:8000/prompts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Marketing Email Draft",
    "content": "Write a promotional email about {{product_name}} for {{audience}}.",
    "description": "Generates a first-draft marketing email",
    "collection_id": null
  }'
```

**fetch**

```javascript
const res = await fetch("http://localhost:8000/prompts", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    title: "Marketing Email Draft",
    content: "Write a promotional email about {{product_name}} for {{audience}}.",
    description: "Generates a first-draft marketing email",
    collection_id: null,
  }),
});
const data = await res.json();
```

**Sample response — `201 Created`**

```json
{
  "id": "b7f1c9a0-1234-4a9e-9c7b-1a2b3c4d5e6f",
  "title": "Marketing Email Draft",
  "content": "Write a promotional email about {{product_name}} for {{audience}}.",
  "description": "Generates a first-draft marketing email",
  "collection_id": null,
  "created_at": "2026-08-17T09:00:00Z",
  "updated_at": "2026-08-17T09:00:00Z"
}
```

**Sample response — `400 Bad Request`** (unknown `collection_id`)

```json
{ "detail": "Collection not found" }
```

**Sample response — `422 Unprocessable Entity`** (missing/invalid fields — FastAPI's default validation error shape)

```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

### `PUT /prompts/{prompt_id}`

Fully replaces an existing prompt's `title`, `content`, `description`, and `collection_id`. All fields in the body are required (full replace, not a partial update — use `PATCH` for that). Preserves `id` and `created_at`; refreshes `updated_at`.

**curl**

```bash
curl -X PUT http://localhost:8000/prompts/b7f1c9a0-1234-4a9e-9c7b-1a2b3c4d5e6f \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Marketing Email Draft (v2)",
    "content": "Write a promotional email about {{product_name}} for {{audience}} in a {{tone}} tone.",
    "description": "Generates a first-draft marketing email",
    "collection_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
  }'
```

**fetch**

```javascript
const res = await fetch(`http://localhost:8000/prompts/${promptId}`, {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    title: "Marketing Email Draft (v2)",
    content: "Write a promotional email about {{product_name}} for {{audience}} in a {{tone}} tone.",
    description: "Generates a first-draft marketing email",
    collection_id: "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  }),
});
const data = await res.json();
```

**Sample response — `200 OK`**

```json
{
  "id": "b7f1c9a0-1234-4a9e-9c7b-1a2b3c4d5e6f",
  "title": "Marketing Email Draft (v2)",
  "content": "Write a promotional email about {{product_name}} for {{audience}} in a {{tone}} tone.",
  "description": "Generates a first-draft marketing email",
  "collection_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "created_at": "2026-08-17T09:00:00Z",
  "updated_at": "2026-08-17T09:15:00Z"
}
```

**Errors**: `404` (prompt not found), `400` (unknown `collection_id`), `422` (invalid body) — same shapes as `POST /prompts` above.

---

### `PATCH /prompts/{prompt_id}`

Partially updates a prompt — only the fields included in the body are changed; omitted fields are left as-is. `updated_at` is always refreshed on success. Prefer this over `PUT` for single-field edits.

**curl**

```bash
curl -X PATCH http://localhost:8000/prompts/b7f1c9a0-1234-4a9e-9c7b-1a2b3c4d5e6f \
  -H "Content-Type: application/json" \
  -d '{ "title": "Marketing Email Draft (v3)" }'
```

**fetch**

```javascript
const res = await fetch(`http://localhost:8000/prompts/${promptId}`, {
  method: "PATCH",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ title: "Marketing Email Draft (v3)" }),
});
const data = await res.json();
```

**Sample response — `200 OK`**

```json
{
  "id": "b7f1c9a0-1234-4a9e-9c7b-1a2b3c4d5e6f",
  "title": "Marketing Email Draft (v3)",
  "content": "Write a promotional email about {{product_name}} for {{audience}} in a {{tone}} tone.",
  "description": "Generates a first-draft marketing email",
  "collection_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "created_at": "2026-08-17T09:00:00Z",
  "updated_at": "2026-08-17T09:20:00Z"
}
```

**Errors**: `404` (prompt not found), `400` (unknown `collection_id`, only checked when `collection_id` is explicitly included), `422` (invalid body).

---

### `DELETE /prompts/{prompt_id}`

Deletes a prompt by id.

**curl**

```bash
curl -X DELETE http://localhost:8000/prompts/b7f1c9a0-1234-4a9e-9c7b-1a2b3c4d5e6f
```

**fetch**

```javascript
const res = await fetch(`http://localhost:8000/prompts/${promptId}`, {
  method: "DELETE",
});
```

**Sample response — `204 No Content`** (empty body)

**Sample response — `404 Not Found`**

```json
{ "detail": "Prompt not found" }
```

---

## Collections

### `GET /collections`

Lists all collections.

**curl**

```bash
curl http://localhost:8000/collections
```

**fetch**

```javascript
const res = await fetch("http://localhost:8000/collections");
const data = await res.json();
```

**Sample response — `200 OK`**

```json
{
  "collections": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "Marketing",
      "description": "Prompts for marketing copy and campaigns",
      "created_at": "2026-08-10T08:00:00Z"
    }
  ],
  "total": 1
}
```

---

### `GET /collections/{collection_id}`

Retrieves a single collection by its id.

**curl**

```bash
curl http://localhost:8000/collections/3fa85f64-5717-4562-b3fc-2c963f66afa6
```

**fetch**

```javascript
const res = await fetch(`http://localhost:8000/collections/${collectionId}`);
const data = await res.json();
```

**Sample response — `200 OK`**

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Marketing",
  "description": "Prompts for marketing copy and campaigns",
  "created_at": "2026-08-10T08:00:00Z"
}
```

**Sample response — `404 Not Found`**

```json
{ "detail": "Collection not found" }
```

---

### `POST /collections`

Creates a new collection. `name` is required; `description` is optional.

| Field | Type | Constraints |
|---|---|---|
| `name` | string | Required, 1–100 characters |
| `description` | string \| null | Optional, max 500 characters |

**curl**

```bash
curl -X POST http://localhost:8000/collections \
  -H "Content-Type: application/json" \
  -d '{ "name": "Marketing", "description": "Prompts for marketing copy and campaigns" }'
```

**fetch**

```javascript
const res = await fetch("http://localhost:8000/collections", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    name: "Marketing",
    description: "Prompts for marketing copy and campaigns",
  }),
});
const data = await res.json();
```

**Sample response — `201 Created`**

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Marketing",
  "description": "Prompts for marketing copy and campaigns",
  "created_at": "2026-08-17T09:00:00Z"
}
```

**Sample response — `422 Unprocessable Entity`** (e.g. missing `name`)

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

### `DELETE /collections/{collection_id}`

Deletes a collection. Any prompts assigned to it are **unassigned** (their `collection_id` is set to `null`) rather than deleted, before the collection itself is removed.

**curl**

```bash
curl -X DELETE http://localhost:8000/collections/3fa85f64-5717-4562-b3fc-2c963f66afa6
```

**fetch**

```javascript
const res = await fetch(`http://localhost:8000/collections/${collectionId}`, {
  method: "DELETE",
});
```

**Sample response — `204 No Content`** (empty body)

**Sample response — `404 Not Found`**

```json
{ "detail": "Collection not found" }
```

---

## Error Codes & Response Format

All error responses use FastAPI's default `HTTPException` JSON shape:

```json
{ "detail": "<message>" }
```

except `422` validation errors, where `detail` is an array of per-field error objects (FastAPI/Pydantic's default shape), as shown in the `POST` examples above.

| Status | Meaning | When it occurs |
|---|---|---|
| `200 OK` | Success | Successful `GET`, `PUT`, `PATCH` |
| `201 Created` | Resource created | Successful `POST /prompts`, `POST /collections` |
| `204 No Content` | Success, no body | Successful `DELETE` |
| `400 Bad Request` | Invalid reference | `collection_id` supplied on a prompt create/update does not match an existing collection |
| `404 Not Found` | Resource missing | `prompt_id` or `collection_id` in the URL path does not exist |
| `422 Unprocessable Entity` | Invalid request body | Request body fails schema validation (missing required field, wrong type, string too long/short) — FastAPI's automatic validation, not custom-coded |

Clients should branch on **HTTP status code**, not by parsing the `detail` message text, since only the status code is a stable contract.
