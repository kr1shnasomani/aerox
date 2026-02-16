import pandas as pd
import numpy as np
import logging
from sklearn.metrics import (
    roc_auc_score, f1_score, precision_score, recall_score, confusion_matrix,
    average_precision_score, precision_recall_curve, auc, log_loss,
    brier_score_loss, accuracy_score, balanced_accuracy_score,
    fbeta_score, matthews_corrcoef, cohen_kappa_score
)
from lifelines.utils import concordance_index
import json
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

def find_optimal_threshold(y_true, y_scores, mode='f05'):
    """
    Find optimal threshold based on specified mode.
    
    Args:
        y_true: True labels
        y_scores: Predicted probabilities
        mode: 'f05' (precision-focused), 'f2' (recall-focused), or 'f1' (balanced)
    
    Returns:
        float: Optimal threshold
    """
    if mode == 'f2' or mode == 'recall':
        return find_recall_optimal_threshold(y_true, y_scores)
    elif mode == 'f1':
        return find_balanced_threshold(y_true, y_scores)
    else:
        return find_precision_optimal_threshold(y_true, y_scores)

def find_recall_optimal_threshold(y_true, y_scores):
    """
    Find optimal threshold maximizing F2 score (favoring recall).
    Prioritizes catching fraudsters even at cost of some false positives.
    """
    thresholds = np.arange(0.1, 0.95, 0.01)
    best_thresh = 0.5
    best_f2 = 0
    
    for t in thresholds:
        pred = (y_scores >= t).astype(int)
        # F2 = (5 * P * R) / (4 * P + R) - weights recall 4x more than precision
        p = precision_score(y_true, pred, zero_division=0)
        r = recall_score(y_true, pred, zero_division=0)
        
        # Require minimum precision of 0.50 to avoid too many false positives
        if p < 0.50:
            continue
            
        f2 = (5 * p * r) / (4 * p + r + 1e-10)
        
        if f2 > best_f2:
            best_f2 = f2
            best_thresh = t
    
    logger.info(f"Recall-optimized threshold: {best_thresh:.4f} (F2={best_f2:.4f})")
    return float(best_thresh)

def find_balanced_threshold(y_true, y_scores):
    """Find threshold maximizing F1 score (balanced precision-recall)."""
    thresholds = np.arange(0.1, 0.95, 0.01)
    best_thresh = 0.5
    best_f1 = 0
    
    for t in thresholds:
        pred = (y_scores >= t).astype(int)
        f1 = f1_score(y_true, pred, zero_division=0)
        
        if f1 > best_f1:
            best_f1 = f1
            best_thresh = t
    
    logger.info(f"Balanced threshold: {best_thresh:.4f} (F1={best_f1:.4f})")
    return float(best_thresh)

def find_precision_optimal_threshold(y_true, y_scores):
    """
    Find optimal threshold maximizing F0.5 score (favoring precision).
    Original implementation.
    """
    thresholds = np.arange(0.1, 0.95, 0.01)
    best_thresh = 0.5
    best_f05 = 0
    
    # Calculate Precision-Recall curve to find safe threshold options
    precision, recall, pr_thresholds = precision_recall_curve(y_true, y_scores)
    
    # Find thresholds where Precision >= 0.85
    # Add a minimum recall constraint to avoid picking thresholds with 1 sample
    mask = (precision[:-1] >= 0.85) & (recall[:-1] > 0.10) 
    high_prec_indices = np.where(mask)[0]
    
    if len(high_prec_indices) > 0:
        # If we can hit 0.85 precision with decent recall, optimize for F0.5 within that region
        # Or just pick the one with best recall
        best_idx = high_prec_indices[np.argmax(recall[high_prec_indices])]
        best_thresh = pr_thresholds[best_idx]
        logger.info(f"Targeting Precision >= 0.85 with Recall > 0.10. Selected threshold: {best_thresh:.4f}")
        return float(best_thresh)

    # Fallback to F0.5 optimization if 0.85 precision is unreachable
    for t in thresholds:
        pred = (y_scores >= t).astype(int)
        # F0.5 = (1.25 * P * R) / (0.25 * P + R)
        p = precision_score(y_true, pred, zero_division=0)
        r = recall_score(y_true, pred, zero_division=0)
        f05 = (1.25 * p * r) / (0.25 * p + r + 1e-10)
        
        if f05 > best_f05:
            best_f05 = f05
            best_thresh = t
            
    logger.info(f"Optimal Threshold (F0.5) found: {best_thresh:.2f} (Score: {best_f05:.4f})")
    return float(best_thresh)

def evaluate_intent(y_true, y_pred_score, threshold=0.5):
    """
    Evaluate Intent Model (Binary Classification).
    """
    try:
        y_pred = (y_pred_score >= threshold).astype(int)
        
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        npv = tn / (tn + fn) if (tn + fn) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0
        
        metrics = {
            # Probabilistic / Ranking Metrics
            "roc_auc": float(roc_auc_score(y_true, y_pred_score)),
            "pr_auc": float(average_precision_score(y_true, y_pred_score)),
            "log_loss": float(log_loss(y_true, np.clip(y_pred_score, 1e-7, 1-1e-7))),
            "brier_score": float(brier_score_loss(y_true, y_pred_score)),
            
            # Threshold-based Classification Metrics
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
            "f2_score": float(fbeta_score(y_true, y_pred, beta=2, zero_division=0)),
            "f0.5_score": float(fbeta_score(y_true, y_pred, beta=0.5, zero_division=0)),
            "specificity": float(specificity),
            "npv": float(npv),
            "fpr": float(fpr),
            "fnr": float(fnr),
            
            # Correlation-based Metrics
            "mcc": float(matthews_corrcoef(y_true, y_pred)),
            "cohen_kappa": float(cohen_kappa_score(y_true, y_pred)),
            
            # Confusion Matrix
            "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
            "threshold_used": float(threshold)
        }
        
        logger.info(f"Intent Model Metrics: ROC-AUC={metrics['roc_auc']:.4f}, PR-AUC={metrics['pr_auc']:.4f}, F1={metrics['f1_score']:.4f}, Precision={metrics['precision']:.4f}, Recall={metrics['recall']:.4f}")
        return metrics
    except Exception as e:
        logger.error(f"Intent Eval failed: {e}")
        return {}

def evaluate_capacity(model, test_df, duration_col='T', event_col='E'):
    """
    Evaluate Capacity Model (Survival Analysis) with comprehensive metrics.
    """
    try:
        # 1. Concordance Index (Harrell's C-Index)
        c_index = model.score(test_df, scoring_method="concordance_index")
        
        # 2. Log-Likelihood (partial, from the model fit)
        log_likelihood = float(model.log_likelihood_)
        
        # 3. AIC (Akaike Information Criterion) — lower is better
        aic = float(model.AIC_partial_)
        
        # 4. Number of significant covariates (p < 0.05)
        summary = model.summary
        n_significant = int((summary['p'] < 0.05).sum())
        n_covariates = len(summary)
        
        # 5. Proportional Hazards Test (Schoenfeld residuals)
        try:
            ph_test = model.check_assumptions(test_df, p_value_threshold=0.05, show_plots=False)
            ph_violations = 0  # If no exception, all pass
        except Exception:
            ph_violations = -1  # Could not compute or has violations
            
        # 6. Median Survival Prediction Quality
        # Predict risk scores and compare ranking with actual durations
        risk_scores = model.predict_partial_hazard(test_df).values.flatten()
        actual_T = test_df[duration_col].values
        actual_E = test_df[event_col].values
        
        # Re-compute C-index from raw predictions for validation
        c_index_manual = float(concordance_index(actual_T, -risk_scores, actual_E))
        
        # 7. Log-Rank style: median predicted vs actual
        median_risk = float(np.median(risk_scores))
        high_risk = risk_scores >= median_risk
        low_risk = risk_scores < median_risk
        
        median_T_high_risk = float(np.median(actual_T[high_risk])) if high_risk.sum() > 0 else 0
        median_T_low_risk = float(np.median(actual_T[low_risk])) if low_risk.sum() > 0 else 0
        risk_separation_ratio = median_T_low_risk / (median_T_high_risk + 1e-6)
        
        metrics = {
            "c_index": float(c_index),
            "c_index_manual": c_index_manual,
            "log_likelihood_partial": log_likelihood,
            "aic_partial": aic,
            "n_covariates": n_covariates,
            "n_significant_covariates": n_significant,
            "median_survival_high_risk": median_T_high_risk,
            "median_survival_low_risk": median_T_low_risk,
            "risk_separation_ratio": float(risk_separation_ratio)
        }
        
        logger.info(f"Capacity Model: C-Index={c_index:.4f}, AIC={aic:.2f}, Significant Covariates={n_significant}/{n_covariates}")
        return metrics
    except Exception as e:
        logger.error(f"Capacity Eval failed: {e}")
        # Fallback: at least return c_index if possible
        try:
            c_index = model.score(test_df, scoring_method="concordance_index")
            return {"c_index": float(c_index)}
        except:
            return {}

def save_report(metrics_intent, metrics_capacity, filepath):
    report = {
        "intent_model": metrics_intent,
        "capacity_model": metrics_capacity
    }
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=4)
    logger.info(f"Report saved to {filepath}")
