# Course Catalog API
Standalone FastAPI backend for a course catalog: describes a course with a Pydantic model, implements course list and single course routes, with filtering, sorting, and pagination.

## How to run

1. Create a virtual environment.
   ```bash
   python -m venv .venv
   ```
2. Activate the environment.
    ```bash
    For Windows (PowerShell): .venv\Scripts\Activate.ps1
    ```
3. Install dependencies.
   ```bash
    pip install -r requirements.txt
   ```
4. Start the dev server.
    ```bash
    fastapi dev main.py
    ```
6. Open the interactive documentation at http://127.0.0.1:8000/docs

## What was verified
- `GET /` returns `{"message": "Course Catalog API is running"}`

- `GET /courses` returns 6 courses. `ai-integration` first (32 likes), `api-design` last (11)

- `GET /courses?is_effective=true` returns 2 courses: `ai-integration`, `api-design`

- `GET /courses?is_effective=false` returns 4 courses: `modern-frontend`, `web-security`, `backend-fastapi`, `databases-postgresql`

- `GET /courses?sort=title` returns 6 courses alphabetically by title

- `GET /courses?page=2&page_size=2` returns `web-security` and `backend-fastapi`

- `GET /courses/web-security` returns the single course `web-security`

- `GET /courses/nope` returns 404 error with `{"detail": "Course not found"}`


# Lab5
FastAPI backend for the course catalog. Serves courses and accepts likes and enrollments.

## Running

```bash
cd course-catalog-api
.venv\Scripts\Activate.ps1        
fastapi dev main.py
```

The API is available at `http://localhost:8000`. The interactive docs are at `/docs`.

## What changed (Lab 5)

### CORS

The frontend at `http://localhost:3000` is allowed to read responses from this API. Without this permission the browser hides the response from JavaScript, even if the server itself answered 200.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

`allow_origins` contains *origins* - scheme, host and port, with **no path and no trailing slash**. `http://localhost:3000/` (with a slash) matches nothing and would block every request from the page.

### camelCase in JSON

Python code stays in `snake_case`; Pydantic renames fields in JSON. All models inherit from `CamelModel`:

```python
class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
    )
```

- `alias_generator=to_camel` - each field gets a camelCase alias (`is_effective` -> `isElective`).
- `validate_by_name=True` - accepts the Python field name when constructing objects (this is why `data.py` still uses `is_effective=True`).
- `validate_by_alias=True` - accepts the alias as well.

Query parameters are **not** affected by aliases: the filter still uses `?is_effective=true`.

### New routes

#### `POST /courses/{course_id}/like`

Increments the like counter and returns the updated course. Returns `404` if the course does not exist.

Example:

```
POST /courses/web-security/like
-> 200
{"id": "web-security", "title": "Web Security Essentials", "description": "...",
 "credits": 4, "isElective": false, "likes": 22}
```

#### `POST /enrollments`

Accepts a JSON body with `courseId` and `studentName`, creates an enrollment record and returns it with an assigned `id`. Returns `404` if the course does not exist, `422` if `studentName` is shorter than 2 characters.

Example success:

```
POST /enrollments
{"courseId": "web-security", "studentName": "Aigerim"}
-> 201
{"courseId": "web-security", "studentName": "Aigerim", "id": 1}
```

Example validation error:

```
POST /enrollments
{"courseId": "web-security", "studentName": "A"}
-> 422
{"detail": [{"loc": ["body", "studentName"], "msg": "String should have at least 2 characters", "type": "string_too_short"}]}
```

#### `GET /enrollments`

Returns all enrollments (in memory - reset on server restart).

Example:

```
GET /enrollments
-> 200
[{"courseId": "web-security", "studentName": "Aigerim", "id": 1}]
```

## In-memory storage

Likes and enrollments live in server memory (`ENROLLMENTS` list in `main.py`, `likes` field on `Course` in `data.py`). Every restart of `fastapi dev` resets them to their initial values. Persistent storage will be added later (PostgreSQL, weeks 6–7).