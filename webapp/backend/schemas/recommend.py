from pydantic import BaseModel, Field
from typing import List, Optional

class RecommendRequest(BaseModel):
    user_id: int
    top_n: int = Field(default=10, ge=5, le=20, description="Number of recommendations to return")
    min_nutrition_score: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Minimum health score threshold")
    max_calories: Optional[float] = Field(default=None, ge=0.0, description="Maximum calorie threshold")

class RecommendItem(BaseModel):
    rank: int
    recipe_id: int
    name: str
    minutes: int
    tags: List[str]
    n_ingredients: int
    calories: float
    nutrition_score: float
    cf_score: float
    similarity_score: float
    final_score: float
    dominant_signal: str = Field(description="Dominant signal: 'CF', 'CBF', or 'Nutrition'")

class RecommendResponse(BaseModel):
    user_id: int
    mode: str = Field(description="Recommendation mode: 'hybrid' or 'cold_start'")
    recommendations: List[RecommendItem]
