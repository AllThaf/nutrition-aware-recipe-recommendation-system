from fastapi import APIRouter, Depends, HTTPException
import asyncpg
from datetime import date
from webapp.backend.database import get_db
from webapp.backend.schemas.interaction import InteractionRequest, InteractionResponse

router = APIRouter(prefix="/interactions", tags=["Interactions"])

@router.post("", response_model=InteractionResponse)
async def post_interaction(body: InteractionRequest, db: asyncpg.Connection = Depends(get_db)):
    """
    Log an interaction (rating) for a recipe by a user.
    Upserts (updates) if the interaction already exists.
    """
    # Verify recipe exists
    recipe_exists = await db.fetchval("SELECT EXISTS(SELECT 1 FROM recipes WHERE id = $1);", body.recipe_id)
    if not recipe_exists:
        raise HTTPException(status_code=404, detail=f"Recipe ID {body.recipe_id} not found")
        
    query = """
        INSERT INTO interactions (user_id, recipe_id, rating, date)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (user_id, recipe_id)
        DO UPDATE SET rating = EXCLUDED.rating, date = EXCLUDED.date
        RETURNING user_id, recipe_id, rating;
    """
    try:
        row = await db.fetchrow(query, body.user_id, body.recipe_id, body.rating, date.today())
        if not row:
            raise HTTPException(status_code=500, detail="Failed to record interaction")
            
        return InteractionResponse(
            success=True,
            user_id=row["user_id"],
            recipe_id=row["recipe_id"],
            rating=float(row["rating"])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
