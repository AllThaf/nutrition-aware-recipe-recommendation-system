"""Recommendation inference pipelines.

This backend integrates the latest CF recommendation model artifact shipped in
`cf/outputs/models/`.

The CF model pickles in this repo are trained using the wrappers in `cf/models/*`.
Those wrappers expose a `score_candidates(user_id, candidate_items)` API.
"""

from __future__ import annotations

import os
import pickle
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

# Ensure `cf/` is importable so pickled model wrappers can resolve modules like
# `models.ncf_model` during unpickling.
_CF_PARENT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cf"))
if _CF_PARENT not in os.sys.path:
    os.sys.path.insert(0, _CF_PARENT)


def _resolve_model_path(
    model_path: Optional[str],
    model_filename: str,
    pickle_path: str,
) -> str:
    """Resolve the on-disk path to the model pickle.

    Accepted inputs:
    - model_path is absolute file => use directly
    - model_path is relative directory => join pickle_path + model_path + filename
    - model_path is absolute directory => join model_path + filename
    - model_path is None/empty => join pickle_path + filename
    """
    mp = (model_path or "").strip()
    if mp:
        # If it looks like a file, use it.
        if mp.lower().endswith((".pkl", ".pickle", ".joblib")):
            if os.path.isabs(mp):
                return mp
            return os.path.normpath(os.path.join(pickle_path, mp))

        # Otherwise treat as directory.
        if os.path.isabs(mp):
            return os.path.normpath(os.path.join(mp, model_filename))
        return os.path.normpath(os.path.join(pickle_path, mp, model_filename))

    # Fallback: try to load model_filename under pickle_path
    return os.path.normpath(os.path.join(pickle_path, model_filename))


@dataclass
class ScoredRecipe:
    recipe: Dict[str, Any]
    score: float
    reasoning: str


class CFRecipeRecommendationPipeline:
    """CF-based recommendation pipeline using the pickled CF wrapper model."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        model_filename: str = "best_cf_model_ncf.pkl",
        pickle_path: str = ".",
    ) -> None:
        self.model = None
        self.model_path = _resolve_model_path(model_path, model_filename, pickle_path)
        self._load_model()

    def _load_model(self) -> None:
        try:
            with open(self.model_path, "rb") as f:
                loaded = pickle.load(f)

            # Some training scripts pickle a wrapper dict like: {"name": ..., "model": <wrapper>}
            # while others pickle the wrapper object directly.
            if isinstance(loaded, dict) and "model" in loaded:
                self.model = loaded["model"]
            else:
                self.model = loaded

            print(f"✓ CF model loaded from {self.model_path} ({type(self.model)})")
        except Exception as e:
            raise RuntimeError(f"Failed to load CF model from {self.model_path}: {e}") from e


    def _get_mapping(self) -> Tuple[Optional[Dict[Any, int]], Optional[Dict[Any, int]]]:
        """Best-effort extraction of ID mappings from the loaded model."""
        user_id_map = None
        item_id_map = None

        for user_attr in ("user_id_map", "user2idx", "users_map", "user_map"):
            if hasattr(self.model, user_attr):
                user_id_map = getattr(self.model, user_attr)
                break

        for item_attr in ("item_id_map", "item2idx", "items_map", "item_map"):
            if hasattr(self.model, item_attr):
                item_id_map = getattr(self.model, item_attr)
                break

        return user_id_map, item_id_map

    def _map_user(self, raw_user_id: Any) -> int:
        user_id_map, _ = self._get_mapping()
        if user_id_map is None:
            return int(raw_user_id)

        if raw_user_id not in user_id_map:
            raise KeyError(f"User id {raw_user_id} not found in model mapping")
        return int(user_id_map[raw_user_id])

    def _map_items(self, raw_item_ids: Sequence[Any]) -> np.ndarray:
        _, item_id_map = self._get_mapping()
        if item_id_map is None:
            return np.array([int(x) for x in raw_item_ids], dtype=np.int64)

        mapped: List[int] = []
        for rid in raw_item_ids:
            if rid not in item_id_map:
                # Unknown items are skipped.
                continue
            mapped.append(int(item_id_map[rid]))
        return np.array(mapped, dtype=np.int64)

    def _score(self, raw_user_id: Any, raw_recipe_ids: Sequence[int]) -> np.ndarray:
        user_idx = self._map_user(raw_user_id)
        candidate_item_idxs = self._map_items(raw_recipe_ids)

        if candidate_item_idxs.size == 0:
            return np.array([], dtype=np.float32)

        if not hasattr(self.model, "score_candidates"):
            raise RuntimeError("Loaded model does not expose score_candidates(user_id, candidate_items).")

        scores = self.model.score_candidates(user_idx, candidate_item_idxs)
        return np.asarray(scores, dtype=np.float32)

    def get_top_recommendations(
        self,
        user_preferences: Dict[str, Any],
        recipes: List[Dict[str, Any]],
        n_recommendations: int = 5,
    ) -> List[Dict[str, Any]]:
        raw_recipe_ids = [int(r["id"]) for r in recipes if r.get("id") is not None]
        recipes_by_id = {int(r["id"]): r for r in recipes if r.get("id") is not None}

        user_id = user_preferences.get("user_id")
        if user_id is None:
            user_id = user_preferences.get("id")

        scores = self._score(user_id, raw_recipe_ids)
        if scores.size == 0:
            return self._fallback_by_preferences(user_preferences, recipes, n_recommendations)

        # If item mapping exists, we must align scores with the mapped subset.
        _, item_id_map = self._get_mapping()
        scored_items: List[Tuple[int, float]] = []

        if item_id_map is None:
            for rid, s in zip(raw_recipe_ids, scores.tolist()):
                scored_items.append((rid, float(s)))
        else:
            valid_rids = [rid for rid in raw_recipe_ids if rid in item_id_map]
            for rid, s in zip(valid_rids, scores.tolist()):
                scored_items.append((rid, float(s)))

        scored_items.sort(key=lambda x: x[1], reverse=True)
        top = scored_items[:n_recommendations]

        results: List[Dict[str, Any]] = []
        for rid, s in top:
            recipe = recipes_by_id.get(rid)
            if recipe is None:
                continue
            results.append(
                {
                    "recipe": recipe,
                    "score": self._normalize_score(s),
                    "reasoning": self._generate_reasoning(user_preferences, recipe),
                }
            )

        return results

    def _normalize_score(self, score: float) -> float:
        # CF outputs may not be [0,1]. Keep UI stable.
        try:
            return float(1.0 / (1.0 + np.exp(-score)))
        except Exception:
            return 0.5

    def _generate_reasoning(self, user_preferences: Dict[str, Any], recipe: Dict[str, Any]) -> str:
        reasons: List[str] = []

        min_cal = user_preferences.get("min_calories") or 0
        max_cal = user_preferences.get("max_calories") or 3000
        cal = recipe.get("calories") or 0
        if min_cal <= cal <= max_cal:
            reasons.append("Matches your calorie goals")

        min_protein = user_preferences.get("min_protein") or 0
        if (recipe.get("protein") or 0) >= min_protein:
            reasons.append("Good protein content")

        if user_preferences.get("vegetarian"):
            name = str(recipe.get("name", "")).lower()
            if "meat" not in name:
                reasons.append("Fits your vegetarian preferences")

        return " | ".join(reasons) if reasons else "Matches your dietary preferences"

    def _fallback_by_preferences(
        self,
        user_preferences: Dict[str, Any],
        recipes: List[Dict[str, Any]],
        n_recommendations: int,
    ) -> List[Dict[str, Any]]:
        min_cal = user_preferences.get("min_calories") or 0
        max_cal = user_preferences.get("max_calories") or 3000

        def score_recipe(r: Dict[str, Any]) -> float:
            cal = r.get("calories") or 0
            if min_cal <= cal <= max_cal:
                return 1.0
            if cal < min_cal:
                return max(0.0, 1.0 - (min_cal - cal) / max(1.0, max_cal - min_cal + 1.0))
            return max(0.0, 1.0 - (cal - max_cal) / max(1.0, max_cal - min_cal + 1.0))

        ranked = sorted(recipes, key=score_recipe, reverse=True)
        out: List[Dict[str, Any]] = []
        for r in ranked[:n_recommendations]:
            out.append(
                {
                    "recipe": r,
                    "score": float(score_recipe(r)),
                    "reasoning": self._generate_reasoning(user_preferences, r),
                }
            )
        return out

