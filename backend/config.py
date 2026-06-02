"""Configuration settings for FastAPI application"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/nutrition_recipe_db"
)

# API Configuration
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
API_TITLE = "Nutrition-Aware Recipe Recommendation System"
API_DESCRIPTION = "Backend API untuk sistem rekomendasi resep berbasis nutrisi"
API_VERSION = "1.0.0"

# Model Configuration
# Default to the latest CF model artifact shipped with the repo.
MODEL_FILENAME = os.getenv("MODEL_FILENAME", "best_cf_model_ncf.pkl")
# Path (relative or absolute) to the directory containing the pickle.
# Defaults to the repo's CF output model directory.
# NOTE: some environments may set MODEL_PATH to an unrelated relative directory.
# For compatibility, always default to repo-local cf output unless an absolute path is provided.
raw_model_path = os.getenv("MODEL_PATH")
MODEL_PATH = raw_model_path if raw_model_path and os.path.isabs(raw_model_path) else "cf/outputs/models/"


# Force repo-local default in absence of env var override.
# This prevents accidental loading attempts from unrelated relative paths.
if not os.getenv("MODEL_PATH"):
    MODEL_PATH = "cf/outputs/models/"


# If an environment variable accidentally points somewhere invalid (e.g. "./models/"),
# the loader will fail. Leave this override here for local runs.


# Used as a base when composing absolute-ish paths in the pipeline.
# Keep it as the repo root relative path.
PICKLE_PATH = os.getenv("PICKLE_PATH", ".")



# CORS Configuration
CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://localhost:5173",
]

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
