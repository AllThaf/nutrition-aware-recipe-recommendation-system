from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class PersonaPreferences(BaseModel):
    max_calories: Optional[float] = None
    min_nutrition_score: Optional[float] = None

class PersonaResponse(BaseModel):
    user_id: int
    display_name: str
    bio: str
    avatar_color: str
    preferences: PersonaPreferences

class UserHistoryRecipeItem(BaseModel):
    recipe_id: int
    name: str
    rating: float
    date: Optional[str] = None

class UserHistoryResponse(BaseModel):
    user_id: int
    interaction_count: int
    recipes: List[UserHistoryRecipeItem]

class LoginRequest(BaseModel):
    user_id: int
    password: str

class LoginResponse(BaseModel):
    user_id: int
    display_name: str
    token: str

