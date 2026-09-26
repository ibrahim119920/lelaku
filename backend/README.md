# Lelaku Backend

FastAPI, SQLAlchemy, Psycopg 3, and Alembic. Psycopg is used for synchronous LL-05 auth/profile handlers and asynchronous trip/chat handlers through SQLAlchemy's async engine. API contracts consumed by the frontend are documented in [the auth/profile contract](../docs/auth-profile-contract.md).

## Structure

~~~text
app/
├── main.py          # FastAPI app, CORS, error handlers, and router registration
├── base.py          # shared ORM Base and UUID-as-TEXT adapter
├── models.py        # auth/profile/session/vehicle model registry
├── core/            # settings, async database session, session-backed user dependency
├── trip/            # trips, requests, members, ratings, and matching
└── chat/            # trip messages
migrations/versions/ # single Alembic chain beginning at the LL-05 schema
tests/               # LL-05 auth/config and trip/chat tests
~~~

Trip and chat endpoints use the same opaque, revocable lelaku_session cookie as LL-05. They resolve the current user from user_sessions; the temporary JWT placeholder has been removed.

users.user_id remains TEXT in PostgreSQL to preserve the LL-05 schema. The trip domain maps UUID strings to Python UUID values while keeping user foreign keys as TEXT.

## Run locally

From the repository root:

~~~powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements-dev.txt
Copy-Item backend\.env.example backend\.env
~~~

Set DATABASE_URL in backend/.env. Run migrations and start the API:

~~~powershell
python -m alembic -c backend\alembic.ini upgrade head
python -m uvicorn backend.app.main:app --reload --port 8000
~~~

APP_ENV=staging and APP_ENV=production require sslmode=verify-full. The database URL is only read by the backend; do not put it in frontend environment variables.

## Tests

Trip/chat integration tests recreate tables in a dedicated local PostgreSQL database. The test configuration rejects non-local hosts and database names that do not contain test.

~~~powershell
docker run --rm --name lelaku-pg-test -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=lelaku_test -p 55432:5432 postgres:16-alpine
~~~

In another terminal:

~~~powershell
$env:TEST_DATABASE_URL = "postgresql+psycopg://postgres:postgres@127.0.0.1:55432/lelaku_test?sslmode=disable"
python -m pytest backend\tests -q
~~~

The separate Supabase integration test remains opt-in and requires its own staging project-reference allowlist.

## Migration chain

backend/migrations/versions/20260923_0001_auth_profile_sessions.py remains the first revision. The next revisions add vehicles, trips and matching, ride requests and members, messages, and ratings. The former 0001_auth_placeholder migration is not part of the chain; it would duplicate LL-05 auth tables.

Check migration SQL without connecting to a database:

~~~powershell
python -m alembic -c backend\alembic.ini upgrade head --sql
~~~
