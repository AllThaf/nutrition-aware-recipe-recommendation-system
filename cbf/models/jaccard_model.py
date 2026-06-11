import pandas as pd
import numpy as np
import pickle
from pathlib import Path

# Shared Paths
MODEL_DIR = Path(__file__).parent.parent / "outputs" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

class JaccardRecommender:
    def __init__(self):
        self.recipe_ingredients = {} # recipe_id -> set of ingredients (or ingredient_ids)
        self.item_ids = None
        self.item_id_to_idx = {}
        
    def fit(self, df: pd.DataFrame, ingredients_col: str, id_col: str = 'id'):
        """
        Fit the Jaccard model by storing the set of ingredients for each recipe.
        """
        print(f"Fitting Jaccard model on {len(df)} recipes...")
        self.item_ids = df[id_col].values
        self.item_id_to_idx = {item_id: idx for idx, item_id in enumerate(self.item_ids)}
        
        # Build dictionary of sets for fast intersection/union
        for _, row in df.iterrows():
            item_id = row[id_col]
            # Ensure ingredients are in a list/iterable
            ingredients = row[ingredients_col]
            self.recipe_ingredients[item_id] = set(ingredients)
            
        print(f"Jaccard index built for {len(self.recipe_ingredients)} recipes.")
        
    def save(self, filepath: str):
        """Save the model state."""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'recipe_ingredients': self.recipe_ingredients,
                'item_ids': self.item_ids,
                'item_id_to_idx': self.item_id_to_idx
            }, f)
        print(f"Model saved to {filepath}")
            
    def load(self, filepath: str):
        """Load the model state."""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.recipe_ingredients = data['recipe_ingredients']
            self.item_ids = data['item_ids']
            self.item_id_to_idx = data['item_id_to_idx']
        print(f"Model loaded from {filepath}")
            
    def get_similar_items(self, item_id: int, top_k: int = 10) -> list:
        """
        Get top_k most similar items based on Jaccard similarity
        """
        if item_id not in self.recipe_ingredients:
            raise ValueError(f"Item ID {item_id} not found.")
            
        target_set = self.recipe_ingredients[item_id]
        
        results = []
        for other_id, other_set in self.recipe_ingredients.items():
            if other_id == item_id:
                continue
            intersection = len(target_set.intersection(other_set))
            union = len(target_set.union(other_set))
            score = intersection / union if union > 0 else 0.0
            results.append((other_id, score))
            
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
