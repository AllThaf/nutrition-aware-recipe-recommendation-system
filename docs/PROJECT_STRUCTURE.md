# Project Structure

This document explains the repository layout and the purpose of each top-level component.

## Top-level directories/files

- `backend/`
  - FastAPI backend (API + database models + ML inference pipeline integration).
- `frontend/`
  - Static HTML/CSS/JavaScript dashboard that talks to the backend REST API.
- `cf/`
  - Collaborative-filtering (CF) model code used to build/train CF wrappers.
  - Note: runtime inference loads **pickles** that may reference modules under `cf/models/*`.
- `models/`
  - Storage location for model artifacts (kept for compatibility with other training/inference workflows).
- `requirements.txt`
  - Python dependencies.
- `docker-compose.yml`, `Dockerfile.backend`
  - Containerized runtime for PostgreSQL + backend.
- `seed_db.py`
  - Seeds sample database data.
- `setup.sh`, `setup.bat`
  - Convenience scripts for local development.

## Backend package (`backend/`)

- `backend/main.py`
  - Creates the FastAPI app, configures CORS, initializes DB schema, and mounts frontend static assets.
- `backend/config.py`
  - Loads environment variables and centralizes runtime configuration (DB URL, CORS, server settings, model paths).
- `backend/database.py`
  - SQLAlchemy engine/session factory, ORM base, and DB initialization (`init_db`).
- `backend/models.py`
  - SQLAlchemy ORM models: `User`, `Recipe`, `UserPreference`, `Recommendation`, `ModelEvaluation`.
- `backend/schemas.py`
  - Pydantic request/response models for API payload validation.
- `backend/routes.py`
  - `APIRouter(prefix="/api")` defining all REST endpoints.
- `backend/pipeline.py`
  - `CFRecipeRecommendationPipeline`: loads the pickled CF wrapper model and scores recipe candidates.
- `backend/utils.py`
  - Utility helpers (currently includes response formatting and some unrelated utility functions).

## Frontend (`frontend/`)

- `frontend/index.html`
  - Landing/home page.
- `frontend/dashboard.html`
  - Main dashboard UI (multiple sections/tabs).
- `frontend/static/styles.css`
  - Styling.
- `frontend/static/dashboard.js`
  - Frontend logic: calls backend endpoints and renders charts.

## Deployment (Docker)

- `docker-compose.yml`
  - Starts PostgreSQL and the FastAPI backend container.
- `Dockerfile.backend`
  - Builds a slim Python image, installs `requirements.txt`, copies repo, and runs uvicorn.

