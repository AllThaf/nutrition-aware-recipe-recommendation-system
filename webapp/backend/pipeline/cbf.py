import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any

def score_cbf_candidates(cbf_artifacts, candidate_recipe_ids: List[int], past_recipe_ids: List[int]) -> List[Dict[str, Any]]:
    """
    Score candidates using Content-Based Filtering.
    Adopts Max-Pooling cosine similarity from ablation/cascade.py.
    """
    if not past_recipe_ids or not candidate_recipe_ids:
        return [{"recipe_id": rid, "similarity_score": 0.0} for rid in candidate_recipe_ids]
        
    mat = cbf_artifacts.tfidf_matrix
    mapping = cbf_artifacts.item_id_to_idx
    
    # Get indices for user history
    hist_idx = [mapping[rid] for rid in past_recipe_ids if rid in mapping]
    if not hist_idx:
        return [{"recipe_id": rid, "similarity_score": 0.0} for rid in candidate_recipe_ids]
        
    # Get indices for candidate recipes
    cand_idx = []
    valid_mask = []
    for rid in candidate_recipe_ids:
        if rid in mapping:
            cand_idx.append(mapping[rid])
            valid_mask.append(True)
        else:
            cand_idx.append(0)  # dummy index
            valid_mask.append(False)
            
    # Fetch vectors
    hist_vecs = mat[hist_idx]
    cand_vecs = mat[cand_idx]
    
    # Calculate cosine similarity matrix (shape: num_history, num_candidates)
    sims = cosine_similarity(hist_vecs, cand_vecs)
    
    # Max similarity for each candidate
    scores = sims.max(axis=0)
    
    # Mask out candidates not in vocabulary
    scores = scores * np.array(valid_mask)
    
    scores_dict = {rid: float(s) for rid, s in zip(candidate_recipe_ids, scores)}
    
    return [
        {"recipe_id": rid, "similarity_score": scores_dict.get(rid, 0.0)}
        for rid in candidate_recipe_ids
    ]
