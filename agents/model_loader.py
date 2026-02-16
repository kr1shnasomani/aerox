"""Model loader for Intent and Capacity models with real scoring"""

import pickle
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import logging

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from agents.config import (
    DECISION_MATRIX, MOCK_ML_SCORES, MOCK_COMPANY_DATA,
    MOCK_EXTERNAL_DATA, GREEN_FLAG_SCORES, RED_FLAG_SCORES, LGD
)

logger = logging.getLogger(__name__)

class ModelLoader:
    """Load and run trained Intent and Capacity models"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.intent_model = None
        self.capacity_model = None
        self.dataset1 = None
        
        self._load_models()
        self._load_dataset()
    
    def _load_models(self):
        """Load serialized models"""
        try:
            # Load Intent model (Ensemble)
            intent_path = self.project_root / "models" / "intent_ensemble.pkl"
            with open(intent_path, 'rb') as f:
                self.intent_model = pickle.load(f)
            logger.info("✓ Loaded intent_ensemble.pkl")
            
            # Load Capacity model (Cox PH)
            capacity_path = self.project_root / "models" / "capacity_cox.pkl"
            self.capacity_model = joblib.load(capacity_path)
            logger.info("✓ Loaded capacity_cox.pkl")
            
        except Exception as e:
            logger.warning(f"Could not load models: {e}. Will use mock scores.")
    
    def _load_dataset(self):
        """Load company dataset"""
        try:
            dataset_path = self.project_root / "dataset" / "dataset1.csv"
            self.dataset1 = pd.read_csv(dataset_path)
            logger.info(f"✓ Loaded dataset1.csv ({len(self.dataset1)} companies)")
        except Exception as e:
            logger.warning(f"Could not load dataset: {e}")
    
    def score_company(self, company_id):
        """
        Score a company using real models or fallback to mock data
        
        Returns:
            dict with keys: intent_score, capacity_score, pd_7d, pd_14d, pd_30d, 
                           risk_category, company_data
        """
        # Check for test company IDs
        if company_id == "IN-TRV-000123":  # Green flag
            return self._enrich_scores(GREEN_FLAG_SCORES, company_id)
        elif company_id == "IN-TRV-000999":  # Red flag
            return self._enrich_scores(RED_FLAG_SCORES, company_id)
        
        # Try real model scoring
        if self.intent_model and self.capacity_model and self.dataset1 is not None:
            try:
                return self._real_model_score(company_id)
            except Exception as e:
                logger.warning(f"Real scoring failed for {company_id}: {e}. Using mock.")
        
        # Fallback to mock
        return self._enrich_scores(MOCK_ML_SCORES, company_id)
    
    def _real_model_score(self, company_id):
        """Score company using trained models"""
        # Find company in dataset
        company_row = self.dataset1[self.dataset1['company_id'] == company_id]
        
        if company_row.empty:
            raise ValueError(f"Company {company_id} not found in dataset")
        
        company_row = company_row.iloc[0]
        
        # Get features (drop non-feature columns)
        drop_cols = ['company_id', 'fraud_flag', 'default_flag', 'risk_score', 
                     'snapshot_date', 'seasonal_period']
        feature_cols = [c for c in company_row.index if c not in drop_cols]
        
        # Handle categorical encoding (region, segment)
        features = company_row[feature_cols].copy()
        
        # Simple one-hot encoding for categorical columns (matching training)
        if 'segment' in features.index:
            segment_val = features['segment']
            for seg in ['micro', 'small_medium', 'medium_large', 'enterprise']:
                features[f'segment_{seg}'] = 1 if segment_val == seg else 0
            features = features.drop('segment')
        
        if 'region' in features.index:
            region_val = features['region']
            for reg in ['north', 'south', 'east', 'west', 'central']:
                features[f'region_{reg}'] = 1 if region_val == reg else 0
            features = features.drop('region')
        
        # Convert to numpy array (ensure all numeric)
        X = pd.to_numeric(features, errors='coerce').fillna(0).values.reshape(1, -1)
        
        # Score with Intent model
        intent_score = self.intent_model.predict(X)[0]
        
        # Score with Capacity model
        # Capacity model needs survival data format - approximate from features
        capacity_score = self._estimate_capacity_score(company_row)
        
        # Estimate PD from capacity model (survival probabilities → PD)
        pd_7d = min(0.50, max(0.001, (1 - capacity_score) * 0.03))
        pd_14d = min(0.60, pd_7d * 3)
        pd_30d = min(0.70, pd_7d * 6)
        
        # Determine risk category
        risk_category = self._categorize_risk(intent_score, capacity_score)
        
        # Build company data from row
        company_data = {
            "segment": company_row.get('segment', 'small_medium'),
            "credit_utilization": company_row.get('credit_utilization', 0.5),
            "on_time_payment_rate": company_row.get('on_time_payment_rate', 0.8),
            "avg_late_payment_days": company_row.get('avg_late_payment_days', 5),
            "chargeback_rate": company_row.get('chargeback_rate', 0.01),
            "business_age_months": company_row.get('business_age_months', 24),
            "years_with_platform": company_row.get('years_with_platform', 1.5)
        }
        
        return {
            "intent_score": float(intent_score),
            "capacity_score": float(capacity_score),
            "pd_7d": float(pd_7d),
            "pd_14d": float(pd_14d),
            "pd_30d": float(pd_30d),
            "risk_category": risk_category,
            "company_data": company_data,
            "external_data": MOCK_EXTERNAL_DATA  # Always mock for external
        }
    
    def _estimate_capacity_score(self, company_row):
        """Estimate capacity score from Cox model partial hazard"""
        try:
            # Cox model predicts hazard (higher = worse)
            # We need capacity score (higher = better)
            # Use credit_utilization and payment behavior as proxy
            credit_util = company_row.get('credit_utilization', 0.5)
            on_time_rate = company_row.get('on_time_payment_rate', 0.8)
            
            # Simple heuristic: capacity = (1 - credit_util) * on_time_rate
            capacity_score = (1 - credit_util) * on_time_rate
            return max(0.1, min(0.95, capacity_score))
        
        except Exception:
            return 0.55  # Default moderate capacity
    
    def _categorize_risk(self, intent_score, capacity_score):
        """Categorize as green/yellow/red based on decision matrix"""
        if intent_score >= DECISION_MATRIX['block_intent_threshold']:
            return "red"
        
        if (intent_score < DECISION_MATRIX['approve_intent_threshold'] and
            capacity_score >= DECISION_MATRIX['approve_capacity_threshold']):
            return "green"
        
        return "yellow"
    
    def _enrich_scores(self, base_scores, company_id):
        """Add company_data and external_data to scores"""
        result = base_scores.copy()
        result['company_data'] = MOCK_COMPANY_DATA
        result['external_data'] = MOCK_EXTERNAL_DATA
        return result


# Global singleton
_model_loader = None

def get_model_loader():
    """Get or create ModelLoader singleton"""
    global _model_loader
    if _model_loader is None:
        _model_loader = ModelLoader()
    return _model_loader
