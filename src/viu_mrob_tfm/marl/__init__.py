"""Lightweight MARL baselines for warehouse coalition experiments."""

from viu_mrob_tfm.marl.neural_policy import (
    DEFAULT_HIDDEN_DIM,
    NeuralPolicyParams,
    initial_neural_vector,
    neural_param_size,
    score_neural_features,
    unpack_neural_vector,
)
from viu_mrob_tfm.marl.shared_policy import (
    MARL_CTDE_FEATURE_NAMES,
    DEFAULT_MARL_CTDE_WEIGHTS,
    build_global_features,
    build_pair_features,
    coerce_policy_weights,
)

__all__ = [
    "DEFAULT_HIDDEN_DIM",
    "DEFAULT_MARL_CTDE_WEIGHTS",
    "MARL_CTDE_FEATURE_NAMES",
    "NeuralPolicyParams",
    "build_global_features",
    "build_pair_features",
    "coerce_policy_weights",
    "initial_neural_vector",
    "neural_param_size",
    "score_neural_features",
    "unpack_neural_vector",
]
