# Design notes & tradeoffs

A short, honest tour of the decisions behind this submission — what was chosen, why, and what I'd change with more time or for production. Intended as a companion to the [README](README.md) and as talking points for a walkthrough.

## Shape of the codebase

Four layers, each with a single responsibility:

```
routes  ->  services  ->  repositories  ->  database (ORM entities)
                |
             mappers  (entity <-> internal model <-> API response)
```

- **Routes** only handle HTTP concerns (status codes, auth guards, request/response shapes).
- **Services** hold business rules (uniqueness checks, report aggregation, verification flow).
- **Repositories** are the only code that touches the database. Swapping the persistence layer means touching this layer alone.
- **Mappers** keep the database schema from leaking into the API contract, so the two can evolve independently.

This is more structure than a toy CRUD app strictly needs, but it makes the boundaries explicit and the pieces independently testable, which is the point of the exercise.

The code is formatted with **black** + **isort** and linted with **flake8** (plus **pylint** and **vulture** for deeper static and dead-code analysis); config lives in `pyproject.toml` / `.flake8`, and the shipped code passes black/isort/flake8 cleanly.

## Dependency injection (`container.py`)

`dependency-injector` wires everything in one place:

- **Singletons** for shared, app-lifetime resources — the database manager, the message queue, the upload-progress publisher.
- **Factories** for per-request services, each bound to the request's database session.

The payoff is testability: any provider can be overridden (`container.user_service.override(...)`) so a service can be tested with a fake repository, or a route with a fake service, without monkeypatching imports.

## Database & the fallback

The default is a local SQLite file so the project runs with `pip install` + `python run.py` and nothing else. The access layer is async throughout (`AsyncSession`), so the *same* code runs on SQLite (`aiosqlite`) locally and PostgreSQL (`asyncpg`) in production.

`database.py` tries the configured `DATABASE_URL` first and falls back to SQLite if it can't connect. The intent: the service should always start in an evaluation environment, while still being pointed at a real database via one env var.

**Tradeoff:** SQLite and Postgres aren't identical (types, concurrency, `ON CONFLICT` semantics). The fallback is a convenience for evaluation, not a claim that SQLite is production-ready.

## Bulk CSV ingestion

The upload endpoint parses + validates the file, records an `UploadJob`, and returns a `job_id` immediately (202). Ingestion runs in the background in chunks, updating progress and publishing an event per chunk; the client polls the status endpoint.

- **As shipped:** `BackgroundTasks` (same process) and per-row inserts with a duplicate-WID guard.
- **Production:** a separate worker consuming RabbitMQ, doing `INSERT ... ON CONFLICT DO NOTHING` in batches. The publisher is already abstracted (`src/mq_messaging/`), so this is a swap, not a rewrite.

**Tradeoff:** `BackgroundTasks` work is lost if the process dies mid-job and doesn't scale beyond the one process — acceptable for this scope, which is exactly why the queue boundary exists.

## Auth & RBAC

- JWT (`python-jose`) with a `role` claim; passwords hashed with `bcrypt` (cost 12).
- Role guards are FastAPI dependencies (`require_admin`, `require_operator`) applied per route.
- A default admin is seeded on first start so the API is immediately usable.

**For production I'd change:** the default `JWT_SECRET_KEY` and seeded admin password must come from secrets, never defaults; add refresh tokens and token revocation; rate-limit `/auth/login`.

## AI image extraction

Optional and fully isolated in `ai_extractor.py`. It only runs when the Azure OpenAI credentials (`AZURE_OPENAI_API_KEY` + `AZURE_OPENAI_ENDPOINT`) are set, imports the SDK lazily, and swallows all errors — verification never depends on it being available. Uses a vision-capable Azure OpenAI deployment with OpenAI structured outputs — the response is constrained to a JSON schema derived from the `DateExtraction` Pydantic model, so parsing is guaranteed rather than best-effort.

## Known limitations (called out deliberately)

- `BackgroundTasks` instead of a durable worker (see above).
- Booleans on some tables are stored as `'true'/'false'` strings for portability rather than a native boolean — a deliberate simplification I'd normalise with a proper boolean column + migration.
- No Alembic yet; tables are auto-created. Production needs migrations.
- Test coverage is a single end-to-end smoke test (`smoke_test.py`) rather than a unit suite — it proves the wiring works; I'd add unit tests per service/repository next.

## What I'd do next, in priority order

1. Unit tests per service and repository (the DI container makes this clean).
2. Alembic migrations + a real Postgres-first setup.
3. Replace `BackgroundTasks` with a RabbitMQ worker and conflict-aware bulk insert.
4. Move uploaded images to object storage.
5. Harden auth (secrets management, refresh/revocation, login rate limiting).
