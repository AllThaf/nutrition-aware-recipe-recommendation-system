from pydantic import BaseModel

class StatsResponse(BaseModel):
    total_recipes: int
    total_users: int
    total_interactions: int
    sparsity: float
