from dataclasses import dataclass

@dataclass(frozen=True)
class ChurnPredictionConfig:
    horizon_days: int = 30
    snapshot_step_days: int = 30
    min_history_days: int = 90
    random_state: int = 42
    test_size: float = 0.20
    validation_size_within_trainval: float = 0.25
    cv_folds: int = 5
    outlier_lower_quantile: float = 0.01
    outlier_upper_quantile: float = 0.99
