from pydantic import BaseModel, Field

class InteractionRequest(BaseModel):
    user_id: int
    recipe_id: int
    rating: float = Field(..., ge=1.0, le=5.0, description="Rating from 1.0 to 5.0")

class InteractionResponse(BaseModel):
    success: bool
    user_id: int
    recipe_id: int
    rating: float
