import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Resolve paths to ensure internal modules import properly
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from webapp.backend.database import create_db_pool, close_db_pool
from webapp.backend.settings import settings
from webapp.backend.pipeline.loader import load_cf, load_cbf, load_nutrition
from webapp.backend.routers import stats, recipes, users, interactions, recommend, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    # 1. Initialize PostgreSQL Connection Pool
    await create_db_pool()
    
    # 2. Load Recommendation Pipeline Models
    try:
        app.state.cf = load_cf(settings.CF_MODEL_PATH)
    except Exception as e:
        print(f"CRITICAL: Failed to load CF model artifact: {e}")
        app.state.cf = None
        
    try:
        app.state.cbf = load_cbf(settings.CBF_MODEL_PATH)
    except Exception as e:
        print(f"CRITICAL: Failed to load CBF model artifact: {e}")
        app.state.cbf = None
        
    app.state.nutrition = load_nutrition()
    
    print("Application initialization complete.")
    yield
    
    # --- SHUTDOWN ---
    await close_db_pool()
    print("Application shutdown complete.")

app = FastAPI(
    title="Nutrition-Aware Recipe Recommendation API",
    description="Backend API service for hybrid recipe recommendation using NCF, CBF, and Nutrition Cascade",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(stats.router)
app.include_router(recipes.router)
app.include_router(users.router)
app.include_router(interactions.router)
app.include_router(recommend.router)
app.include_router(auth.router)

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Welcome to the Nutrition-Aware Recipe Recommendation System API",
        "docs_url": "/docs"
    }
