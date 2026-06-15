from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default="postgresql://postgres:secret@db:5432/recipe_db",
        description="Database URL for PostgreSQL connection"
    )
    CF_MODEL_PATH: str = Field(
        default="/app/cf/outputs/models/best_cf_model_ncf.pkl",
        description="File path to Collaborative Filtering model pickle"
    )
    CBF_MODEL_PATH: str = Field(
        default="/app/cbf/outputs/models/best_cbf_model_tfidf.pkl",
        description="File path to Content-Based Filtering model pickle"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
