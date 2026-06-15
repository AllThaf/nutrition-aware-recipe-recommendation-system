import pandas as pd
from typing import List, Dict, Any

def score_nutrition_candidates(nutrition_scorer, candidate_recipes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Score candidate recipes using the NutritionScorer.
    Expects candidate_recipes to be a list of dicts, where each dict has:
      - 'recipe_id'
      - 'nutrition' (list of float values: [calories, total_fat_pdv, sugar_pdv, sodium_pdv, protein_pdv, sat_fat_pdv, carbs_pdv])
    """
    if not candidate_recipes:
        return []
        
    data = []
    for r in candidate_recipes:
        rid = r.get("recipe_id") or r.get("id")
        nutr = r.get("nutrition")
        
        # If it is a string representation of a list, parse it
        if isinstance(nutr, str):
            import ast
            try:
                nutr = ast.literal_eval(nutr)
            except Exception:
                nutr = None
                
        if isinstance(nutr, list) and len(nutr) >= 7:
            data.append({
                "recipe_id": rid,
                "calories": float(nutr[0]),
                "total_fat_pdv": float(nutr[1]),
                "sugar_pdv": float(nutr[2]),
                "sodium_pdv": float(nutr[3]),
                "protein_pdv": float(nutr[4]),
                "sat_fat_pdv": float(nutr[5]),
                "carbs_pdv": float(nutr[6]),
                "saturated_fat_pdv": float(nutr[5]) # map both to support scoring.py thresholds
            })
        else:
            data.append({
                "recipe_id": rid,
                "calories": 0.0,
                "total_fat_pdv": 0.0,
                "sugar_pdv": 0.0,
                "sodium_pdv": 0.0,
                "protein_pdv": 0.0,
                "sat_fat_pdv": 0.0,
                "carbs_pdv": 0.0,
                "saturated_fat_pdv": 0.0
            })
            
    df = pd.DataFrame(data)
    df_scored = nutrition_scorer.calculate_score(df)
    
    scores_dict = df_scored.set_index("recipe_id")["nutrition_score"].to_dict()
    
    return [
        {"recipe_id": r.get("recipe_id") or r.get("id"), "nutrition_score": float(scores_dict.get(r.get("recipe_id") or r.get("id"), 50.0))}
        for r in candidate_recipes
    ]
