# Database Models (SQLAlchemy)

This document describes the SQLAlchemy ORM models in `backend/models.py`.

## ORM base and sessions

- `backend/database.py`
  - Defines `Base` and `engine` from `DATABASE_URL`.
  - Provides `get_db()` dependency which yields a SQLAlchemy `Session`.
  - `init_db()` calls `Base.metadata.create_all(bind=engine)`.

## Tables

### `User` (`users`)

- Purpose: simple local account record used by the current “auth-like” endpoints.
- Fields:
  - `id: String(64)` (primary key)
  - `username: String(255)` (unique, indexed)
  - `password_hash: String(255)`
  - `created_at`, `updated_at` timestamps.

### `Recipe` (`recipes`)

- Purpose: recipe catalogue with nutrition fields.
- Fields:
  - `id: Integer` (primary key)
  - `name: String(255)` (unique, indexed)
  - `description: Text | NULL`
  - `ingredients: JSON` (non-null)
  - Nutrition:
    - `calories`, `protein`, `carbs`, `fat`, `fiber`, `sodium` (all `Float | NULL`)
  - Metadata:
    - `difficulty: String(50) | NULL`
    - `cooking_time: Integer | NULL` (minutes)
    - `servings: Integer | NULL`
  - Timestamps: `created_at`, `updated_at`.

### `UserPreference` (`user_preferences`)

- Purpose: user dietary restrictions and numeric nutrition goals.
- Fields:
  - `id: Integer` (primary key)
  - `user_id: String(255)` (unique, indexed)
  - Restrictions:
    - `vegetarian`, `vegan`, `gluten_free`, `lactose_free` (Boolean, default False)
  - Goals:
    - `min_calories`, `max_calories`
    - `min_protein`, `max_protein`
    - `min_carbs`, `max_carbs`
    - `min_fat`, `max_fat`
    - All are `Float | NULL`
  - `allergies: JSON | NULL`
  - Timestamps.

### `Recommendation` (`recommendations`)

- Purpose: persisted recommendation outputs to support rating later.
- Fields:
  - `id: Integer` (primary key)
  - `user_id: String(255)`
  - `recipe_id: Integer`
  - `recipe_name: String(255)`
  - `score: Float` (recommendation score stored)
  - `reasoning: Text | NULL`
  - `is_rated: Boolean` (default False)
  - `user_rating: Float | NULL` (user-provided rating; UI implies 1–5)
  - timestamps.

### `ModelEvaluation` (`model_evaluations`)

- Purpose: store evaluation metrics for the recommendation model.
- Fields:
  - `id: Integer` (primary key)
  - `accuracy`, `precision`, `recall`, `f1_score` (Float | NULL)
  - `rmse`, `mae` (Float | NULL)
  - aggregate counters:
    - `total_recommendations`, `total_ratings`, `average_rating`
  - `evaluation_data: JSON | NULL`
  - timestamps.

## Relationship note

This codebase does not define explicit SQLAlchemy `relationship()` fields between models.
Instead, route handlers query by keys directly (e.g., selecting `Recipe` and `UserPreference` records independently).

