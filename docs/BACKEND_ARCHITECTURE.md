# Backend Architecture

This document describes the backend components and how they interact.

## Runtime flow (high level)

1. `backend/main.py`
   - Loads configuration from `backend/config.py` (which reads `.env`).
   - Calls `init_db()` from `backend/database.py` to create tables if they do not exist.
   - Creates a FastAPI application, configures CORS, includes API router from `backend/routes.py`.
   - Serves frontend pages:
     - `/` serves `frontend/index.html`
     - `/dashboard` serves `frontend/dashboard.html`
     - `/static` mounts `frontend/static`.
2. Requests are handled by route handlers in `backend/routes.py`.
3. Route handlers use:
   - SQLAlchemy sessions from `backend/database.get_db()`
   - ORM entities from `backend/models.py`
   - Pydantic schemas from `backend/schemas.py`
4. Recommendation generation is performed by:
   - `backend/pipeline.CFRecipeRecommendationPipeline` (loads model pickle and scores candidates)
   - Pipeline invocation occurs inside `POST /api/recommendations`.

## Key design choices (as implemented)

- **FastAPI + APIRouter**
  - API endpoints are defined in one router with `prefix="/api"`.
- **SQLAlchemy ORM**
  - Models are declared in `backend/models.py`.
  - There are no explicit ORM relationship definitions; endpoints query each table directly.
- **Config-driven model loading**
  - `backend/config.py` defines `MODEL_FILENAME`, `MODEL_PATH`, and `PICKLE_PATH`.
  - `backend/pipeline.py` resolves the on-disk pickle path at runtime.
- **Pickle loading with `sys.path` adjustment**
  - `backend/pipeline.py` inserts the repo `cf/` directory into `sys.path` to support module resolution during pickle unpickling.

## Module responsibility mapping

- `backend/main.py`: app setup + static mounting.
- `backend/routes.py`: HTTP API contract + persistence (read/write ORM records).
- `backend/database.py`: engine/session/base/DDL init.
- `backend/models.py`: table schemas.
- `backend/schemas.py`: request/response payload shapes.
- `backend/pipeline.py`: ML model pickle loading + inference scoring.
- `backend/config.py`: env var sourcing.

