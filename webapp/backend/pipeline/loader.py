import sys
import os
import pickle
from pathlib import Path
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

# Mock implicit module to prevent ImportError during unpickling/imports
class MockImplicitModule(MagicMock):
    __version__ = "0.7.2"

mock_implicit = MockImplicitModule()
mock_implicit_als = MagicMock()
mock_implicit_als.AlternatingLeastSquares = MagicMock()
mock_implicit_bpr = MagicMock()
mock_implicit_bpr.BayesianPersonalizedRanking = MagicMock()

sys.modules["implicit"] = mock_implicit
sys.modules["implicit.als"] = mock_implicit_als
sys.modules["implicit.bpr"] = mock_implicit_bpr

# Mock surprise module to prevent ImportError during unpickling/imports
mock_surprise = MagicMock()
mock_surprise.Dataset = MagicMock()
mock_surprise.Reader = MagicMock()
mock_surprise.SVD = MagicMock()
sys.modules["surprise"] = mock_surprise

# Ensure we add cf and nutrition directories to sys.path so pickle can resolve classes
def _setup_paths():
    root = Path(__file__).resolve().parent.parent.parent.parent
    
    # Docker paths
    docker_cf = Path("/app/cf")
    docker_nutrition = Path("/app/nutrition")
    
    # Local fallback paths
    local_cf = root / "cf"
    local_nutrition = root / "nutrition"
    
    # Add CF
    if docker_cf.exists():
        sys.path.append(str(docker_cf))
    elif local_cf.exists():
        sys.path.append(str(local_cf))
        
    # Add Nutrition
    if docker_nutrition.exists():
        sys.path.append(str(docker_nutrition))
    elif local_nutrition.exists():
        sys.path.append(str(local_nutrition))

_setup_paths()

try:
    from scoring import NutritionScorer
except ImportError:
    # Fallback definition if import fails for any reason
    class NutritionScorer:
        def __init__(self, thresholds=None, rewards=None):
            self.thresholds = thresholds or {
                'calories': 30.0,
                'total_fat_pdv': 30.0,
                'sugar_pdv': 20.0,
                'sodium_pdv': 20.0,
                'saturated_fat_pdv': 20.0
            }
            self.rewards = rewards or {
                'protein_pdv': 5.0,
                'fiber_pdv': 5.0
            }
        
        def calculate_score(self, df, weight_col=None):
            df = df.copy()
            import numpy as np
            penalties = np.zeros(len(df))
            bonus = np.zeros(len(df))
            for nutrient, thr in self.thresholds.items():
                col = 'sat_fat_pdv' if nutrient == 'saturated_fat_pdv' and 'sat_fat_pdv' in df.columns else nutrient
                if col in df.columns:
                    excess = np.maximum(0, df[col] - thr)
                    penalties += (excess / 10.0) * 5.0
            for nutrient, base_val in self.rewards.items():
                if nutrient in df.columns:
                    bonus += (df[nutrient] / base_val) * 2.0
            scores = 100.0 - penalties + bonus
            df['nutrition_score'] = np.clip(scores, 0, 100)
            return df

@dataclass
class CFArtifacts:
    net: Any
    user2idx: dict[int, int]
    item2idx: dict[int, int]
    idx2item: dict[int, int]

@dataclass
class CBFArtifacts:
    tfidf_matrix: Any
    item_id_to_idx: dict[int, int]
    vectorizer: Any

def load_cf(model_path_str: str) -> CFArtifacts:
    model_path = Path(model_path_str)
    if not model_path.exists():
        # Fallback to local
        root = Path(__file__).resolve().parent.parent.parent.parent
        model_path = root / "cf" / "outputs" / "models" / "best_cf_model_ncf.pkl"
        
    if not model_path.exists():
        raise FileNotFoundError(f"CF model file not found at {model_path_str} or local fallback")

    print(f"Loading CF model from {model_path}...")
    model_dir = model_path.parent
    
    with open(model_path, "rb") as f:
        data = pickle.load(f)
    
    # If pickled object is a dict containing the wrapper NCFModel
    if isinstance(data, dict) and "model" in data:
        net = data["model"]._model
    else:
        net = data._model if hasattr(data, "_model") else data
        
    net.eval()
    
    # Load mappings
    with open(model_dir / "user2idx.pkl", "rb") as f:
        user2idx = pickle.load(f)
    with open(model_dir / "item2idx.pkl", "rb") as f:
        item2idx = pickle.load(f)
    with open(model_dir / "idx2item.pkl", "rb") as f:
        idx2item = pickle.load(f)
        
    return CFArtifacts(net=net, user2idx=user2idx, item2idx=item2idx, idx2item=idx2item)

def load_cbf(model_path_str: str) -> CBFArtifacts:
    model_path = Path(model_path_str)
    if not model_path.exists():
        # Fallback to local
        root = Path(__file__).resolve().parent.parent.parent.parent
        model_path = root / "cbf" / "outputs" / "models" / "best_cbf_model_tfidf.pkl"
        
    if not model_path.exists():
        raise FileNotFoundError(f"CBF model file not found at {model_path_str} or local fallback")

    print(f"Loading CBF model from {model_path}...")
    with open(model_path, "rb") as f:
        data = pickle.load(f)
        
    tfidf_matrix = data.get("tfidf_matrix")
    vectorizer = data.get("vectorizer")
    
    # Try item_id_to_idx first, then recipe_index as fallback
    item_id_to_idx = data.get("item_id_to_idx")
    if item_id_to_idx is None:
        item_id_to_idx = data.get("recipe_index")
    if item_id_to_idx is None:
        item_id_to_idx = {}
        
    return CBFArtifacts(tfidf_matrix=tfidf_matrix, item_id_to_idx=item_id_to_idx, vectorizer=vectorizer)

def load_nutrition() -> NutritionScorer:
    print("Initializing NutritionScorer...")
    return NutritionScorer()
