from pydantic import BaseModel
from typing import List, Dict

class RecipeNutritionDetails(BaseModel):
    calories: float
    total_fat_pdv: float
    sugar_pdv: float
    sodium_pdv: float
    protein_pdv: float
    saturated_fat_pdv: float
    carbs_pdv: float

class RecipeDetailResponse(BaseModel):
    id: int
    name: str
    minutes: int
    tags: List[str]
    ingredients: List[str]
    n_steps: int
    steps: List[str]
    description: str
    n_ingredients: int
    nutrition_raw: List[float]
    nutrition: RecipeNutritionDetails
    nutrition_score: float

class RecipeSearchResponse(BaseModel):
    recipe_id: int
    name: str
    minutes: int
    tags: List[str]
    n_ingredients: int
    calories: float
    nutrition_score: float

class RecipePopularResponse(BaseModel):
    recipe_id: int
    name: str
    minutes: int
    tags: List[str]
    n_ingredients: int
    calories: float
    nutrition_score: float
    interaction_count: int
    avg_rating: float

