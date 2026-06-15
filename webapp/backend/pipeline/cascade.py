import numpy as np
from typing import List, Dict, Any
from webapp.backend.pipeline.cf import score_cf_candidates
from webapp.backend.pipeline.cbf import score_cbf_candidates
from webapp.backend.pipeline.nutrition import score_nutrition_candidates

def run_cascade(
    app_state,
    user_id: int,
    past_recipe_ids: List[int],
    candidate_rows: List[Dict[str, Any]],
    min_nutrition_score: float = None,
    max_calories: float = None,
    top_n: int = 10,
    nutrition_weight: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Run multi-stage cascading hybrid recommendation:
    Stage 0: Filter candidates BEFORE ranking based on strict criteria (Calorie & Nutrition constraints)
    Stage 1: NCF (CF) scoring -> Keep top 100 candidates
    Stage 2: CBF Max-Pooling similarity scoring -> Keep top 30 candidates
    Stage 3: Nutrition scoring & blending and final ranking -> Top N
    """
    if not candidate_rows:
        return []

    # --- STAGE 0: Pre-filtering (Filter First) ---
    # 1. Filter by calories (first element of nutrition array)
    if max_calories is not None:
        filtered_candidates = []
        for row in candidate_rows:
            nutr = row.get("nutrition")
            if isinstance(nutr, list) and len(nutr) > 0:
                calories = float(nutr[0])
            else:
                calories = 0.0
            row["calories"] = calories
            if calories <= max_calories:
                filtered_candidates.append(row)
        candidate_rows = filtered_candidates
    else:
        # Pre-populate calories for later stage
        for row in candidate_rows:
            nutr = row.get("nutrition")
            if isinstance(nutr, list) and len(nutr) > 0:
                row["calories"] = float(nutr[0])
            else:
                row["calories"] = 0.0

    # 2. Filter by minimum nutrition score
    if min_nutrition_score is not None:
        nutrition_scorer = app_state.nutrition
        nutrition_results = score_nutrition_candidates(nutrition_scorer, candidate_rows)
        nutrition_score_map = {res["recipe_id"]: res["nutrition_score"] for res in nutrition_results}
        
        filtered_candidates = []
        for row in candidate_rows:
            rid = row["id"]
            nutr_score = nutrition_score_map.get(rid, 50.0)
            row["nutrition_score"] = nutr_score
            if nutr_score >= min_nutrition_score:
                filtered_candidates.append(row)
        candidate_rows = filtered_candidates

    if not candidate_rows:
        return []

    # --- STAGE 1: Collaborative Filtering ---
    # Score all remaining candidates using CF
    cf_artifacts = app_state.cf
    
    candidate_recipe_ids = [r["id"] for r in candidate_rows]
    try:
        cf_results = score_cf_candidates(
            cf_artifacts.net,
            cf_artifacts.user2idx,
            cf_artifacts.item2idx,
            user_id,
            candidate_recipe_ids
        )
        cf_score_map = {res["recipe_id"]: res["cf_score"] for res in cf_results}
    except KeyError:
        cf_score_map = {rid: 0.0 for rid in candidate_recipe_ids}

    for row in candidate_rows:
        row["cf_score"] = cf_score_map.get(row["id"], 0.0)

    # Sort by CF score and keep top 100 candidates
    candidate_rows.sort(key=lambda x: x["cf_score"], reverse=True)
    stage1_candidates = candidate_rows[:100]

    # --- STAGE 2: Content-Based Filtering ---
    # Score remaining candidates using TF-IDF similarity to past history
    cbf_artifacts = app_state.cbf
    stage1_recipe_ids = [r["id"] for r in stage1_candidates]
    
    cbf_results = score_cbf_candidates(cbf_artifacts, stage1_recipe_ids, past_recipe_ids)
    cbf_score_map = {res["recipe_id"]: res["similarity_score"] for res in cbf_results}

    for row in stage1_candidates:
        row["similarity_score"] = cbf_score_map.get(row["id"], 0.0)

    # Sort by CBF similarity and keep top 30 candidates
    stage1_candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
    stage2_candidates = stage1_candidates[:30]

    # --- STAGE 3: Nutrition Scoring & Blending ---
    # Ensure nutrition score is populated for stage2 candidates
    if min_nutrition_score is None:
        nutrition_scorer = app_state.nutrition
        nutrition_results = score_nutrition_candidates(nutrition_scorer, stage2_candidates)
        nutrition_score_map = {res["recipe_id"]: res["nutrition_score"] for res in nutrition_results}
        for row in stage2_candidates:
            row["nutrition_score"] = nutrition_score_map.get(row["id"], 50.0)

    final_candidates = []
    for row in stage2_candidates:
        sim_score = row["similarity_score"]
        nutr_score = row["nutrition_score"]
        norm_nutr = nutr_score / 100.0
        row["final_score"] = (1 - nutrition_weight) * sim_score + nutrition_weight * norm_nutr
        
        # Heuristic to determine dominant signal for explanation
        if nutr_score >= 80 and row["final_score"] - sim_score * (1 - nutrition_weight) > 0.15:
            row["dominant_signal"] = "Nutrition"
        elif sim_score > 0.1:
            row["dominant_signal"] = "CBF"
        else:
            row["dominant_signal"] = "CF"
            
        final_candidates.append(row)

    # Sort by final score descending and select top N
    final_candidates.sort(key=lambda x: x["final_score"], reverse=True)
    results = final_candidates[:top_n]
    
    # Format output
    output_recommendations = []
    for rank, r in enumerate(results, 1):
        output_recommendations.append({
            "rank": rank,
            "recipe_id": r["id"],
            "name": r["name"],
            "minutes": r["minutes"],
            "tags": r["tags"],
            "n_ingredients": r["n_ingredients"],
            "calories": r["calories"],
            "nutrition_score": r["nutrition_score"],
            "cf_score": r["cf_score"],
            "similarity_score": r["similarity_score"],
            "final_score": r["final_score"],
            "dominant_signal": r["dominant_signal"]
        })
        
    return output_recommendations
