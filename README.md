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

## What changed

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

# Lab 7

Backend of the course catalog: FastAPI, SQLAlchemy 2.1, PostgreSQL, and Alembic migrations (Labs 4-7 of "Advanced Web Technologies").

## How to run

You need Python 3.11 or newer and PostgreSQL 16 or newer.

Once, as the `postgres` superuser, create the role and the database:

```sql
CREATE ROLE catalog_app LOGIN PASSWORD 'change-me';
CREATE DATABASE course_catalog OWNER catalog_app;
```

Then, from the project folder, run the following commands:

```bash
# 1. Environment and dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Environment variables
# Copy the example file (on Windows use: copy .env.example .env)
cp .env.example .env

# 3. Migrations and seed data
alembic upgrade head
psql -h localhost -U catalog_app -d course_catalog -v ON_ERROR_STOP=1 -f seed.sql

# 4. Run the server
fastapi dev main.py
```

API documentation: http://localhost:8000/docs. 
The password 'change-me' is for teaching; in a real project, passwords are never put into the repository.

## What changed in the API

- **Data storage:** Data is now stored in a PostgreSQL database and survives server restarts (unlike the in-memory lists from Lab 5).
- **Enrollment contract:** `POST /enrollments` now requires `studentId` (an integer) instead of `studentName`. A student must be created first via `POST /students`.
- **New routes:** 
  - `POST /students` — creates a new student.
  - `GET /enrollments` — returns the list of enrollments with student names and course titles using a JOIN.
  - `GET /stats/courses` — shows how many students are enrolled in each course, including courses with zero enrollments.
- **Course level:** Added a `level` field to courses (beginner, intermediate, advanced) and a `?level=` query parameter to the `GET /courses` filter.
- **Error handling:** Database constraint violations are now caught and mapped to HTTP 409 (Conflict) or 404 (Not Found) instead of returning 500 Internal Server Error.

## Migrations

| Command | What it does |
|---|---|
| `alembic upgrade head` | applies all the missing migrations |
| `alembic downgrade -1` | rolls back the last migration |
| `alembic current` | shows the version of the database |
| `alembic history` | shows the chain of migrations |
| `alembic revision --autogenerate -m "text"` | writes a draft from models vs. database |
| `alembic check` | reports whether the models and the database have diverged |
| `alembic upgrade 0001:0002 --sql` | prints the SQL of a migration without running it |
| `alembic stamp head` | marks the database as up to date without running migrations |

## Experiment log

| # | Experiment | What I saw | Cause | How I fixed it |
|---|---|---|---|---|
| 1 | The `uq` template in naming convention changed | `check_models.py` showed different names (e.g., `students_email_unique` instead of `students_email_key`). | The naming convention template in `db.py` didn't match the actual database constraint names. | Restored the original template `%(table_name)s_%(column_0_N_name)s_key`. |
| 2 | Min length removed from `StudentIn`, name "N" | Server returned 500 Internal Server Error. Traceback showed `CheckViolation` on `students_name_check`. | The request passed Pydantic validation but was rejected by the database `CHECK` constraint. The constraint was not in our error dictionary. | Restored `Field(min_length=2)` in `schemas.py`. |
| 3 | A typo in a constraint name in the dictionary | Server returned 500 Internal Server Error. Traceback showed the real name was `students_email_key`. | The key in `CONSTRAINT_ERRORS` didn't exactly match the database constraint name. | Fixed the key back to `students_email_key`. |
| 4 | `title` without NOT NULL in the database, `alembic check` | `alembic check` failed with `Detected NOT NULL on column 'courses.title'`. | Someone manually altered the database schema, making it different from the model. | Ran `ALTER TABLE courses ALTER COLUMN title SET NOT NULL;` in psql. |
| 5 | Automatic migration 0002 on existing data | `alembic upgrade` failed with `NotNullViolation: column "level" contains null values`. | Alembic tried to add a non-nullable column to a table that already had rows, so it didn't know what value to put. | Split the migration into 3 steps: add as nullable, fill with `UPDATE`, then alter to `NOT NULL`. |
| 6 | `import models` commented out in `env.py` | `alembic revision --autogenerate` generated a migration to drop all tables (`op.drop_table...`). | Without importing `models`, SQLAlchemy metadata was empty, so Alembic thought the database had extra tables. | Uncommented `import models` in `env.py` and deleted the bad migration file. |
| 7 | A `phone` field in the model without a migration | `alembic check` failed with `Detected added column 'students.phone'`. | The model was updated, but no migration was generated to reflect the change in the database. | Removed the `phone` field from the model for this experiment. |
| 8 | Two migrations from one revision | `alembic upgrade head` failed with `Multiple head revisions are present`. | Two developers created migrations from the same base revision (`0002`), creating two parallel heads. | Ran `alembic merge heads -m "..."` to create a merge migration. |

## Decisions

- **Why is the API response chosen by the constraint name rather than by SQLSTATE?** 
  SQLSTATE only shows the *type* of error (e.g., 23505 for uniqueness). But we have two unique constraints (email and enrollment). The constraint name is unique and tells us exactly *which* rule was violated.
- **Why is it better to catch the error after `commit()` than to check with a `SELECT` in advance?** 
  Checking in advance (e.g., "does this email exist?") creates a race condition: between the check and the insert, another request might take the same email. It's better to try the insert and handle the database's rejection (EAFP principle).
- **Why is a like incremented with `UPDATE courses SET likes = likes + 1` rather than by reading the number into the program?** 
  If two users like a course at the same time, reading the value, incrementing it in Python, and saving it back can cause a "lost update". The database engine handles `likes + 1` atomically, preventing lost updates.
- **Why is migration 0002 split into three steps?** 
  Because the table already had data. We can't add a `NOT NULL` column without a default value to a table with rows. We add it as nullable, fill it with data, and then make it `NOT NULL`.

## Migration 0002 self-check

| What to check | Result |
|---|---|
| **Goal and steps** | Yes. The goal is to add `level`. Steps: add nullable, fill data, make NOT NULL. |
| **Data** | Existing rows were filled with 'beginner'/'intermediate' based on `is_elective`. |
| **Renames and drops** | No renames or drops in this migration. |
| **Rollback** | Yes, `downgrade` drops the `level` column. Acceptable for this training project. |
| **Verification** | SQL from `--sql` was read. Upgrade -> downgrade -> upgrade cycle tested. `alembic check` is clean. |
| **History** | Single head. Migration is committed together with the model changes. |
| **Application** | `CourseOut` schema and `seed.sql` updated. Filter `?level=` added. |