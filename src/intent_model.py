import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv, GATConv, HeteroConv, Linear
import lightgbm as lgb
import xgboost as xgb
import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from imblearn.over_sampling import SMOTE
import optuna
import logging

logger = logging.getLogger(__name__)

class HeteroGNN(torch.nn.Module):
    def __init__(self, metadata, hidden_dims, out_channels, num_nodes_dict, embedding_dim=32, dropout=0.3):
        super().__init__()
        self.dropout_rate = dropout
        node_types, edge_types = metadata
        
        # 1. Embeddings for auxiliary nodes
        self.embeddings = torch.nn.ModuleDict()
        for nt in node_types:
            if nt != 'company' and nt in num_nodes_dict:
                self.embeddings[nt] = torch.nn.Embedding(num_nodes_dict[nt], embedding_dim)
        
        # 2. Convolutional Layers (GATConv)
        
        # Project initial features to hidden_dim[0]
        # We assume hidden_dims has at least one element
        initial_dim = hidden_dims[0]
        self.feature_proj = Linear(-1, initial_dim) 
        self.embedding_proj = Linear(embedding_dim, initial_dim)

        self.convs = torch.nn.ModuleList()
        self.bns = torch.nn.ModuleList()
        # Residual adjustments
        self.res_projs = torch.nn.ModuleList()

        prev_dim = initial_dim
        
        for hidden_dim in hidden_dims:
            # Graph Attention Layer
            conv = HeteroConv({
                edge_type: GATConv((-1, -1), hidden_dim, heads=2, concat=False, add_self_loops=False, dropout=0.1) 
                for edge_type in edge_types
            }, aggr='sum') 
            self.convs.append(conv)
            
            # Batch Normalization
            bn_dict = torch.nn.ModuleDict()
            for nt in node_types:
                bn_dict[nt] = torch.nn.BatchNorm1d(hidden_dim)
            self.bns.append(bn_dict)
            
            # Residual Projection if dimensions mismatch
            if prev_dim != hidden_dim:
                self.res_projs.append(Linear(prev_dim, hidden_dim))
            else:
                self.res_projs.append(torch.nn.Identity())
            
            prev_dim = hidden_dim
            
        self.lin = Linear(hidden_dims[-1], out_channels)
        
    def forward(self, x_dict, edge_index_dict):
        # 1. Project Inputs
        x_dict_curr = {}
        for nt, x in x_dict.items():
            if nt == 'company':
                x_dict_curr[nt] = self.feature_proj(x)
            elif nt in self.embeddings: # Embeddings
                emb = self.embeddings[nt](x)
                x_dict_curr[nt] = self.embedding_proj(emb)
        
        # 2. GNN Layers with Residuals
        for i, conv in enumerate(self.convs):
            x_in = x_dict_curr
            
            # Apply Convolution
            x_out = conv(x_in, edge_index_dict)
            
            # Apply BN + Activation + Dropout + Residual
            x_dict_next = {}
            for nt, x_val in x_out.items():
                # BN
                if nt in self.bns[i]:
                    x_val = self.bns[i][nt](x_val)
                
                # Activation
                x_val = F.relu(x_val)
                
                # Dropout
                x_val = F.dropout(x_val, p=self.dropout_rate, training=self.training)
                
                # Residual
                if nt in x_in:
                    res = self.res_projs[i](x_in[nt])
                    if res.shape == x_val.shape:
                        x_val = x_val + res
                
                x_dict_next[nt] = x_val
            
            x_dict_curr = x_dict_next
            
        # 3. Final Prediction (only for companies)
        return self.lin(x_dict_curr['company'])


class LightGBMIntentModel:
    """LightGBM-based Intent Model with SMOTE and Optuna tuning."""
    
    def __init__(self, config):
        self.config = config
        self.model = None
        self.best_params = None
        self.use_smote = config.get('use_smote', True)
        self.tune_hyperparams = config.get('tune_hyperparams', True)
        
    def train(self, X_train, y_train, X_val, y_val):
        """Train LightGBM with optional SMOTE and Optuna tuning."""
        logger.info(f"Training LightGBM Intent Model (SMOTE={self.use_smote}, Tuning={self.tune_hyperparams})")
        
        # Apply SMOTE if enabled
        if self.use_smote and y_train.sum() < len(y_train) * 0.5:
            logger.info(f"Original class distribution: {np.bincount(y_train.astype(int))}")
            smote = SMOTE(random_state=self.config.get('random_seed', 42), k_neighbors=5)
            X_train, y_train = smote.fit_resample(X_train, y_train)
            logger.info(f"After SMOTE: {np.bincount(y_train.astype(int))}")
        
        # Hyperparameter tuning with Optuna
        if self.tune_hyperparams:
            logger.info("Starting Optuna hyperparameter tuning...")
            self.best_params = self._tune_hyperparameters(X_train, y_train, X_val, y_val)
        else:
            # Default parameters
            self.best_params = {
                'num_leaves': self.config.get('num_leaves', 31),
                'max_depth': self.config.get('max_depth', -1),
                'learning_rate': self.config.get('learning_rate', 0.05),
                'n_estimators': self.config.get('n_estimators', 500),
                'min_child_samples': self.config.get('min_child_samples', 20),
                'subsample': self.config.get('subsample', 0.8),
                'colsample_bytree': self.config.get('colsample_bytree', 0.8),
                'reg_alpha': self.config.get('reg_alpha', 0.1),
                'reg_lambda': self.config.get('reg_lambda', 0.1),
            }
        
        # Train final model
        logger.info(f"Training final model with params: {self.best_params}")
        
        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
        
        # Calculate scale_pos_weight for class imbalance
        pos_count = y_train.sum()
        neg_count = len(y_train) - pos_count
        scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1.0
        
        params = {
            **self.best_params,
            'objective': 'binary',
            'metric': 'auc',
            'boosting_type': 'gbdt',
            'verbose': -1,
            'scale_pos_weight': scale_pos_weight,
            'random_state': self.config.get('random_seed', 42),
        }
        
        self.model = lgb.train(
            params,
            train_data,
            num_boost_round=self.best_params.get('n_estimators', 500),
            valid_sets=[train_data, val_data],
            valid_names=['train', 'val'],
            callbacks=[
                lgb.early_stopping(stopping_rounds=50, verbose=False),
                lgb.log_evaluation(period=50)
            ]
        )
        
        logger.info(f"Training complete. Best iteration: {self.model.best_iteration}")
        return self
    
    def _tune_hyperparameters(self, X_train, y_train, X_val, y_val):
        """Tune hyperparameters using Optuna."""
        
        def objective(trial):
            params = {
                'num_leaves': trial.suggest_int('num_leaves', 20, 150),
                'max_depth': trial.suggest_int('max_depth', 3, 12),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
                'min_child_samples': trial.suggest_int('min_child_samples', 5, 50),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'reg_alpha': trial.suggest_float('reg_alpha', 1e-3, 10.0, log=True),
                'reg_lambda': trial.suggest_float('reg_lambda', 1e-3, 10.0, log=True),
            }
            
            train_data = lgb.Dataset(X_train, label=y_train)
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
            
            pos_count = y_train.sum()
            neg_count = len(y_train) - pos_count
            scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1.0
            
            lgb_params = {
                **params,
                'objective': 'binary',
                'metric': 'auc',
                'boosting_type': 'gbdt',
                'verbose': -1,
                'scale_pos_weight': scale_pos_weight,
                'random_state': self.config.get('random_seed', 42),
            }
            
            model = lgb.train(
                lgb_params,
                train_data,
                num_boost_round=params['n_estimators'],
                valid_sets=[val_data],
                callbacks=[
                    lgb.early_stopping(stopping_rounds=30, verbose=False)
                ]
            )
            
            y_pred = model.predict(X_val)
            auc = roc_auc_score(y_val, y_pred)
            
            return auc
        
        study = optuna.create_study(
            direction='maximize',
            sampler=optuna.samplers.TPESampler(seed=self.config.get('random_seed', 42))
        )
        
        n_trials = self.config.get('optuna_trials', 50)
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        logger.info(f"Optuna tuning complete. Best AUC: {study.best_value:.4f}")
        logger.info(f"Best parameters: {study.best_params}")
        
        return study.best_params
    
    def predict(self, X):
        """Predict probabilities for the positive class."""
        if self.model is None:
            raise ValueError("Model not trained yet. Call train() first.")
        return self.model.predict(X)
    
    def get_feature_importance(self, feature_names=None):
        """Get feature importance from the trained model."""
        if self.model is None:
            raise ValueError("Model not trained yet.")
        
        importance = self.model.feature_importance(importance_type='gain')
        
        if feature_names is not None:
            return dict(zip(feature_names, importance))
        return importance


class EnsembleIntentModel:
    """
    Ensemble of LightGBM, XGBoost, and CatBoost with stacking for improved recall.
    Uses focal loss weighting and optimized for recall metric.
    """
    
    def __init__(self, config):
        self.config = config
        self.models = {}
        self.meta_model = None
        self.use_smote = config.get('use_smote', True)
        self.focal_gamma = config.get('focal_gamma', 2.0)
        self.recall_weight = config.get('recall_weight', 2.0)  # Higher = prioritize recall
        
    def train(self, X_train, y_train, X_val, y_val):
        """Train ensemble with multiple base learners and a meta-learner."""
        logger.info(f"Training Ensemble Intent Model (SMOTE={self.use_smote}, Recall-Optimized)")
        
        # Apply SMOTE if enabled
        if self.use_smote and y_train.sum() < len(y_train) * 0.5:
            logger.info(f"Original class distribution: {np.bincount(y_train.astype(int))}")
            smote = SMOTE(random_state=self.config.get('random_seed', 42), k_neighbors=5)
            X_train_sm, y_train_sm = smote.fit_resample(X_train, y_train)
            logger.info(f"After SMOTE: {np.bincount(y_train_sm.astype(int))}")
        else:
            X_train_sm, y_train_sm = X_train, y_train
        
        # Calculate class weights for focal loss effect
        pos_count = y_train_sm.sum()
        neg_count = len(y_train_sm) - pos_count
        scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1.0
        
        # Increase positive weight to boost recall
        scale_pos_weight *= self.recall_weight
        
        # === 1. Train LightGBM ===
        logger.info("Training LightGBM base learner...")
        train_data = lgb.Dataset(X_train_sm, label=y_train_sm)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
        
        lgb_params = {
            'objective': 'binary',
            'metric': 'auc',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'max_depth': 6,
            'learning_rate': 0.05,
            'scale_pos_weight': scale_pos_weight,
            'min_child_samples': 10,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'reg_alpha': 0.1,
            'reg_lambda': 0.1,
            'verbose': -1,
            'random_state': self.config.get('random_seed', 42),
        }
        
        self.models['lgb'] = lgb.train(
            lgb_params,
            train_data,
            num_boost_round=300,
            valid_sets=[val_data],
            callbacks=[
                lgb.early_stopping(stopping_rounds=30, verbose=False),
                lgb.log_evaluation(period=0)
            ]
        )
        
        # === 2. Train XGBoost ===
        logger.info("Training XGBoost base learner...")
        dtrain = xgb.DMatrix(X_train_sm, label=y_train_sm)
        dval = xgb.DMatrix(X_val, label=y_val)
        
        xgb_params = {
            'objective': 'binary:logistic',
            'eval_metric': 'auc',
            'max_depth': 6,
            'learning_rate': 0.05,
            'scale_pos_weight': scale_pos_weight,
            'min_child_weight': 5,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'reg_alpha': 0.1,
            'reg_lambda': 0.1,
            'seed': self.config.get('random_seed', 42),
        }
        
        self.models['xgb'] = xgb.train(
            xgb_params,
            dtrain,
            num_boost_round=300,
            evals=[(dval, 'val')],
            early_stopping_rounds=30,
            verbose_eval=False
        )
        
        # === 3. Meta-learner (Stacking) ===
        logger.info("Training meta-learner (Logistic Regression)...")
        
        # Get base predictions on train set (for meta-training)
        train_meta_features = self._get_base_predictions(X_train_sm)
        
        # Get base predictions on validation set
        val_meta_features = self._get_base_predictions(X_val)
        
        # Train logistic regression meta-model
        self.meta_model = LogisticRegression(
            class_weight={0: 1, 1: self.recall_weight},  # Boost positive class
            random_state=self.config.get('random_seed', 42),
            max_iter=1000
        )
        self.meta_model.fit(train_meta_features, y_train_sm)
        
        # Evaluate ensemble
        val_preds = self.predict(X_val)
        val_auc = roc_auc_score(y_val, val_preds)
        logger.info(f"Ensemble Validation AUC: {val_auc:.4f}")
        
        return self
    
    def _get_base_predictions(self, X):
        """Get predictions from all base models."""
        preds = []
        
        # LightGBM
        preds.append(self.models['lgb'].predict(X))
        
        # XGBoost
        dmatrix = xgb.DMatrix(X)
        preds.append(self.models['xgb'].predict(dmatrix))
        
        return np.column_stack(preds)
    
    def predict(self, X):
        """Predict probabilities using ensemble."""
        if not self.models or self.meta_model is None:
            raise ValueError("Models not trained yet. Call train() first.")
        
        # Get base model predictions
        base_preds = self._get_base_predictions(X)
        
        # Meta-model prediction
        ensemble_preds = self.meta_model.predict_proba(base_preds)[:, 1]
        
        return ensemble_preds
    
    def get_feature_importance(self, feature_names=None):
        """Get average feature importance across base models."""
        if not self.models:
            raise ValueError("Models not trained yet.")
        
        # Get LightGBM importance
        lgb_importance = self.models['lgb'].feature_importance(importance_type='gain')
        
        # Get XGBoost importance
        xgb_importance = self.models['xgb'].get_score(importance_type='gain')
        xgb_importance_array = np.array([xgb_importance.get(f'f{i}', 0) for i in range(len(lgb_importance))])
        
        # Average importance
        avg_importance = (lgb_importance + xgb_importance_array) / 2
        
        if feature_names is not None:
            return dict(zip(feature_names, avg_importance))
        return avg_importance
