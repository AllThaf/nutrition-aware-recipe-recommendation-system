from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Optional
import asyncpg
from webapp.backend.database import get_db
from webapp.backend.schemas.recipe import RecipeDetailResponse, RecipeNutritionDetails, RecipeSearchResponse, RecipePopularResponse
from webapp.backend.pipeline.nutrition import score_nutrition_candidates

router = APIRouter(prefix="/recipes", tags=["Recipes"])

@router.get("/search", response_model=List[RecipeSearchResponse])
async def search_recipes(
    request: Request,
    query: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: asyncpg.Connection = Depends(get_db)
):
    """
    Search recipes with optional text query (Postgres FTS) and tag filter.
    Calculates nutrition_score on the fly in batch.
    """
    sql = "SELECT id, name, minutes, tags, n_ingredients, nutrition FROM recipes"
    conditions = []
    params = []
    
    param_idx = 1
    if query:
        # Full-text search using GIN tsvector
        conditions.append(f"to_tsvector('english', name) @@ plainto_tsquery('english', ${param_idx})")
        params.append(query)
        param_idx += 1
        
    if tag:
        conditions.append(f"${param_idx} = ANY(tags)")
        params.append(tag)
        param_idx += 1
        
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
        
    sql += f" ORDER BY name LIMIT ${param_idx} OFFSET ${param_idx+1};"
    params.extend([limit, offset])
    
    rows = await db.fetch(sql, *params)
    recipes_list = [dict(r) for r in rows]
    
    if not recipes_list:
        return []
        
    # Calculate nutrition scores in a single batch
    nutrition_scorer = request.app.state.nutrition
    scored_items = [{"recipe_id": r["id"], "nutrition": r["nutrition"]} for r in recipes_list]
    scores = score_nutrition_candidates(nutrition_scorer, scored_items)
    scores_map = {item["recipe_id"]: item["nutrition_score"] for item in scores}
    
    results = []
    for r in recipes_list:
        nutr = r["nutrition"]
        calories = float(nutr[0]) if isinstance(nutr, list) and len(nutr) > 0 else 0.0
        
        results.append(RecipeSearchResponse(
            recipe_id=r["id"],
            name=r["name"],
            minutes=r["minutes"],
            tags=r["tags"] or [],
            n_ingredients=r["n_ingredients"] or 0,
            calories=calories,
            nutrition_score=scores_map.get(r["id"], 50.0)
        ))
        
    return results

@router.get("/popular", response_model=List[RecipePopularResponse])
async def get_popular_recipes(
    request: Request,
    limit: int = 20,
    db: asyncpg.Connection = Depends(get_db)
):
    """
    Get popular recipes based on interaction count and average rating.
    """
    query = """
        SELECT r.id, r.name, r.minutes, r.tags, r.n_ingredients, r.nutrition,
               COALESCE(sub.cnt, 0) as interaction_count,
               COALESCE(sub.avg_r, 0.0) as avg_rating
        FROM recipes r
        JOIN (
            SELECT recipe_id, COUNT(*) as cnt, AVG(rating) as avg_r
            FROM interactions
            GROUP BY recipe_id
        ) sub ON r.id = sub.recipe_id
        ORDER BY interaction_count DESC, avg_rating DESC
        LIMIT $1;
    """
    rows = await db.fetch(query, limit)
    recipes_list = [dict(r) for r in rows]
    
    if not recipes_list:
        return []
        
    # Calculate nutrition scores in a single batch
    nutrition_scorer = request.app.state.nutrition
    scored_items = [{"recipe_id": r["id"], "nutrition": r["nutrition"]} for r in recipes_list]
    scores = score_nutrition_candidates(nutrition_scorer, scored_items)
    scores_map = {item["recipe_id"]: item["nutrition_score"] for item in scores}
    
    results = []
    for r in recipes_list:
        nutr = r["nutrition"]
        calories = float(nutr[0]) if isinstance(nutr, list) and len(nutr) > 0 else 0.0
        
        results.append(RecipePopularResponse(
            recipe_id=r["id"],
            name=r["name"],
            minutes=r["minutes"],
            tags=r["tags"] or [],
            n_ingredients=r["n_ingredients"] or 0,
            calories=calories,
            nutrition_score=scores_map.get(r["id"], 50.0),
            interaction_count=r["interaction_count"],
            avg_rating=float(r["avg_rating"])
        ))
        
    return results

@router.get("/{recipe_id}", response_model=RecipeDetailResponse)
async def get_recipe_detail(recipe_id: int, request: Request, db: asyncpg.Connection = Depends(get_db)):
    """
    Get full details for a recipe, including calculated health score and parsed nutrition values.
    """
    row = await db.fetchrow("SELECT * FROM recipes WHERE id = $1;", recipe_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Recipe {recipe_id} not found")
        
    # Calculate nutrition score on-the-fly
    nutrition_scorer = request.app.state.nutrition
    recipe_dict = dict(row)
    
    # Calculate score
    scored = score_nutrition_candidates(
        nutrition_scorer, 
        [{"recipe_id": recipe_dict["id"], "nutrition": recipe_dict["nutrition"]}]
    )
    nutr_score = scored[0]["nutrition_score"] if scored else 50.0
    
    raw_nutr = recipe_dict["nutrition"]
    if isinstance(raw_nutr, list) and len(raw_nutr) >= 7:
        nutr_details = RecipeNutritionDetails(
            calories=float(raw_nutr[0]),
            total_fat_pdv=float(raw_nutr[1]),
            sugar_pdv=float(raw_nutr[2]),
            sodium_pdv=float(raw_nutr[3]),
            protein_pdv=float(raw_nutr[4]),
            saturated_fat_pdv=float(raw_nutr[5]),
            carbs_pdv=float(raw_nutr[6])
        )
    else:
        nutr_details = RecipeNutritionDetails(
            calories=0.0, total_fat_pdv=0.0, sugar_pdv=0.0, sodium_pdv=0.0,
            protein_pdv=0.0, saturated_fat_pdv=0.0, carbs_pdv=0.0
        )
        
    return RecipeDetailResponse(
        id=recipe_dict["id"],
        name=recipe_dict["name"],
        minutes=recipe_dict["minutes"],
        tags=recipe_dict["tags"] or [],
        ingredients=recipe_dict["ingredients"] or [],
        n_steps=recipe_dict["n_steps"] or 0,
        steps=recipe_dict["steps"] or [],
        description=recipe_dict["description"] or "",
        n_ingredients=recipe_dict["n_ingredients"] or 0,
        nutrition_raw=raw_nutr or [],
        nutrition=nutr_details,
        nutrition_score=nutr_score
    )
