"""
cf/evaluator.py
───────────────
Evaluation metrics for Top-N recommendation.

Implements the Leave-One-Out (LOO) evaluation protocol as described in:
  He et al. (2017) — Neural Collaborative Filtering (WWW '17)
  Tamm et al. (2021) — Quality Metrics in Recommender Systems (RecSys '21)

Metrics:
  HR@K  (Hit Rate @ K)      — 1 if ground truth appears in top-K recommendations
  MRR   (Mean Reciprocal Rank) — 1/rank of the ground truth in the ranked list
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np
import pandas as pd


# ══════════════════════════════════════════════════════════════════════════════
# Core metric functions
# ══════════════════════════════════════════════════════════════════════════════

def hit_at_k(ranked_positions: List[int], label_idx: int, k: int) -> float:
    """
    Hit Rate @ K.

    Parameters
    ----------
    ranked_positions : list of candidate indices sorted by descending score.
                       e.g. [3, 0, 7, 1, ...] means candidate #3 is rank 1.
    label_idx        : index (in the candidate list) of the ground-truth item.
    k                : cut-off rank.

    Returns
    -------
    1.0 if label_idx is in the top-K of ranked_positions, else 0.0
    """
    return 1.0 if label_idx in ranked_positions[:k] else 0.0


def reciprocal_rank(ranked_positions: List[int], label_idx: int) -> float:
    """
    Reciprocal Rank (RR) component for MRR.

    Returns 1/rank if the ground-truth is found in the ranked list, else 0.0.
    Rank is 1-based.
    """
    try:
        rank = ranked_positions.index(label_idx) + 1  # 1-based
        return 1.0 / rank
    except ValueError:
        return 0.0  # not found


# ══════════════════════════════════════════════════════════════════════════════
# Batch evaluation
# ══════════════════════════════════════════════════════════════════════════════

def evaluate_loo(
    model,
    loo_data: List[dict],
    k_values: Tuple[int, ...] = (5, 10, 20),
    verbose: bool = True,
) -> dict[str, float]:
    """
    Evaluate a CF model on Leave-One-Out data.

    The model must expose:
        score_candidates(user_id: int, candidate_items: np.ndarray) -> np.ndarray
            Returns a float array of scores, one per candidate.
            Higher score = more relevant.

    Parameters
    ----------
    model    : trained CF model with `score_candidates` method.
    loo_data : list of dicts from data_prep.prepare_loo_eval().
    k_values : HR@K cut-offs to compute.
    verbose  : print intermediate progress.

    Returns
    -------
    dict with keys like 'HR@5', 'HR@10', 'HR@20', 'MRR'
    """
    buckets: dict[str, list[float]] = {f"HR@{k}": [] for k in k_values}
    buckets["MRR"] = []

    n = len(loo_data)
    report_every = max(1, n // 10)

    for idx, entry in enumerate(loo_data):
        u          = entry["u"]
        candidates = entry["candidates"]   # np.ndarray, shape (1 + n_neg,)
        label_idx  = entry["label_idx"]    # position of pos_item in candidates

        # Get scores from model
        scores = model.score_candidates(u, candidates)  # shape: (n_candidates,)

        # Rank by descending score → list of candidate positions
        ranked_positions: List[int] = np.argsort(scores)[::-1].tolist()

        # Accumulate metrics
        for k in k_values:
            buckets[f"HR@{k}"].append(hit_at_k(ranked_positions, label_idx, k))
        buckets["MRR"].append(reciprocal_rank(ranked_positions, label_idx))

        if verbose and (idx + 1) % report_every == 0:
            pct = (idx + 1) / n * 100
            print(f"  Evaluating… {idx+1:,}/{n:,} ({pct:.0f}%)")

    results = {key: float(np.mean(vals)) for key, vals in buckets.items()}
    return results


# ══════════════════════════════════════════════════════════════════════════════
# Pretty printing
# ══════════════════════════════════════════════════════════════════════════════

def print_metrics(name: str, metrics: dict[str, float]) -> None:
    """Print a formatted metrics row."""
    ks = sorted(
        [int(k.split("@")[1]) for k in metrics if k.startswith("HR@")]
    )
    header = f"{'Model':<14}" + "".join(f"  HR@{k:>2}" for k in ks) + "     MRR"
    row    = f"{name:<14}" + "".join(f"  {metrics[f'HR@{k}']:>6.4f}" for k in ks) + f"  {metrics['MRR']:>6.4f}"
    print(header)
    print("-" * len(header))
    print(row)


def metrics_to_dataframe(results: dict[str, dict]) -> pd.DataFrame:
    """
    Convert {model_name: metrics_dict} to a tidy DataFrame for reporting.

    Example input:
        {
          'ALS': {'HR@5': 0.12, 'HR@10': 0.18, 'HR@20': 0.25, 'MRR': 0.09},
          'BPR': {'HR@5': 0.15, 'HR@10': 0.21, 'HR@20': 0.28, 'MRR': 0.11},
        }
    """
    rows = []
    for model_name, metrics in results.items():
        row = {"Model": model_name}
        row.update(metrics)
        rows.append(row)
    df = pd.DataFrame(rows).set_index("Model")
    # Sort columns: HR@5, HR@10, HR@20, MRR
    ordered_cols = sorted(
        [c for c in df.columns if c.startswith("HR@")],
        key=lambda c: int(c.split("@")[1]),
    ) + ["MRR"]
    return df[[c for c in ordered_cols if c in df.columns]]
