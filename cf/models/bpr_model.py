"""
cf/models/bpr_model.py
──────────────────────
BPR (Bayesian Personalized Ranking) Collaborative Filtering model.

BPR directly optimizes a pairwise ranking objective — making it theoretically
well-aligned with Top-N ranking metrics like Hit Rate@K and MRR.

For each training step, BPR samples:
  (user u, positive item i, negative item j)
  and optimizes: P(u prefers i over j) via sigmoid loss.

Reference:
  Rendle, S., Freudenthaler, C., Gantner, Z., & Schmidt-Thieme, L. (2009).
  BPR: Bayesian Personalized Ranking from Implicit Feedback. UAI 2009.

Implementation:
  Uses the `implicit` library (https://github.com/benfred/implicit)
  which provides an optimized Cython/C++ BPR implementation.
"""

from __future__ import annotations

import os
import numpy as np
import scipy.sparse as sp

# Prevent OpenBLAS internal threading from conflicting with implicit's own parallelism
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

try:
    from implicit.bpr import BayesianPersonalizedRanking
except ImportError as e:
    raise ImportError(
        "The `implicit` library is required. Install with: pip install implicit"
    ) from e


class BPRModel:
    """
    BPR Collaborative Filtering model.

    Optimizes pairwise ranking loss — directly aligned with HR@K and MRR.
    Requires a binary user-item interaction matrix (positive interactions only).

    Parameters
    ----------
    factors                 : latent embedding dimension.
    learning_rate           : SGD step size.
    regularization          : L2 regularization on user/item factors.
    iterations              : number of training epochs over all interactions.
    verify_negative_samples : if True, re-sample negatives that are actually positive.
    random_state            : random seed.
    """

    def __init__(
        self,
        factors: int = 64,
        learning_rate: float = 0.01,
        regularization: float = 0.01,
        iterations: int = 100,
        verify_negative_samples: bool = True,
        random_state: int = 42,
    ) -> None:
        self.factors                  = factors
        self.learning_rate            = learning_rate
        self.regularization           = regularization
        self.iterations               = iterations
        self.verify_negative_samples  = verify_negative_samples
        self.random_state             = random_state

        self._model        = None
        self._user_factors = None  # (n_users, factors)
        self._item_factors = None  # (n_items, factors)

    # ── Training ──────────────────────────────────────────────────────────────

    def fit(self, user_item_matrix: sp.csr_matrix) -> "BPRModel":
        """
        Train BPR on a (n_users × n_items) binary sparse matrix.

        Positive entries (value > 0) are treated as observed interactions.
        All missing entries are potential negatives for pairwise sampling.

        Parameters
        ----------
        user_item_matrix : csr_matrix of shape (n_users, n_items),
                           binary (0/1) values recommended.
        """
        # Ensure binary values — BPR only uses presence/absence
        bin_matrix = user_item_matrix.copy()
        bin_matrix.data = np.ones_like(bin_matrix.data, dtype=np.float32)

        self._model = BayesianPersonalizedRanking(
            factors                 = self.factors,
            learning_rate           = self.learning_rate,
            regularization          = self.regularization,
            iterations              = self.iterations,
            verify_negative_samples = self.verify_negative_samples,
            use_gpu                 = False,
            random_state            = self.random_state,
        )

        self._model.fit(bin_matrix, show_progress=True)

        self._user_factors = np.array(self._model.user_factors)  # (n_users, factors+1)
        self._item_factors = np.array(self._model.item_factors)  # (n_items, factors+1)
        # Note: implicit 0.7.x BPR appends a bias dimension → shape is (n, factors+1)
        # Dot product still works correctly as both user and item share the same extended space

        print(
            f"[BPR] Trained — factors={self.factors}, "
            f"lr={self.learning_rate}, reg={self.regularization}, iter={self.iterations}"
        )
        return self

    # ── Inference ─────────────────────────────────────────────────────────────

    def score_candidates(self, user_id: int, candidate_items: np.ndarray) -> np.ndarray:
        """
        Score candidate items for a given user using learned embeddings.

        Score = dot product of user factor and item factor.
        Higher score → model predicts higher relative preference.

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
            "factors"      : self.factors,
            "learning_rate": self.learning_rate,
            "regularization": self.regularization,
            "iterations"   : self.iterations,
        }

    def __repr__(self) -> str:
        return (
            f"BPRModel(factors={self.factors}, lr={self.learning_rate}, "
            f"reg={self.regularization}, iter={self.iterations})"
        )
