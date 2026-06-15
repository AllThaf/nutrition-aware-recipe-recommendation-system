import torch
import numpy as np
from typing import List, Dict, Any

def score_cf_candidates(net, user2idx: Dict[int, int], item2idx: Dict[int, int], user_id: int, candidate_recipe_ids: List[int]) -> List[Dict[str, Any]]:
    """
    Score specific recipe IDs for a user using NCF Net.
    Recipes that are not recognized by the NCF model will get a score of 0.0.
    """
    if user_id not in user2idx:
        raise KeyError(f"User {user_id} not found in user2idx mapping")
        
    u_idx = user2idx[user_id]
    
    # Filter candidate recipe IDs to only those that are in item2idx and within model bounds
    valid_candidates = []
    valid_item_idxs = []
    
    num_items = net.emb_i_gmf.num_embeddings
    for rid in candidate_recipe_ids:
        if rid in item2idx:
            item_idx = item2idx[rid]
            if item_idx < num_items:
                valid_candidates.append(rid)
                valid_item_idxs.append(item_idx)
            
    if not valid_candidates:
        return [{"recipe_id": rid, "cf_score": 0.0} for rid in candidate_recipe_ids]
        
    # Convert to tensors
    u_tensor = torch.tensor([u_idx] * len(valid_item_idxs), dtype=torch.long)
    i_tensor = torch.tensor(valid_item_idxs, dtype=torch.long)
    
    net.eval()
    with torch.no_grad():
        scores = net(u_tensor, i_tensor)
        if len(scores.shape) == 0:
            scores = scores.unsqueeze(0)
        scores = scores.cpu().numpy()
        
    scores_dict = {rid: float(s) for rid, s in zip(valid_candidates, scores)}
    
    return [
        {"recipe_id": rid, "cf_score": scores_dict.get(rid, 0.0)}
        for rid in candidate_recipe_ids
    ]

def get_top_cf_recipes(net, user2idx: Dict[int, int], idx2item: Dict[int, int], user_id: int, top_k: int = 100) -> List[Dict[str, Any]]:
    """
    Get top K recipes from NCF model for a user among all items the model knows.
    """
    if user_id not in user2idx:
        raise KeyError(f"User {user_id} not found in user2idx mapping")
        
    u_idx = user2idx[user_id]
    n_items = net.emb_i_gmf.num_embeddings
    
    u_tensor = torch.tensor([u_idx] * n_items, dtype=torch.long)
    i_tensor = torch.tensor(list(range(n_items)), dtype=torch.long)
    
    net.eval()
    with torch.no_grad():
        scores = net(u_tensor, i_tensor)
        if len(scores.shape) == 0:
            scores = scores.unsqueeze(0)
        scores = scores.cpu().numpy()
        
    # Sort descending
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        idx_int = int(idx)
        if idx_int in idx2item:
            recipe_id = idx2item[idx_int]
            results.append({
                "recipe_id": recipe_id,
                "cf_score": float(scores[idx_int])
            })
    return results
