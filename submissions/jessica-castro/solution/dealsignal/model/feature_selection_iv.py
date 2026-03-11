from typing import Dict, List

from utils.logger import get_logger

logger = get_logger(__name__)

IV_LABELS = [
    (0.3, "Strong"),
    (0.1, "Medium"),
    (0.02, "Weak"),
    (0.0, "Useless"),
]


def select_features_by_iv(iv_scores: Dict[str, float], threshold: float = 0.02) -> List[str]:
    selected = [f for f, iv in iv_scores.items() if iv >= threshold]
    log_iv_report(iv_scores, selected)
    return selected


def log_iv_report(iv_scores: Dict[str, float], selected: List[str]) -> None:
    logger.info("=" * 55)
    logger.info("%-30s %8s  %s", "Feature", "IV", "Status")
    logger.info("-" * 55)
    for feat, iv in sorted(iv_scores.items(), key=lambda x: -x[1]):
        label = next(lbl for thresh, lbl in IV_LABELS if iv >= thresh)
        status = "SELECTED" if feat in selected else "rejected"
        logger.info("%-30s %8.4f  [%s] %s", feat, iv, label, status)
    logger.info("=" * 55)
    logger.info("Selected %d / %d features (IV >= %.2f)", len(selected), len(iv_scores), 0.02)
