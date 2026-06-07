# Product Verification System — Backend

A FastAPI-based warehouse product verification system supporting bulk CSV ingestion, on-floor product validation with image capture, optional AI-assisted expiry extraction, and role-based reporting.

> **About this submission.** The service runs out of the box with **zero external dependencies** — it uses a local SQLite database and an in-process message queue so it can be evaluated with a single `pip install` and `python run.py`. The codebase is also written against a production target (PostgreSQL + RabbitMQ): if a `DATABASE_URL` pointing at Postgres is configured but unreachable, the app automatically falls back to the local database. The [Target architecture](#target-architecture-production) section describes how this would be deployed for real, and [Implementation status](#implementation-status) maps exactly what is built vs. what is described as the target.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Overview](#overview)
- [Implementation status](#implementation-status)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Architecture Decisions](#architecture-decisions)
- [Data Schema](#data-schema)
- [API Endpoints](#api-endpoints)
- [Role-Based Access Control](#role-based-access-control)
- [AI Image Analysis](#ai-image-analysis)
- [Configuration](#configuration)
- [Code Quality](#code-quality)
- [Target architecture (production)](#target-architecture-production)

---

## Quick Start

Requires Python 3.11+.

```bash
pip install -r requirements.txt
python run.py
```

Then open the interactive API docs at **http://localhost:8000/docs**.

On first start the app creates its local database, all tables, and a default admin account:

```
username: admin
password: admin12345
```

A typical run-through:

1. `POST /auth/login` with the admin credentials to get a JWT.
2. `POST /products/upload` with a CSV (`wid,ean,manufacturing_date,expiry_date`) — returns a `job_id`.
3. `GET /products/upload/{job_id}/status` to watch ingestion progress.
4. `POST /verify` with a `wid` to look up a product and log a verification event.
5. `GET /reports` / `GET /reports/export` for verification reporting.

A runnable end-to-end check of all of the above lives in [`smoke_test.py`](smoke_test.py).

---

## Overview

The system serves three user personas:

| Persona | Role | Capabilities |
|---|---|---|
| Warehouse Manager | `admin` | Upload CSV files, view/export reports, manage users |
| Warehouse Operator | `operator` | Verify products on the floor, capture images |
| QA Manager | `qa_manager` | Reserved role for reporting workflows |

Core flows:

1. **Bulk ingestion** — an admin uploads a CSV. The request returns immediately with a `job_id`; rows are ingested in the background in chunks, and progress is published as events.
2. **On-floor verification** — an operator submits a WID, optionally uploads a photo, and the system returns the product details for visual comparison while logging the verification event.
3. **Reporting** — an admin selects a date range and retrieves verification events, with CSV export.

---

## Implementation status

This is the honest map of what is built in this repository vs. what is described as the production target.

| Concern | This submission (as-built) | Target (production) |
|---|---|---|
| Database | SQLite (local file, auto-created) | PostgreSQL 16 + asyncpg |
| Connection | Automatic fallback to SQLite if the configured DB is unreachable | Pooled async connections to Postgres |
| Schema management | Tables auto-created on startup (`Base.metadata.create_all`) | Alembic migrations |
| Messaging | In-process async queue (`src/mq_messaging/connection.py`) | RabbitMQ via `aio-pika` |
| Background processing | FastAPI `BackgroundTasks` (same process) | Dedicated worker process consuming the queue |
| Bulk insert | Per-row ORM insert with duplicate-WID guard | `INSERT ... ON CONFLICT` / `COPY` |
| AI extraction | Optional; no-op unless Azure OpenAI credentials are set | Always-on Azure OpenAI Vision |

Everything in the "as-built" column is wired, runs, and is exercised by the smoke test. The "target" column reflects design intent and is the direction the code is structured to grow toward (e.g. the messaging layer is isolated behind a publisher so swapping the in-process queue for RabbitMQ touches one module).

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| Database | SQLite (shipped) / PostgreSQL 16 (target) |
| Dependency injection | `dependency-injector` |
| Messaging | In-process queue (shipped) / RabbitMQ (target) |
| Auth | JWT (`python-jose`) + `bcrypt` |
| AI image analysis | Azure OpenAI Vision (optional) |
| Python version | 3.11+ |

---

## Project Structure

The codebase is organised by responsibility — each folder is one layer:

```
src/
├── access_control/   # JWT, password hashing, role-based route guards
├── models/           # ORM entities + Pydantic request/response/read schemas
├── repositories/     # Data access — the only layer that touches the database
├── services/         # Business logic
├── mappers/          # entity <-> model <-> response conversions
├── mq_messaging/     # Publisher abstraction + in-process message queue
├── routes/           # FastAPI routers (auth, products, verification, reports)
├── utils/            # CSV parsing, image handling, AI extraction
├── config.py         # Settings (env-driven)
├── database.py       # Engine/session management + fallback logic
├── container.py      # dependency-injector wiring (singletons + factories)
└── app.py            # App factory, lifespan, router registration
```

Top level: `run.py` (start the server), `schema.sql` (PostgreSQL DDL), `smoke_test.py` (end-to-end check), `requirements.txt` / `requirements-dev.txt`, `.env.example`.

---

## Architecture Decisions

### Layered design
Routes depend on services, services depend on repositories, repositories own all database access. Mappers translate between ORM entities, internal models, and API response schemas so the database shape never leaks directly into the API contract.

### Dependency injection (`container.py`)
[`container.py`](src/container.py) uses `dependency-injector` to centralise wiring:
- **Singletons** for application-lifetime resources (the database manager, the message queue, the upload-progress publisher).
- **Factories** for per-request services, each bound to the request's database session (`container.user_service(session)`).

Routes never construct a service directly, and any provider can be overridden in a test.

### Async SQLAlchemy
All database access uses `AsyncSession`, keeping the event loop free during I/O. The same code path runs on SQLite (`aiosqlite`) locally and PostgreSQL (`asyncpg`) in production.

### Database fallback
[`database.py`](src/database.py) attempts the configured `DATABASE_URL` first; if the connection fails (e.g. Postgres is not running), it logs the reason and falls back to a local SQLite database so the service always starts.

### Background ingestion
The upload endpoint validates and parses the CSV, creates an `UploadJob`, and returns a `job_id` immediately. Ingestion then runs in the background in chunks, updating job progress and publishing progress events after each chunk. The client polls the status endpoint. (Shipped via `BackgroundTasks`; in production this becomes a separate worker consuming RabbitMQ — see [Implementation status](#implementation-status).)

### RBAC
JWT tokens carry a `role` claim. Dependencies in [`access_control/dependencies.py`](src/access_control/dependencies.py) enforce role requirements per route.

---

## Data Schema

The full schema — every table and index — is defined in [`schema.sql`](schema.sql), which mirrors the ORM entities in `src/models/db_entities/`. The application also auto-creates these tables on startup, so the script is only needed when provisioning a PostgreSQL database up front:

```bash
psql "$DATABASE_URL" -f schema.sql
```

Four tables: `users`, `products`, `upload_jobs`, and `verification_logs` (which references `products` and `users`). IDs are application-generated UUID strings.

---

## API Endpoints

| Method | Path | Role | Description |
|---|---|---|---|
| GET | `/health` | public | Liveness check |
| POST | `/auth/login` | public | Returns a JWT access token |
| POST | `/auth/register` | admin | Create a new user with a role |
| POST | `/products/upload` | admin | Upload a CSV, returns a `job_id` (202) |
| GET | `/products/upload/{job_id}/status` | admin | Poll upload job progress |
| GET | `/products` | admin | List ingested products |
| POST | `/verify` | operator, admin | Look up a WID and log a verification event |
| POST | `/verify/image` | operator, admin | Attach an image to a verification log (+ optional AI extraction) |
| GET | `/reports` | admin | Paginated verification events by date range |
| GET | `/reports/export` | admin | Download verification events as CSV |

---

## Role-Based Access Control

| Feature | admin | operator |
|---|---|---|
| Upload CSV / check job status | ✅ | ❌ |
| List products | ✅ | ❌ |
| Verify product (WID lookup) | ✅ | ✅ |
| Attach verification image | ✅ | ✅ |
| View / export reports | ✅ | ❌ |
| Register new users | ✅ | ❌ |

---

## AI Image Analysis

When an image is submitted to `POST /verify/image`, [`ai_extractor.py`](src/utils/ai_extractor.py) can send it to the Azure OpenAI Vision API to extract manufacturing/expiry dates. The model is called with **structured outputs** (a JSON schema derived from the `DateExtraction` Pydantic model), so the response is guaranteed to match the expected shape. This is **opt-in**: it only runs if the Azure OpenAI credentials are configured, and any failure is swallowed so verification never depends on it. Extracted values are stored on the verification log.

---

## Configuration

All settings have working defaults; a `.env` file is optional. See [`.env.example`](.env.example).

```
# Database — omit to use the local SQLite database.
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/product_verification

# JWT
JWT_SECRET_KEY=change-me-in-production
JWT_EXPIRATION_HOURS=24

# Azure OpenAI (optional — enables AI image date extraction when set)
# AZURE_OPENAI_API_KEY=...
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_OPENAI_API_VERSION=2024-08-01-preview  # required for structured outputs
# GPT_DEPLOYMENT=gpt-4o

# App
DEBUG=False
UPLOAD_DIR=uploads
```

---

## Code Quality

The codebase is formatted and linted with a standard toolchain (config in [`pyproject.toml`](pyproject.toml) and [`.flake8`](.flake8)):

| Tool | Purpose |
|---|---|
| **black** | Opinionated code formatting |
| **isort** | Import ordering |
| **flake8** | Style + error linting |
| **pylint** | Deeper static analysis |
| **vulture** | Dead-code detection |

Install the tooling and run it with:

```bash
pip install -r requirements-dev.txt

isort src && black src        # auto-format
flake8 src                    # lint
pylint src                    # static analysis
vulture src                   # dead code
```

The shipped code passes `black --check`, `isort --check`, and `flake8` cleanly.

---

## Target architecture (production)

The repository runs standalone, but the code is organised to scale to a production deployment:

- **PostgreSQL** as the primary store, with Alembic managing migrations instead of `create_all`. The async engine and pooling are already in place.
- **RabbitMQ** for messaging: the publisher abstraction in `src/mq_messaging/` would publish to a durable topic exchange, and a **separate worker process** would consume upload jobs and perform chunked, conflict-aware bulk inserts (`INSERT ... ON CONFLICT DO NOTHING`).
- **Object storage** for verification images instead of local disk.
- **Horizontal scaling** of the API behind a load balancer, with the worker scaled independently.

Because messaging, persistence, and background work are each isolated behind their own module, moving from the shipped local mode to this target is a matter of swapping implementations rather than restructuring the application.
