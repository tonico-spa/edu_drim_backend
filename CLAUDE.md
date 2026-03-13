# EDU_DRIM Backend — Claude Instructions

## What this service is

FastAPI backend for EDU_DRIM, an educational platform for teachers. It handles auth, quiz submission with tag-based course matching, a Sanity-backed class/course catalog, and teacher-assembled custom courses stored in PostgreSQL.

---

## Stack

- **Python 3.12+**, managed with `uv` — no `requirements.txt`, use `pyproject.toml`
- **FastAPI 0.111** — all routers, one file per resource
- **SQLAlchemy 2** — ORM only, no raw SQL in routers
- **PostgreSQL** — primary data store, migrations via Alembic
- **Alembic 1.13** — always autogenerate migrations after model changes
- **python-jose** — JWT signing/verification (HS256)
- **passlib + bcrypt** — password hashing (12 rounds)
- **httpx** — sync HTTP client for Sanity GROQ API calls
- **pydantic v2** — request/response schemas

---

## Running locally

```bash
# Install deps
uv sync

# Copy and fill env
cp .env.example .env

# Apply migrations
uv run alembic upgrade head

# Seed data (quiz questions, tags, etc.)
uv run python seed.py

# Run dev server
uv run uvicorn main:app --reload
```

Server runs on **port 8000**. Docs at `http://localhost:8000/docs`.

---

## Project layout

```
edu_drim_backend/
├── main.py              # App factory, CORS, router registration
├── database.py          # SQLAlchemy engine, SessionLocal, Base, get_db()
├── dependencies.py      # get_current_teacher() — JWT auth dependency
├── models/
│   ├── teacher.py       # Teacher
│   ├── class_.py        # Class, ClassTag, LevelEnum
│   ├── course.py        # CatalogCourse*, TeacherCourse, TeacherCourseClass
│   ├── quiz.py          # QuizQuestion, QuizOption, QuizOptionTagWeight
│   └── tag.py           # Tag
├── schemas/             # Pydantic v2 schemas (separate from ORM models)
│   ├── teacher.py       # TeacherRegister, TeacherLogin, TeacherOut, TokenOut, ForgotPasswordRequest, ResetPasswordRequest
│   ├── course.py        # TeacherCourseCreate, TeacherCourseUpdate, TeacherCourseOut
│   ├── quiz.py          # QuestionOut, QuizSubmit
│   └── class_.py
├── routers/             # One file per resource
│   ├── auth.py
│   ├── quiz.py
│   ├── classes.py
│   ├── courses.py
│   ├── teacher_courses.py
│   └── webhooks.py
├── services/
│   ├── sanity.py        # All GROQ queries to Sanity CDN
│   └── tag_matcher.py   # Quiz answer → tag score computation
└── alembic/             # Migration scripts
```

---

## API surface

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/register` | No | Create teacher, returns JWT |
| POST | `/api/auth/login` | No | Returns JWT |
| POST | `/api/auth/forgot-password` | No | Always 200 (anti-enum) — TODO: send email |
| POST | `/api/auth/reset-password` | No | Validates JWT reset token, updates password |
| GET | `/api/quiz/questions` | No | All questions ordered by `order` field, with options |
| POST | `/api/quiz/submit` | No | `{ answers: {question_id: option_id} }` → `{ tags, resource }` |
| GET | `/api/classes` | No | Query params: `?tags=tag1,tag2&resource=computador` — returns Sanity classes sorted by `match_pct` |
| GET | `/api/classes/{class_id}` | No | Single class by Sanity `_id` |
| GET | `/api/courses` | No | Query param: `?tags=tag1,tag2` — returns Sanity courses sorted by `match_pct` |
| GET | `/api/courses/{course_id}` | No | Single course by Sanity `_id` |
| GET | `/api/teacher/courses` | **JWT** | List teacher's custom courses |
| GET | `/api/teacher/courses/{id}` | **JWT** | Single teacher course |
| POST | `/api/teacher/courses` | **JWT** | Create custom course with ordered class IDs |
| PUT | `/api/teacher/courses/{id}` | **JWT** | Update title/description/class order (full rewrite of classes) |
| DELETE | `/api/teacher/courses/{id}` | **JWT** | Delete teacher course |
| POST | `/api/webhooks/sanity` | HMAC sig | Upsert or deactivate class from Sanity publish event |
| POST | `/api/webhooks/sanity/sync/{sanity_id}` | No | Manual re-sync trigger (placeholder) |
| GET | `/health` | No | `{ "status": "ok" }` |

---

## Auth

- JWT stored and sent as `Authorization: Bearer <token>` by the frontend
- Token payload: `{ sub: teacher_id (UUID str), name, exp }`
- Expiry: 24 hours
- All protected routes use `Depends(get_current_teacher)` from `dependencies.py`
- `SECRET_KEY` defaults to `"dev_secret"` in dev — always set `JWT_SECRET` in prod

---

## Tag matching logic (`services/tag_matcher.py`)

1. Quiz answers are `{ question_id: option_id }` dicts
2. `compute_tags()` looks up `QuizOptionTagWeight` rows for each selected option
3. Accumulates weighted scores per tag across all answers
4. Tags with `score >= threshold` (default: 2) become **topic tags**
5. Special resource tags (`sin_tecnologia`, `computador`, `computador_internet`) are separated — the one with the highest score becomes the **resource** filter
6. Returns `(topic_tags: list[str], resource: str | None)`
7. These are passed to `/api/classes?tags=...&resource=...` and `/api/courses?tags=...` by the frontend

---

## Sanity integration (`services/sanity.py`)

- All class and course **reads** go directly to Sanity via GROQ (not from PostgreSQL)
- Uses `httpx.get()` synchronously — timeout 10s
- Sanity URL: `https://{SANITY_PROJECT_ID}.api.sanity.io/v2024-01-01/data/query/{SANITY_DATASET}?query=...`
- `fetch_classes(tag_names, resource)` — filters and projects class documents
- `fetch_class_by_sanity_id(sanity_id)` — single class with `materials` field included
- `fetch_courses(tag_names)` — catalog courses with nested classes
- `fetch_course_by_id(sanity_id)` — single course with nested classes

**Webhook flow (writes to PostgreSQL):**
```
Sanity publish → POST /api/webhooks/sanity
  payload._type == "class"         → _upsert_class() in PostgreSQL
  payload._type == "sanity.deleteEvent" → _deactivate_class() (sets is_active=False)
```
- Signature: HMAC-SHA256 of raw body with `SANITY_WEBHOOK_SECRET`, compared against `sanity-webhook-signature` header
- If `SANITY_WEBHOOK_SECRET` is not set, signature check is skipped (local dev)

---

## Database conventions

- **All PKs are UUIDs** (`uuid.uuid4()`, PostgreSQL `UUID` type)
- **Soft deletes for classes** — never `DELETE` a class row; set `is_active = False` on Sanity delete events
- **`TeacherCourseClass.order`** — always delete all rows and rewrite the full ordered list on PUT (never patch individual rows)
- **`TeacherCourseClass.class_id`** is a `String` (Sanity document `_id`), not a FK to `classes`
- **`Class.sanity_id`** — unique, indexed; used for webhook upserts

---

## Migrations

```bash
# After any model change
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head

# Rollback one step
uv run alembic downgrade -1
```

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://edudrim:edudrim@localhost:5432/edudrim` | PostgreSQL connection |
| `JWT_SECRET` | `dev_secret` | JWT signing key |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins |
| `SANITY_WEBHOOK_SECRET` | `""` | HMAC secret — if empty, sig check is skipped |
| `SANITY_PROJECT_ID` | `""` | Sanity project ID for GROQ queries |
| `SANITY_DATASET` | `production` | Sanity dataset |

---

## Key conventions

- **No raw SQL** — use SQLAlchemy ORM everywhere in routers
- **Business logic in `services/`** — routers should be thin
- **Schemas in `schemas/`** — never use ORM models directly as response types
- **`Depends(get_current_teacher)`** on every protected endpoint — never roll your own auth check in a router
- **`match_pct`** is computed in routers (`classes.py`, `courses.py`), not in Sanity or the DB
- The `forgot-password` endpoint always returns 200 regardless of whether the email exists (prevents user enumeration)
- Email sending in `forgot-password` is a **TODO** — the reset token is generated but not sent

---

## Known gaps / future work

- `POST /api/auth/forgot-password` — email sending not implemented (TODO in `routers/auth.py`)
- `POST /api/webhooks/sanity/sync/{sanity_id}` — manual sync is a placeholder (no actual GROQ fetch)
- `DELETE /api/teacher/me` — account deletion not implemented
- Pagination exists in the DB layer but no endpoints expose `page`/`limit` params yet
