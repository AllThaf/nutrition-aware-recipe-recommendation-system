import pandas as pd
import numpy as np
import pickle
import random
import itertools
from pathlib import Path
import networkx as nx
from gensim.models import Word2Vec
from sklearn.metrics.pairwise import cosine_similarity

# Shared Paths
MODEL_DIR = Path(__file__).parent.parent / "outputs" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

class Node2VecRecommender:
    def __init__(self, vector_size=100, num_walks=5, walk_length=15, window=5, sg=1, seed=42):
        self.vector_size = vector_size
        self.num_walks = num_walks
        self.walk_length = walk_length
        self.window = window
        self.sg = sg
        self.seed = seed
        self.model = None
        self.recipe_vectors = None
        self.item_ids = None
        self.item_id_to_idx = {}
        
    def fit(self, df: pd.DataFrame, ingredients_col: str, id_col: str = 'id'):
        """
        Builds the co-occurrence graph, generates random walks, trains Word2Vec on the walks,
        and aggregates node embeddings to build recipe vectors.
        """
        print(f"Building co-occurrence graph for {len(df)} recipes...")
        self.item_ids = df[id_col].values
        self.item_id_to_idx = {item_id: idx for idx, item_id in enumerate(self.item_ids)}
        
        # Ensure all ingredient items are strings
        recipes_ingredients = df[ingredients_col].apply(lambda x: [str(item) for item in x]).tolist()
        
        # 1. Build NetworkX Graph
        G = nx.Graph()
        cooccurrences = {}
        
        # Build node list first
        for recipe_ing in recipes_ingredients:
            for ing in recipe_ing:
                G.add_node(ing)
                
        # Count co-occurrences
        for recipe_ing in recipes_ingredients:
            unique_ing = list(set(recipe_ing))
            if len(unique_ing) < 2:
                continue
            for ing1, ing2 in itertools.combinations(sorted(unique_ing), 2):
                pair = (ing1, ing2)
                cooccurrences[pair] = cooccurrences.get(pair, 0) + 1
                
        # Add edges to the graph
        for (ing1, ing2), weight in cooccurrences.items():
            G.add_edge(ing1, ing2, weight=weight)
            
        print(f"Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
        
        # 2. Precompute transition probabilities for random walks (weighted transitions)
        print("Precomputing transition tables...")
        transitions = {}
        for node in G.nodes():
            neighbors = list(G.neighbors(node))
            if neighbors:
                weights = [G[node][nbr].get('weight', 1.0) for nbr in neighbors]
                transitions[node] = (neighbors, weights)
                
        # 3. Generate Random Walks
        print(f"Generating random walks (num_walks={self.num_walks}, walk_length={self.walk_length})...")
        random.seed(self.seed)
        walks = []
        nodes = list(G.nodes())
        for walk_iter in range(self.num_walks):
            random.shuffle(nodes)
            for node in nodes:
                walk = [node]
                while len(walk) < self.walk_length:
                    curr = walk[-1]
                    if curr in transitions:
                        neighbors, weights = transitions[curr]
                        next_node = random.choices(neighbors, weights=weights, k=1)[0]
                        walk.append(next_node)
                    else:
                        break
                walks.append(walk)
                
        print(f"Generated {len(walks)} random walks. Training Word2Vec embeddings...")
        
        # 4. Train Word2Vec on Random Walks (Node2Vec)
        self.model = Word2Vec(
            sentences=walks,
            vector_size=self.vector_size,
            window=self.window,
            min_count=1,
            sg=self.sg,
            seed=self.seed,
            workers=4
        )
        
        # 5. Build Recipe Vectors (average of ingredient embeddings)
        recipe_vectors = []
        for recipe_ing in recipes_ingredients:
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
            raise ValueError(f"Item ID {item_id} not found.")
            
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
