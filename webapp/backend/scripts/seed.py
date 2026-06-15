import os
import sys
import argparse
import asyncio
import ast
import time
from pathlib import Path
import pandas as pd
import numpy as np
import asyncpg

# Add backend directory to sys.path to enable proper imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

def parse_list(val):
    if not val or pd.isna(val):
        return []
    if isinstance(val, list):
        return val
    try:
        return ast.literal_eval(val)
    except Exception:
        return []

async def seed_db(db_url: str, data_dir: str, limit_recipes: int, reset: bool):
    data_path = Path(data_dir)
    recipes_csv = data_path / "RAW_recipes.csv"
    interactions_csv = data_path / "RAW_interactions.csv"

    if not recipes_csv.exists():
        print(f"Error: RAW_recipes.csv not found at {recipes_csv}")
        return
    if not interactions_csv.exists():
        print(f"Error: RAW_interactions.csv not found at {interactions_csv}")
        return

    print("Connecting to database...")
    conn = await asyncpg.connect(db_url)
    try:
        # 1. Run Schema definition
        schema_path = Path(__file__).resolve().parent / "schema.sql"
        if schema_path.exists():
            print("Applying database schema...")
            schema_ddl = schema_path.read_text()
            await conn.execute(schema_ddl)
        else:
            print("Warning: schema.sql not found, skipping schema creation.")

        # 2. Reset database if requested
        if reset:
            print("Resetting database tables (TRUNCATE)...")
            await conn.execute("TRUNCATE TABLE recipes, interactions RESTART IDENTITY CASCADE;")

        # 3. Read Recipes
        print(f"Reading RAW_recipes.csv (limit={limit_recipes if limit_recipes > 0 else 'All'})...")
        start_time = time.time()
        
        # Read either limited rows or full CSV
        if limit_recipes > 0:
            df_recipes = pd.read_csv(recipes_csv, nrows=limit_recipes * 2) # Read extra to account for drop_duplicates/errors
        else:
            df_recipes = pd.read_csv(recipes_csv)

        # Drop duplicates and fill NaNs
        df_recipes.drop_duplicates(subset=["id"], inplace=True)
        if limit_recipes > 0:
            df_recipes = df_recipes.head(limit_recipes)
            
        df_recipes["name"] = df_recipes["name"].fillna("Unnamed Recipe")
        df_recipes["description"] = df_recipes["description"].fillna("")
        df_recipes["minutes"] = df_recipes["minutes"].fillna(0).astype(int)
        df_recipes["n_steps"] = df_recipes["n_steps"].fillna(0).astype(int)
        df_recipes["n_ingredients"] = df_recipes["n_ingredients"].fillna(0).astype(int)

        print(f"Parsed {len(df_recipes)} unique recipes. Converting array columns...")
        
        recipe_records = []
        for idx, row in df_recipes.iterrows():
            tags = parse_list(row["tags"])
            ingredients = parse_list(row["ingredients"])
            steps = parse_list(row["steps"])
            nutrition = parse_list(row["nutrition"])
            
            recipe_records.append((
                int(row["id"]),
                str(row["name"]),
                int(row["minutes"]),
                tags,
                ingredients,
                int(row["n_steps"]),
                steps,
                str(row["description"]),
                nutrition,
                int(row["n_ingredients"])
            ))

        print("Bulk inserting recipes...")
        await conn.copy_records_to_table(
            "recipes",
            records=recipe_records,
            columns=[
                "id", "name", "minutes", "tags", "ingredients", 
                "n_steps", "steps", "description", "nutrition", "n_ingredients"
            ]
        )
        print(f"Successfully seeded {len(recipe_records)} recipes.")
        
        # Keep track of seeded recipe ids to filter interactions
        seeded_recipe_ids = set(df_recipes["id"])

        # 4. Read and Seed Interactions
        print("Reading and filtering RAW_interactions.csv...")
        
        # Read in chunks to be memory efficient and handle large files
        chunk_size = 100000
        total_interactions_seeded = 0
        
        for chunk in pd.read_csv(interactions_csv, chunksize=chunk_size):
            # Filter rows to only contain seeded recipe IDs
            chunk_filtered = chunk[chunk["recipe_id"].isin(seeded_recipe_ids)].copy()
            if chunk_filtered.empty:
                continue
            
            # Clean values
            chunk_filtered.drop_duplicates(subset=["user_id", "recipe_id"], keep="first", inplace=True)
            chunk_filtered["rating"] = chunk_filtered["rating"].fillna(0.0).astype(float)
            chunk_filtered["review"] = chunk_filtered["review"].fillna("")
            
            # Handle date converting safely
            chunk_filtered["date"] = pd.to_datetime(chunk_filtered["date"], errors="coerce")
            
            interaction_records = []
            for _, row in chunk_filtered.iterrows():
                # Format date to string or None for postgres
                date_val = row["date"].date() if not pd.isna(row["date"]) else None
                interaction_records.append((
                    int(row["user_id"]),
                    int(row["recipe_id"]),
                    float(row["rating"]),
                    date_val,
                    str(row["review"])
                ))
            
            # Use COPY for fast insert
            await conn.copy_records_to_table(
                "interactions",
                records=interaction_records,
                columns=["user_id", "recipe_id", "rating", "date", "review"]
            )
            total_interactions_seeded += len(interaction_records)
            
            # If we've seeded enough and have a limit, break or adjust
            # If limit_recipes is set, we don't necessarily need to limit interactions,
            # but filtering already limits them to only the seeded recipes.
            
        print(f"Successfully seeded {total_interactions_seeded} interactions.")
        
        # 5. Sparsity and Statistics Check
        total_recipes = len(recipe_records)
        num_users_row = await conn.fetchrow("SELECT COUNT(DISTINCT user_id) FROM interactions;")
        total_users = num_users_row[0] if num_users_row else 0
        
        sparsity = 0.0
        if total_recipes > 0 and total_users > 0:
            sparsity = (1.0 - (total_interactions_seeded / (total_recipes * total_users))) * 100.0
            
        end_time = time.time()
        print("\n--- Seeding Summary ---")
        print(f"Elapsed Time    : {end_time - start_time:.2f} seconds")
        print(f"Total Recipes   : {total_recipes}")
        print(f"Total Users     : {total_users}")
        print(f"Interactions    : {total_interactions_seeded}")
        print(f"Sparsity        : {sparsity:.4f}%")
        print("-----------------------")

    finally:
        await conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed PostgreSQL database with food.com recipe dataset")
    parser.add_argument("--limit-recipes", type=int, default=20000, help="Limit number of recipes to seed (0 for all)")
    parser.add_argument("--reset", action="store_true", help="Truncate tables before seeding")
    parser.add_argument("--db-url", type=str, default=os.getenv("DATABASE_URL"), help="Database URL link")
    parser.add_argument("--data-dir", type=str, default="/app/food.com", help="Directory where RAW_recipes.csv and RAW_interactions.csv are located")
    
    args = parser.parse_args()
    
    if not args.db_url:
        # Default fallback for running outside docker
        args.db_url = "postgresql://postgres:secret@localhost:5433/recipe_db"
        
    print(f"Starting Seeding with parameters:")
    print(f"  Database URL : {args.db_url.split('@')[-1] if '@' in args.db_url else args.db_url}")
    print(f"  Data Dir     : {args.data_dir}")
    print(f"  Recipe Limit : {args.limit_recipes}")
    print(f"  Reset DB     : {args.reset}")
    
    asyncio.run(seed_db(args.db_url, args.data_dir, args.limit_recipes, args.reset))
