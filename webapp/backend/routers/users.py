from fastapi import APIRouter, Depends, HTTPException
from typing import List
import asyncpg
from webapp.backend.database import get_db
from webapp.backend.schemas.user import PersonaResponse, PersonaPreferences, UserHistoryResponse, UserHistoryRecipeItem

router = APIRouter(prefix="/users", tags=["Users"])

PERSONAS = [
    PersonaResponse(
        user_id=1533,
        display_name="Budi Santoso (Fitness Enthusiast)",
        bio="Fokus pada makanan berprotein tinggi dan rendah kalori untuk mendukung program defisit kalori dan pembentukan otot.",
        avatar_color="#10B981", # Emerald
        preferences=PersonaPreferences(max_calories=600.0, min_nutrition_score=75.0)
    ),
    PersonaResponse(
        user_id=1535,
        display_name="Siti Aminah (Sugar & Diabetes Prevention)",
        bio="Menghindari gula tinggi dan makanan olahan berat. Menyukai makanan sehat yang seimbang dengan nutrisi makro yang baik.",
        avatar_color="#3B82F6", # Blue
        preferences=PersonaPreferences(max_calories=800.0, min_nutrition_score=70.0)
    ),
    PersonaResponse(
        user_id=1581,
        display_name="Andi Wijaya (Keto Practitioner)",
        bio="Mencari makanan padat gizi untuk gaya hidup aktif. Fokus pada keseimbangan kesehatan secara menyeluruh.",
        avatar_color="#F59E0B", # Amber
        preferences=PersonaPreferences(max_calories=1000.0, min_nutrition_score=60.0)
    ),
    PersonaResponse(
        user_id=1634,
        display_name="Dewi Lestari (Weight Loss Journey)",
        bio="Menjalankan diet rendah kalori yang ketat dengan skor nutrisi makanan yang sangat tinggi untuk menjaga kebugaran tubuh.",
        avatar_color="#8B5CF6", # Purple
        preferences=PersonaPreferences(max_calories=400.0, min_nutrition_score=80.0)
    )
]

@router.get("/personas", response_model=List[PersonaResponse])
async def get_personas():
    """
    Get hardcoded personas with defined profile settings and healthy preferences.
    """
    return PERSONAS

@router.get("/{user_id}/history", response_model=UserHistoryResponse)
async def get_user_history(user_id: int, db: asyncpg.Connection = Depends(get_db)):
    """
    Fetch history of recipe interactions for a given user.
    """
    query = """
        SELECT i.recipe_id, r.name, i.rating, i.date
        FROM interactions i
        JOIN recipes r ON i.recipe_id = r.id
        WHERE i.user_id = $1
        ORDER BY i.date DESC, i.rating DESC;
    """
    rows = await db.fetch(query, user_id)
    
    recipes = []
    for row in rows:
        recipes.append(UserHistoryRecipeItem(
            recipe_id=row["recipe_id"],
            name=row["name"],
            rating=float(row["rating"]),
            date=str(row["date"]) if row["date"] else None
        ))
        
    return UserHistoryResponse(
        user_id=user_id,
        interaction_count=len(recipes),
        recipes=recipes
    )
