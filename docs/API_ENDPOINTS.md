# API Endpoints

This document enumerates the REST endpoints implemented in `backend/routes.py`.

## Base URL and conventions

- API router prefix: `/api`
- Frontend is served from the same FastAPI application, so API is typically called as:
  - `http://localhost:8000/api/...`
- Payloads are validated with Pydantic schemas from `backend/schemas.py`.

## Authentication / user context (current behavior)

Despite the presence of `POST /api/register` and `POST /api/login`, the current “logged-in user” context is implemented via an HTTP header:

- Endpoints `/api/me*` expect header:
  - `X-Username: <username>`

The `/api/login` endpoint returns a simple response (no JWT/sessions). The actual user selection for `/api/me*` uses the header.

> Documentation note: the routes file includes “Auth (simple account system)” functions, but it does not implement JWT/session authentication.

## Recipes

1. `GET /api/recipes`
   - Query params:
     - `skip: int = 0`
     - `limit: int = 100`
   - Response: list of recipes.

2. `GET /api/recipes/{recipe_id}`
   - Response: single recipe.
   - Errors:
     - `404` if not found.

3. `POST /api/recipes`
   - Body: `RecipeCreate` (name, ingredients, optional nutrition and metadata fields)
   - Behavior:
     - Rejects if a recipe with the same `name` already exists.

## Registration / Login (simple demo)

1. `POST /api/register`
   - Body: `{ "username": string, "password": string }`
   - Response: `{ "user_id": string, "username": string }`
   - Behavior:
     - Stores `sha256` password hash in `users.password_hash`.

2. `POST /api/login`
   - Body: `{ "username": string, "password": string }`
   - Response: `{ "user_id": string, "username": string }`
   - Errors:
     - `401` for invalid username/password.

## Current user (“me”) and preferences

### Current user profile
- `GET /api/me`
  - Header: `X-Username`
  - Response: `UserProfile` (`id`, `username`)

### Current user preferences
1. `GET /api/me/preferences`
   - Header: `X-Username`
   - Response: `UserPreference`
   - Errors:
     - `404` if no preferences exist for the user.

2. `POST /api/me/preferences`
   - Header: `X-Username`
   - Body: `UserPreferenceBase` (dietary + goal fields)
   - Behavior: upsert (create if absent; otherwise update fields).

### Preferences by explicit user_id (backward-compatible)
1. `GET /api/users/{user_id}/preferences`
2. `POST /api/users/{user_id}/preferences`

These endpoints do not use `X-Username`; they look up by `user_id` path parameter.

## Recommendations

### Generate recommendations
- `POST /api/recommendations`
  - Body: `GetRecommendationsRequest`
    - `user_id: string`
    - `num_recommendations: int = 5`
  - Behavior (implementation detail):
    1. Loads `UserPreference` for `user_id`.
    2. Loads all `Recipe` records.
    3. Instantiates `CFRecipeRecommendationPipeline` using `MODEL_PATH`, `MODEL_FILENAME`, `PICKLE_PATH`.
    4. Calls `pipeline.get_top_recommendations(...)`.
    5. Persists each generated recommendation into `recommendations` table so rating can be recorded.

### Rate a recommendation
- `POST /api/recommendations/{recommendation_id}/rate`
  - Body: `RecommendationUpdate` (`user_rating`)
  - Behavior:
    - Sets `is_rated=True` and `user_rating`.
    - Returns a message and the updated recommendation.

## Model evaluation

1. `GET /api/evaluation/metrics`
   - Returns the most recently created `ModelEvaluation` record.

2. `POST /api/evaluation/metrics`
   - Body: `ModelEvaluationBase`.
   - Inserts a new record.

3. `GET /api/evaluation/recommendations-by-user`
   - Returns:
     - `total_recommendations`, `total_rated`, `unique_users`, `average_rating`, `rating_percentage`

## Utility endpoints

- `GET /api/health`
  - Returns `{ status: "healthy", message: "API is running" }`

- `GET /api/info`
  - Returns API metadata (title/description/version/status).

