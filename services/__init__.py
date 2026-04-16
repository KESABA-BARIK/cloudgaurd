"""Services module for baseline engine, evaluation, and baseline comparison."""

from .baseline_engine import (
    Trie,
    mine_coarse_rules,
    refine_rules,
    evaluate_request,
    matches_pattern,
    parameterize,
)

from .evaluation import (
    extract_features,
    run_isolation_forest,
    split_data,
    evaluate_metrics,
    cross_validate,
)

from .baselines import (
    NaiveBaseline,
    compare_baselines,
    evaluate_baseline,
)

from .ablation import (
    run_ablation_study,
    evaluate_ablation_variant,
)

from .config_parser import ConfigParser

from .risk_scoring import RiskScoringEngine

from .remediation import RemediationEngine

from .autoencoder import AutoencoderAnomalyDetector

from .shap_explainer import SHAPExplainer

__all__ = [
    'Trie',
    'mine_coarse_rules',
    'refine_rules',
    'evaluate_request',
    'matches_pattern',
    'parameterize',
    'extract_features',
    'run_isolation_forest',
    'split_data',
    'evaluate_metrics',
    'cross_validate',
    'NaiveBaseline',
    'compare_baselines',
    'evaluate_baseline',
    'run_ablation_study',
    'evaluate_ablation_variant',
    'ConfigParser',
    'RiskScoringEngine',
    'RemediationEngine',
    'AutoencoderAnomalyDetector',
    'SHAPExplainer',
]
