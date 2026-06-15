from fastapi import APIRouter, Depends, Request
from typing import List
import asyncpg
from webapp.backend.database import get_db
from webapp.backend.schemas.recommend import RecommendRequest, RecommendResponse, RecommendItem
from webapp.backend.pipeline.cascade import run_cascade
from webapp.backend.pipeline.nutrition import score_nutrition_candidates

router = APIRouter(prefix="/recommend", tags=["Recommendations"])

@router.post("", response_model=RecommendResponse)
async def get_recommendations(
    body: RecommendRequest,
    request: Request,
    db: asyncpg.Connection = Depends(get_db)
):
    """
    Generate recipe recommendations for a user.
    Uses hybrid cascade logic if user is registered in NCF model.
    Falls back to popular, high-nutrition recipes (cold-start) if user is new.
    """
    cf_artifacts = request.app.state.cf
    
    # 1. Check if user is in CF model (warm user) and within model index bounds
    is_warm = False
    if cf_artifacts and body.user_id in cf_artifacts.user2idx:
        u_idx = cf_artifacts.user2idx[body.user_id]
        # Verify the user index fits in the GMF embedding matrix size
        if u_idx < cf_artifacts.net.emb_u_gmf.num_embeddings:
            is_warm = True
    
    if is_warm:
        # --- HYBRID CASCADE PATHWAY ---
        # Fetch user's rating history to filter candidates and compute CBF similarity
        history_rows = await db.fetch("SELECT recipe_id FROM interactions WHERE user_id = $1;", body.user_id)
        past_recipe_ids = [r["recipe_id"] for r in history_rows]
        
        # Query candidates (all recipes from DB excluding their history)
        if past_recipe_ids:
            candidates = await db.fetch("SELECT * FROM recipes WHERE id != ANY($1);", past_recipe_ids)
        else:
            candidates = await db.fetch("SELECT * FROM recipes;")
            
        candidate_rows = [dict(c) for c in candidates]
        
        recommendations = run_cascade(
            app_state=request.app.state,
            user_id=body.user_id,
            past_recipe_ids=past_recipe_ids,
            candidate_rows=candidate_rows,
            min_nutrition_score=body.min_nutrition_score,
            max_calories=body.max_calories,
            top_n=body.top_n
        )
        
        return RecommendResponse(
            user_id=body.user_id,
            mode="hybrid",
            recommendations=[RecommendItem(**rec) for rec in recommendations]
        )
        
    else:
        # --- COLD START PATHWAY ---
        # Fetch popular recipes based on rating counts and averages
        popular_query = """
            SELECT r.id, r.name, r.minutes, r.tags, r.ingredients, 
                   r.n_steps, r.steps, r.description, r.nutrition, r.n_ingredients,
                   COALESCE(sub.cnt, 0) as interaction_count,
                   COALESCE(sub.avg_r, 0.0) as average_rating
            FROM recipes r
            LEFT JOIN (
                SELECT recipe_id, COUNT(*) as cnt, AVG(rating) as avg_r
                FROM interactions
                GROUP BY recipe_id
            ) sub ON r.id = sub.recipe_id
            ORDER BY interaction_count DESC, average_rating DESC
            LIMIT 100;
        """
        rows = await db.fetch(popular_query)
        candidate_rows = [dict(r) for r in rows]
        
        # Score candidates with NutritionScorer
        nutrition_scorer = request.app.state.nutrition
        scored_nutr = score_nutrition_candidates(nutrition_scorer, candidate_rows)
        nutr_score_map = {res["recipe_id"]: res["nutrition_score"] for res in scored_nutr}
        
        # Filter and process
        results = []
        for r in candidate_rows:
            rid = r["id"]
            nutr_score = nutr_score_map.get(rid, 50.0)
            
            # Apply nutrition filter if provided
            if body.min_nutrition_score is not None and nutr_score < body.min_nutrition_score:
                continue
                
            # Parse nutrition array to extract calories
            nutr_array = r.get("nutrition")
            calories = float(nutr_array[0]) if isinstance(nutr_array, list) and len(nutr_array) > 0 else 0.0
            
            # Apply calorie filter if provided
            if body.max_calories is not None and calories > body.max_calories:
                continue
                
            results.append({
                "recipe_id": rid,
                "name": r["name"],
                "minutes": r["minutes"],
                "tags": r["tags"] or [],
                "n_ingredients": r["n_ingredients"] or 0,
                "calories": calories,
                "nutrition_score": nutr_score,
                "cf_score": 0.0,
                "similarity_score": 0.0,
                "final_score": nutr_score / 100.0,
                "dominant_signal": "Nutrition"
            })
            
        # Sort by final score (i.e. healthiness) descending
        results.sort(key=lambda x: x["final_score"], reverse=True)
        top_results = results[:body.top_n]
        
        recommendations = []
        for rank, r in enumerate(top_results, 1):
            recommendations.append(RecommendItem(
                rank=rank,
                recipe_id=r["recipe_id"],
                name=r["name"],
                minutes=r["minutes"],
                tags=r["tags"],
                n_ingredients=r["n_ingredients"],
                calories=r["calories"],
                nutrition_score=r["nutrition_score"],
                cf_score=0.0,
                similarity_score=0.0,
                final_score=r["final_score"],
                dominant_signal="Nutrition"
            ))
            
        return RecommendResponse(
            user_id=body.user_id,
            mode="cold_start",
            recommendations=recommendations
        )
