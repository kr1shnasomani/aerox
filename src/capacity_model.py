import pandas as pd
import numpy as np
import logging
from lifelines import CoxPHFitter
from sklearn.model_selection import KFold
from sklearn.feature_selection import VarianceThreshold
import joblib

logger = logging.getLogger(__name__)

class CapacityModel:
    def __init__(self, penalizer=0.1, l1_ratio=0.0):
        # Increased penalizer slightly and set l1_ratio to 0 (L2 penalty is better for collinearity)
        # Using a stronger penalizer to handle multicollinearity
        self.cph = CoxPHFitter(penalizer=1.0, l1_ratio=0.0) 
        self.cols_to_drop = []
        
    def fit(self, train_df, duration_col='T', event_col='E'):
        logger.info(f"Fitting Cox PH Model (penalizer={self.cph.penalizer})...")
        
        # 1. Drop low variance columns
        selector = VarianceThreshold(threshold=0.01) # Drop near-constant
        # Select only numeric columns for variance check
        numeric_df = train_df.select_dtypes(include=[np.number])
        selector.fit(numeric_df)
        kept_indices = selector.get_support(indices=True)
        kept_cols = numeric_df.columns[kept_indices]
        dropped_low_var = list(set(numeric_df.columns) - set(kept_cols))
        
        if dropped_low_var:
            logger.warning(f"Dropping low variance columns: {dropped_low_var}")
            train_df = train_df.drop(columns=dropped_low_var)

        # 2. Check for correlation with duration and high pairwise correlation
        # Correlation with duration (target leakage check)
        corrs = train_df.corrwith(train_df[duration_col]).abs()
        high_corr_col_target = corrs[corrs > 0.95].index.tolist()
        if high_corr_col_target:
             # Don't drop the duration column itself!
            high_corr_col_target = [c for c in high_corr_col_target if c != duration_col]
            if high_corr_col_target:
                logger.warning(f"Dropping columns highly correlated with duration: {high_corr_col_target}")
                train_df = train_df.drop(columns=high_corr_col_target)

        # Correlation between features
        corr_matrix = train_df.drop(columns=[duration_col, event_col]).corr().abs()
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        to_drop_pairs = [column for column in upper.columns if any(upper[column] > 0.95)]
        
        if to_drop_pairs:
             logger.warning(f"Dropping columns due to high collinearity: {to_drop_pairs}")
             train_df = train_df.drop(columns=to_drop_pairs)

        self.cols_to_drop = dropped_low_var + high_corr_col_target + to_drop_pairs
        
        try:
            self.cph.fit(train_df, duration_col=duration_col, event_col=event_col, show_progress=True)
            logger.info("Cox Model fitted successfully.")
        except Exception as e:
            logger.error(f"Failed to fit Cox Model: {e}")
            raise

    def predict_survival(self, X, times=[30]):
        """Predict survival probability at specific times."""
        # Drop the columns we learned to drop during fit
        if hasattr(self, 'cols_to_drop') and self.cols_to_drop:
             X_clean = X.drop(columns=[c for c in self.cols_to_drop if c in X.columns])
        else:
             X_clean = X
             
        surv_funcs = self.cph.predict_survival_function(X_clean, times=times)
        # Transpose so rows are companies, cols are time points
        return surv_funcs.T

    def save(self, path):
        joblib.dump(self.cph, path)
        logger.info(f"Cox Model saved to {path}")

def tune_penalizer(train_df, duration_col='T', event_col='E', values=[0.01, 0.1, 1.0], folds=3):
    """
    Find best penalizer using Cross-Validation on C-index.
    """
    logger.info("Tuning Cox penalizer...")
    kf = KFold(n_splits=folds, shuffle=True, random_state=42)
    
    best_score = -1
    best_pen = values[0]
    
    for pen in values:
        scores = []
        for train_idx, val_idx in kf.split(train_df):
            train_fold = train_df.iloc[train_idx]
            val_fold = train_df.iloc[val_idx]
            
            model = CoxPHFitter(penalizer=pen, l1_ratio=1.0)
            try:
                model.fit(train_fold, duration_col=duration_col, event_col=event_col)
                sc = model.score(val_fold, scoring_method="concordance_index")
                scores.append(sc)
            except:
                scores.append(0) # Failed fit
                
        avg_score = np.mean(scores)
        logger.info(f"Penalizer {pen}: C-index = {avg_score:.4f}")
        
        if avg_score > best_score:
            best_score = avg_score
            best_pen = pen
            
    logger.info(f"Best penalizer: {best_pen} (C-index {best_score:.4f})")
    return best_pen
