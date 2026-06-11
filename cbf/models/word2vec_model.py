import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from gensim.models import Word2Vec
from sklearn.metrics.pairwise import cosine_similarity

# Shared Paths
MODEL_DIR = Path(__file__).parent.parent / "outputs" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

class Word2VecRecommender:
    def __init__(self, vector_size=100, window=5, min_count=1, sg=1, seed=42):
        self.vector_size = vector_size
        self.window = window
        self.min_count = min_count
        self.sg = sg
        self.seed = seed
        self.model = None
        self.recipe_vectors = None
        self.item_ids = None
        self.item_id_to_idx = {}
        
    def fit(self, df: pd.DataFrame, ingredients_col: str, id_col: str = 'id'):
        """
        Fit the Word2Vec model on the list of ingredients per recipe.
        """
        print(f"Training Word2Vec model on {len(df)} recipes...")
        self.item_ids = df[id_col].values
        self.item_id_to_idx = {item_id: idx for idx, item_id in enumerate(self.item_ids)}
        
        # Ensure all ingredient items are strings for Gensim Word2Vec
        sentences = df[ingredients_col].apply(lambda x: [str(item) for item in x]).tolist()
        
        self.model = Word2Vec(
            sentences=sentences,
            vector_size=self.vector_size,
            window=self.window,
            min_count=self.min_count,
            sg=self.sg,
            seed=self.seed,
            workers=4
        )
        
        # Build recipe vectors (average of ingredient vectors)
        recipe_vectors = []
        for recipe_ing in sentences:
            vecs = [self.model.wv[ing] for ing in recipe_ing if ing in self.model.wv]
            if vecs:
                recipe_vectors.append(np.mean(vecs, axis=0))
            else:
                recipe_vectors.append(np.zeros(self.vector_size))
        
        self.recipe_vectors = np.array(recipe_vectors)
        print(f"Recipe vectors shape: {self.recipe_vectors.shape}")
        
    def save(self, filepath: str):
        """Save the model and recipe vectors."""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'recipe_vectors': self.recipe_vectors,
                'item_ids': self.item_ids,
                'item_id_to_idx': self.item_id_to_idx,
                'vector_size': self.vector_size
            }, f)
        print(f"Model saved to {filepath}")
            
    def load(self, filepath: str):
        """Load the model and recipe vectors."""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.recipe_vectors = data['recipe_vectors']
            self.item_ids = data['item_ids']
            self.item_id_to_idx = data['item_id_to_idx']
            self.vector_size = data['vector_size']
        print(f"Model loaded from {filepath}")
            
    def get_similar_items(self, item_id: int, top_k: int = 10) -> list:
        """
        Get top_k most similar items based on cosine similarity
        """
        if item_id not in self.item_id_to_idx:
            raise ValueError(f"Item ID {item_id} not found in vocabulary.")
            
        target_idx = self.item_id_to_idx[item_id]
        target_vec = self.recipe_vectors[target_idx].reshape(1, -1)
        
        sim_scores = cosine_similarity(target_vec, self.recipe_vectors).flatten()
        
        if len(sim_scores) > top_k + 1:
            top_indices = np.argpartition(sim_scores, -(top_k+1))[-(top_k+1):]
            top_indices = top_indices[np.argsort(sim_scores[top_indices])[::-1]]
        else:
            top_indices = np.argsort(sim_scores)[::-1]
            
        results = []
        for idx in top_indices:
            if idx != target_idx and len(results) < top_k:
                results.append((self.item_ids[idx], sim_scores[idx]))
                
        return results
