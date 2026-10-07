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

