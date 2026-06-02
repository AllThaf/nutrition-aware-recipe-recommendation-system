# Technical Debt Report (Documentation-Only)

This document lists technical debt and documentation inaccuracies discovered during documentation review.

## 1) “Auth” endpoints vs actual authentication behavior

- `backend/routes.py` defines `/api/register` and `/api/login` and a set of `/api/me*` endpoints that use a header (`X-Username`).
- There is no JWT/session/token validation.

**Risk:** Documentation may incorrectly imply secure auth flows if not explicit.

**Recommendation (not implemented):** Clearly document that `/api/login` is demo-only and `/api/me*` uses `X-Username`.

## 2) ORM relationships are not defined

- `backend/models.py` defines models without SQLAlchemy `relationship()` fields.
- Queries are performed by table filtering in route handlers.

**Recommendation (not implemented):** Add relationship fields if desired for maintainability. (This might affect query patterns; therefore, not changed in this documentation-only task.)

## 3) Model pickle path configuration is non-trivial

- `backend/config.py` sets `MODEL_PATH` with logic that may override relative paths.
- `backend/pipeline.py` resolves paths based on:
  - absolute vs relative `MODEL_PATH`
  - `PICKLE_PATH`

**Risk:** Users can set `MODEL_PATH` incorrectly and face runtime errors.

**Recommendation (not implemented):** Document model path resolution rules explicitly and/or improve config clarity in a future change.

## 4) Inconsistent claims in root README/SETUP.md vs code

- The docs in `README.md`/`QUICKSTART.md` mention different endpoint counts and sometimes outdated component status.

**Recommendation (not implemented):** Keep this documentation set authoritative for the API and architecture, and treat root README statements as high-level overview.

## 5) Dependency list may include training/dev-only packages

- Current `requirements.txt` includes Jupyter, matplotlib/seaborn, pandas/sklearn, etc.
- The application runtime may only require a subset.

**Recommendation (not implemented):** In this task we update requirements to match runtime + model loading as closely as possible, and document any uncertainty.

