from fastapi import APIRouter, Depends
import asyncpg
from webapp.backend.database import get_db
from webapp.backend.schemas.stats import StatsResponse

router = APIRouter(prefix="/stats", tags=["Statistics"])

@router.get("", response_model=StatsResponse)
async def get_stats(db: asyncpg.Connection = Depends(get_db)):
    # Query all counts in a single efficient query
    query = """
        SELECT 
            (SELECT COUNT(*) FROM recipes) as total_recipes,
            (SELECT COUNT(DISTINCT user_id) FROM interactions) as total_users,
            (SELECT COUNT(*) FROM interactions) as total_interactions;
    """
    row = await db.fetchrow(query)
    
    total_recipes = row["total_recipes"] if row else 0
    total_users = row["total_users"] if row else 0
    total_interactions = row["total_interactions"] if row else 0
    
    sparsity = 0.0
    if total_recipes > 0 and total_users > 0:
        sparsity = (1.0 - (total_interactions / (total_recipes * total_users))) * 100.0
        
    return StatsResponse(
        total_recipes=total_recipes,
        total_users=total_users,
        total_interactions=total_interactions,
        sparsity=sparsity
    )
