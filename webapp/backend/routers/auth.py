from fastapi import APIRouter, Depends, HTTPException, status
import asyncpg
from webapp.backend.database import get_db
from webapp.backend.schemas.user import LoginRequest, LoginResponse
from webapp.backend.routers.users import PERSONAS

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: asyncpg.Connection = Depends(get_db)):
    """
    Dummy universal authentication endpoint.
    Accepts user_id and password.
    Password must be 'nutricook'.
    """
    if body.password != "nutricook":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password salah. Silakan gunakan password universal 'nutricook'"
        )

    # Check if the user ID matches a persona
    display_name = f"User #{body.user_id}"
    for persona in PERSONAS:
        if persona.user_id == body.user_id:
            display_name = persona.display_name.split(" (")[0] # Clean display name
            break

    # Check if user exists in database interactions (as verification or fallback)
    if display_name == f"User #{body.user_id}":
        row = await db.fetchrow("SELECT DISTINCT user_id FROM interactions WHERE user_id = $1 LIMIT 1;", body.user_id)
        if not row:
            # New user (cold start is allowed, but we can set their display name appropriately)
            display_name = f"User #{body.user_id} (Baru)"

    return LoginResponse(
        user_id=body.user_id,
        display_name=display_name,
        token="dummy-jwt-token"
    )
