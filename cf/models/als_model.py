"""
cf/models/als_model.py
──────────────────────
ALS (Alternating Least Squares) Collaborative Filtering model.

Uses the `implicit` library which implements a highly optimized, multithreaded
C++ backend for ALS on implicit feedback data.

Reference:
  Hu, Y., Koren, Y., & Volinsky, C. (2008).
  Collaborative Filtering for Implicit Feedback Datasets. ICDM 2008.

Confidence formula:
  c(u, i) = 1 + alpha * r(u, i)
  where r(u, i) = 1 for all positive (interacted) items (binary matrix input).
"""

from __future__ import annotations

import os
import numpy as np
import scipy.sparse as sp

# Prevent OpenBLAS internal threading from conflicting with implicit's own parallelism
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

try:
    from implicit.als import AlternatingLeastSquares
    import implicit
    _IMPLICIT_VERSION = tuple(int(x) for x in implicit.__version__.split(".")[:2])
except ImportError as e:
    raise ImportError(
        "The `implicit` library is required. Install with: pip install implicit"
    ) from e


class ALSModel:
    """
    ALS Collaborative Filtering with implicit feedback.

    Parameters
    ----------
    factors        : number of latent factors (embedding dimension).
    regularization : L2 regularization penalty.
    iterations     : number of ALS sweeps.
    alpha          : confidence scaling factor. Higher = more weight on positive items.
    random_state   : random seed for reproducibility.
    """

    def __init__(
        self,
        factors: int = 64,
        regularization: float = 0.01,
        iterations: int = 20,
        alpha: float = 40.0,
        random_state: int = 42,
    ) -> None:
        self.factors        = factors
        self.regularization = regularization
        self.iterations     = iterations
        self.alpha          = alpha
        self.random_state   = random_state

        self._model         = None
        self._user_factors  = None  # (n_users, factors)
        self._item_factors  = None  # (n_items, factors)
        self._n_items       = None

    # ── Training ──────────────────────────────────────────────────────────────

    def fit(self, user_item_matrix: sp.csr_matrix) -> "ALSModel":
        """
        Train ALS on a (n_users × n_items) sparse matrix.

        The matrix values represent preference strength (typically binary 0/1).
        ALS internally computes confidence = 1 + alpha * value.

        Parameters
        ----------
        user_item_matrix : csr_matrix of shape (n_users, n_items).
        """
        self._n_items = user_item_matrix.shape[1]

        # Scale by alpha to get confidence values
        conf_matrix = (self.alpha * user_item_matrix).astype(np.float32)

        self._model = AlternatingLeastSquares(
            factors            = self.factors,
            regularization     = self.regularization,
            iterations         = self.iterations,
            calculate_training_loss = False,
            use_gpu            = False,
            random_state       = self.random_state,
        )

        # implicit >= 0.7 uses user_items directly; older versions need transpose
        # We pass user_item (n_users, n_items) — works with implicit >= 0.6.2
        self._model.fit(conf_matrix, show_progress=True)

        self._user_factors = np.array(self._model.user_factors)  # (n_users, factors)
        self._item_factors = np.array(self._model.item_factors)  # (n_items, factors)

        print(
            f"[ALS] Trained — factors={self.factors}, "
            f"reg={self.regularization}, iter={self.iterations}, alpha={self.alpha}"
        )
        return self

    # ── Inference ─────────────────────────────────────────────────────────────

    def score_candidates(self, user_id: int, candidate_items: np.ndarray) -> np.ndarray:
        """
        Score a set of candidate items for a given user.

        Computes dot product between user factor and each candidate item factor.
        Higher score = model predicts higher relevance.

        Parameters
        ----------
        user_id         : integer user index.
        candidate_items : 1-D integer array of item indices to score.

        Returns
        -------
        scores : np.ndarray of shape (len(candidate_items),)
        """
        if self._user_factors is None:
            raise RuntimeError("Model must be trained before calling score_candidates().")

        u_vec = self._user_factors[user_id]           # (factors,)
        i_mat = self._item_factors[candidate_items]   # (n_cands, factors)
        return i_mat @ u_vec                          # (n_cands,)

    # ── Utils ─────────────────────────────────────────────────────────────────

    def get_params(self) -> dict:
        return {
            "factors"       : self.factors,
            "regularization": self.regularization,
            "iterations"    : self.iterations,
            "alpha"         : self.alpha,
        }

    def __repr__(self) -> str:
        return (
            f"ALSModel(factors={self.factors}, reg={self.regularization}, "
            f"iter={self.iterations}, alpha={self.alpha})"
        )
