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

# Laboratory work 8: GraphQL Alongside REST

## How to run

You need Python 3.11 or newer and PostgreSQL 16 or newer.

Once, as a PostgreSQL administrator, create the role and database:

```sql
CREATE ROLE catalog_app LOGIN PASSWORD 'change-me';
CREATE DATABASE course_catalog OWNER catalog_app;
```

From the project folder, create the environment, install dependencies, configure the database, and start the API:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
psql -h localhost -U catalog_app -d course_catalog -v ON_ERROR_STOP=1 -f seed.sql
fastapi dev main.py
```

REST docs: http://localhost:8000/docs. GraphiQL: http://localhost:8000/graphql. The password `change-me` is for training; real passwords don't go into a repository.

## What changed in the API

- Enrollment, student-creation, and like rules live in `services.py`. `problem.py` translates expected service errors and HTTP errors into RFC 9457 Problem Details with the `application/problem+json` content type.
- Strawberry serves GraphQL at `/graphql`; opening the address in a browser shows GraphiQL, where queries can be written and checked against the schema.
- `enroll` and `likeCourse` mutations return expected rule failures in `data.*.userErrors`. Query-validation and unexpected execution errors are returned in `errors`; an unexpected resolver error is masked as `Unexpected error.`.
- `X-SQL-Queries` reports the number of SQL statements executed for each HTTP request and makes the N+1 problem measurable.
- GraphQL limits query depth to 5 and aliases to 10, validates `limit` to the range 1–100, parses student IDs before querying, and masks unexpected internal errors. `GRAPHQL_INTROSPECTION` controls whether schema introspection is enabled.
- `GET /students/{student_id}` and `GET /students/{student_id}/enrollments` provide the REST data for the My courses screen.

## Example queries

The My courses query (set Variables to `{"id": "2"}`):

```graphql
query MyCourses($id: ID!) {
  student(id: $id) {
    name
    enrollments {
      id
      course { title credits level }
    }
  }
}
```

The enroll mutation (set Variables to `{"input": {"courseId": "web-security", "studentId": "3"}}`):

```graphql
mutation Enroll($input: EnrollInput!) {
  enroll(input: $input) {
    enrollment { id enrolledAt course { title } }
    userErrors { code message }
  }
}
```

Successful response:

```json
{
  "data": {
    "enroll": {
      "enrollment": {
        "id": "13",
        "enrolledAt": "2026-11-25T23:26:26.089545+05:00",
        "course": { "title": "Web Security Essentials" }
      },
      "userErrors": []
    }
  }
}
```

Repeated enrollment response:

```json
{
  "data": {
    "enroll": {
      "enrollment": null,
      "userErrors": [
        {
          "code": "ALREADY_ENROLLED",
          "message": "Student is already enrolled in this course"
        }
      ]
    }
  }
}
```

Enrollment IDs and timestamps are generated by the database and differ between runs.

## REST vs GraphQL comparison

Measurements are for student 2 and the starting data.

| Criterion | REST | GraphQL | Source |
|-----------|------|---------|--------|
| Requests and rounds per screen | 5 requests, 2 rounds | 1 request, 1 round | `measure.py` |
| Bytes in the responses | 1147 | 339 | `measure.py` |
| SQL queries per screen | 5 | 3 | `measure.py`, `X-SQL-Queries` |
| SQL growth with more students | The joined enrollments endpoint uses one SQL query per request | Before DataLoaders: 7/7 queries for 3 students and 27/24 for 20; after DataLoaders: 3/3 at both sizes | `try_n_plus_1.py` |
| Error in the query text | REST reports a missing resource with 404 Problem Details | HTTP 200 with `data: null` and an `errors` entry | Experiments 1 and 8 |
| Expected rule error (repeated enrollment) | HTTP 409 Problem Details, type `already-enrolled` | HTTP 200 with `userErrors[0].code = ALREADY_ENROLLED` | Steps 1 and 4 |
| HTTP cache | GET routes can be cached by URL and HTTP cache rules | POST requests are not normally cached; a GraphQL GET query can be cached, while mutations with GET are rejected | Lecture section 14, experiment 3 |
| Protection from expensive queries | Fixed route shapes | Depth 5, at most 10 aliases, bounded `limit`, checked IDs, masked internal errors, configurable introspection | Experiments 6 and 7 |

**Conclusion.** REST is a good fit for fixed resources and standard GET caching, and its joined enrollment response stays at one SQL query. For a nested screen whose client needs only selected fields, GraphQL reduced this measurement from 5 requests over 2 rounds and 1147 bytes to 1 request over 1 round and 339 bytes. Lazy loading initially grew to 27 and 24 SQL queries for 20 students; request-scoped DataLoaders brought both queries back to 3. GraphQL therefore suits flexible nested screens when its query limits and error handling are enabled.

## Experiment log

| # | Experiment | What I saw | Cause | How I fixed it |
|---|------------|------------|-------|----------------|
| 1 | A typo in a field name and an argument in `snake_case` | HTTP 200, `data: null`, and an `errors` message with `Did you mean 'title'` or `isElective` | GraphQL validates names against the schema before running the resolver; Strawberry exposes Python `snake_case` names as GraphQL `camelCase` | Corrected the field and argument names |
| 2 | Removed `\| None` from the `course` query and requested a nonexistent course | `data: null`; `Cannot return null for non-nullable field Query.course.` with path `["b"]` | The schema's `!` promised a non-null result; the failure nulled the nearest nullable parent and discarded the other alias too | Restored `CourseType \| None` |
| 3 | Sent a mutation with GET | The read query returned 200; the mutation returned 400 text `mutations are not allowed when using GET`; likes stayed at 11 | GET is safe and may be repeated or cached, so mutations must not run through it | Sent changes with POST |
| 4 | Measured nested queries with 3 and then 20 students | Before batching: 7/7 SQL queries for 3 students, 27/24 for 20; GraphiQL still returned one response | Lazy relationship loading issued separate SQL for each object; the response and HTTP status did not show the database work | Batched relationship loads with DataLoaders |
| 5 | Returned rows from the batch query in descending database order | The students query failed with `expected: 3, received: 6`; the enrollments query returned wrong courses for enrollments 2, 4, 5, and 6 without an error | The loader assigned rows by position, but database result order did not match the keys; a matching result count can still silently misassign data | Grouped rows by their key and returned results in key order |
| 6 | Sent a depth-6 cycle, 12 aliases, invalid limits and IDs, and an introspection query | Without protection, the cycle and aliases ran; invalid inputs exposed database or Python errors and SQL details. With protection: depth 5 and aliases 10 were enforced, `limit` and ID errors were clear, and internal errors became `Unexpected error.`. The 12-like mutation was rejected with 0 SQL queries | Without query limits, a client controls query cost; unmasked exceptions can expose SQL, table/column names, and parameter values | Added the depth and alias limiters, explicit argument checks, and error masking |
| 7 | Disabled introspection and queried the schema, an ordinary field, and a typo | `__schema` was rejected, ordinary queries still worked, and a typo still suggested `course` or `courses` | Disabling introspection hides schema discovery but does not hide fields or authorize access to data | Restored `GRAPHQL_INTROSPECTION=true` |
| 8 | Broke the GraphQL query, removed the client's `errors` check, and stopped the API | The typo produced `GraphQLRequestError: Cannot query field 'titel'`; without the check the page showed a destructuring `TypeError`; with the API stopped it showed `TypeError: fetch failed` | HTTP 200 can contain GraphQL errors; discarding them hides the cause, while a network failure has no GraphQL response | Restored the query and the `errors` check, then restarted the API |

The unprotected database errors disclosed SQL text, schema names, and submitted parameter values. `Invalid ID: 'abc'` helps a client correct its request, while `Unexpected error.` is intentionally non-specific and hides internal details. Lowering the depth limit to 2 would reject the legitimate `student → enrollments → course` My courses query.

## Decisions

- The application rule and its error code are defined once in `services.py`; `problem.py` and the GraphQL resolver translate them into their own response formats. Duplicating the rule in both transports could make the two APIs disagree after a later change.
- Loaders are created in the request context so their cache cannot leak between requests or become stale across users. The batch function maps each row to its key because SQL result order is not guaranteed; assigning by position can silently return another course.
- `check_limit` and `parse_id` return actionable messages for invalid client input, while `MaskErrors` hides unexpected failures such as database exceptions. This two-layer approach helps clients fix their requests without disclosing internal SQL or schema details.

## Bonus Task 1: Validation errors as Problem Details

The `RequestValidationError` handler uses `exc.errors()` to get Pydantic's list of validation failures, then maps each item's location and message into `in`, `field`, and `detail`. A request with both a short name and an invalid email now returns 422 with `application/problem+json` and both entries in the `errors` array. The `errors` array is an extension because RFC 9457 defines common problem fields but does not require an API-specific list of invalid fields; the extension lets a client correct multiple values in one response.
