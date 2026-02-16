import argparse
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
import torch
import yaml
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.preprocessing import RobustScaler
from torch.optim.lr_scheduler import ReduceLROnPlateau
import torch.nn.functional as F

# Add src to python path
sys.path.append(str(Path(__file__).parent / "src"))

from src.utils import setup_logger, load_config, set_seed
from src.data_loader import load_datasets, validate_referential_integrity, validate_data_quality
from src.feature_engineering import engineer_features
from src.graph_builder import GraphBuilder
from src.survival_data import prepare_survival_data
from src.intent_model import HeteroGNN, LightGBMIntentModel, EnsembleIntentModel
from src.capacity_model import CapacityModel, tune_penalizer
from src.evaluate import evaluate_intent, evaluate_capacity, save_report, find_optimal_threshold

def main():
    # 1. Setup
    logger = setup_logger()
    logger.info("Starting AEROX Model Training Pipeline")
    
    try:
        config = load_config()
        logger.info("Configuration loaded successfully")
        
        set_seed(config['data']['random_seed'])
        
        # 2. Data Loading
        logger.info("Phase 2: Data Loading & Validation")
        df1, df2, df3 = load_datasets(config)
        
        validate_referential_integrity(df1, df2, df3)
        df1 = validate_data_quality(df1, df2, df3)
        
        # 3. Feature Engineering
        logger.info("Phase 3: Feature Engineering")
        features_df = engineer_features(df1, df2, df3, config)
        
        # 4. Stratified Split (BEFORE Scaling)
        logger.info("Phase 4: Stratified Splitting")
        target_col = 'fraud_flag'
        labels = df1.set_index('company_id').loc[features_df['company_id'], target_col]
        
        sss_test = StratifiedShuffleSplit(n_splits=1, test_size=config['data']['test_ratio'], random_state=config['data']['random_seed'])
        train_val_idx, test_idx = next(sss_test.split(features_df, labels))
        
        train_val_df = features_df.iloc[train_val_idx]
        train_val_labels = labels.iloc[train_val_idx]
        
        val_ratio_adjusted = config['data']['val_ratio'] / (1 - config['data']['test_ratio'])
        sss_val = StratifiedShuffleSplit(n_splits=1, test_size=val_ratio_adjusted, random_state=config['data']['random_seed'])
        train_idx_internal, val_idx_internal = next(sss_val.split(train_val_df, train_val_labels))
        
        train_idx = train_val_idx[train_idx_internal]
        val_idx = train_val_idx[val_idx_internal]
        
        train_ids = features_df.iloc[train_idx]['company_id'].values
        val_ids = features_df.iloc[val_idx]['company_id'].values
        test_ids = features_df.iloc[test_idx]['company_id'].values
        
        logger.info(f"Split: Train={len(train_ids)}, Val={len(val_ids)}, Test={len(test_ids)}")

        # 5. Scaling (Fit on Train, Transform All)
        logger.info("Phase 5: Scaling Features")
        numeric_cols = features_df.select_dtypes(include=np.number).columns.tolist()
        scale_cols = [c for c in numeric_cols if c != 'company_id']
        
        # Ensure float dtype to avoid pandas warnings/errors on scaling
        features_df[scale_cols] = features_df[scale_cols].astype(float)
        
        scaler = RobustScaler()
        scaler.fit(features_df.loc[train_idx, scale_cols])
        features_df.loc[:, scale_cols] = scaler.transform(features_df.loc[:, scale_cols])

        # 6. Graph Construction (Skip if using LightGBM/Ensemble)
        model_type = config['intent_model'].get('type', 'lightgbm')
        
        if model_type in ['heterogeneous_gat', 'gnn']:
            logger.info("Phase 6: Graph Construction")
            graph_builder = GraphBuilder(df3, features_df)
            hetero_data = graph_builder.build()
            
            def get_graph_indices(ids, mapping):
                return torch.tensor([mapping[x] for x in ids if x in mapping], dtype=torch.long)
            
            train_mask = get_graph_indices(train_ids, graph_builder.company_map)
            val_mask = get_graph_indices(val_ids, graph_builder.company_map)
            test_mask = get_graph_indices(test_ids, graph_builder.company_map)
        else:
            logger.info(f"Phase 6: Skipping graph construction ({model_type.upper()} mode)")
            hetero_data = None
            graph_builder = None
        
        # 7. Model 1 (Intent) - Train
        logger.info(f"Phase 7: Training Intent Score Model ({model_type.upper()})")
        
        if model_type in ['lightgbm', 'ensemble']:
            # Prepare tabular data
            feature_cols = [c for c in features_df.columns if c != 'company_id']
            X_train = features_df.iloc[train_idx][feature_cols].values
            X_val = features_df.iloc[val_idx][feature_cols].values
            X_test = features_df.iloc[test_idx][feature_cols].values
            
            y_train = labels.iloc[train_idx].values.astype(int)
            y_val = labels.iloc[val_idx].values.astype(int)
            y_test = labels.iloc[test_idx].values.astype(int)
            
            # Train model (LightGBM or Ensemble)
            if model_type == 'ensemble':
                intent_model = EnsembleIntentModel(config['intent_model'])
            else:
                intent_model = LightGBMIntentModel(config['intent_model'])
            
            intent_model.train(X_train, y_train, X_val, y_val)
            
            # Get predictions
            val_probs = intent_model.predict(X_val)
            test_probs = intent_model.predict(X_test)
            
            # Optimize threshold on validation set (use recall-focused mode for ensemble)
            threshold_mode = config['intent_model'].get('threshold_mode', 'f05')
            best_threshold = find_optimal_threshold(y_val, val_probs, mode=threshold_mode)
            
            # Create intent scores for all companies
            all_X = features_df[feature_cols].values
            intent_scores = intent_model.predict(all_X)
            score_series = pd.Series(intent_scores, index=features_df['company_id'].values)
            
            # Log feature importance
            feature_importance = intent_model.get_feature_importance(feature_cols)
            top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
            logger.info("Top 10 Important Features:")
            for feat, importance in top_features:
                logger.info(f"  {feat}: {importance:.2f}")
            
        else:  # GNN mode
            targets = pd.DataFrame({'company_id': [c for c, i in sorted(graph_builder.company_map.items(), key=lambda x: x[1])]})
            targets = targets.merge(df1[['company_id', 'fraud_flag']], on='company_id', how='left')
            target_tensor = torch.tensor(targets['fraud_flag'].values, dtype=torch.float)
            hetero_data['company'].y = target_tensor
            
            num_nodes_dict = {
                nt: hetero_data[nt].x.size(0) if hasattr(hetero_data[nt], 'x') else hetero_data[nt].num_nodes 
                for nt in hetero_data.node_types
            }
            
            gnn_cfg = config['intent_model']
            model_gnn = HeteroGNN(
                metadata=hetero_data.metadata(), 
                hidden_dims=gnn_cfg['hidden_dims'], 
                out_channels=1, 
                num_nodes_dict=num_nodes_dict,
                embedding_dim=32,
                dropout=gnn_cfg.get('dropout', 0.3)
            )
            
            pos_weight = torch.tensor([gnn_cfg.get('positive_class_weight', 3.5)])
            criterion = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
            optimizer = torch.optim.Adam(model_gnn.parameters(), lr=gnn_cfg['learning_rate'], weight_decay=gnn_cfg.get('weight_decay', 0.0001))
            scheduler = ReduceLROnPlateau(optimizer, mode='max', factor=gnn_cfg.get('lr_scheduler_factor', 0.5), patience=gnn_cfg.get('lr_scheduler_patience', 10), min_lr=1e-5)
            
            best_val_score = 0
            patience_counter = 0
            best_model_state = None
            
            for epoch in range(gnn_cfg['epochs']):
                model_gnn.train()
                optimizer.zero_grad()
                out = model_gnn(hetero_data.x_dict, hetero_data.edge_index_dict)
                loss = criterion(out[train_mask].squeeze(), hetero_data['company'].y[train_mask])
                loss.backward()
                optimizer.step()
                
                model_gnn.eval()
                with torch.no_grad():
                    full_out = model_gnn(hetero_data.x_dict, hetero_data.edge_index_dict).squeeze()
                    val_probs = torch.sigmoid(full_out[val_mask])
                    val_targets = hetero_data['company'].y[val_mask]
                    try:
                        val_auc = evaluate_intent(val_targets.cpu().numpy(), val_probs.cpu().numpy())['roc_auc']
                    except: val_auc = 0.5
                
                scheduler.step(val_auc)
                if val_auc > best_val_score:
                    best_val_score = val_auc
                    best_model_state = model_gnn.state_dict()
                    patience_counter = 0
                else:
                    patience_counter += 1
                    
                if epoch % 10 == 0:
                    logger.info(f"Epoch {epoch}, Loss: {loss.item():.4f}, Val AUC: {val_auc:.4f}")
                if patience_counter >= gnn_cfg.get('early_stopping_patience', 20):
                    logger.info(f"Early stopping at epoch {epoch}")
                    break
            
            if best_model_state: model_gnn.load_state_dict(best_model_state)
            
            # Optimize Threshold
            model_gnn.eval()
            with torch.no_grad():
                full_out = model_gnn(hetero_data.x_dict, hetero_data.edge_index_dict).squeeze()
                val_probs = torch.sigmoid(full_out[val_mask]).cpu().numpy()
                val_y = hetero_data['company'].y[val_mask].cpu().numpy()
                best_threshold = find_optimal_threshold(val_y, val_probs)
                
                intent_scores = torch.sigmoid(full_out).cpu().numpy()

            ordered_ids = [c for c, i in sorted(graph_builder.company_map.items(), key=lambda item: item[1])]
            score_series = pd.Series(intent_scores, index=ordered_ids)
            test_probs = score_series[test_ids].values
            y_test = labels[test_ids].values
        
        # 8. Capacity Model
        logger.info("Phase 8: Training Capacity Score Model (Cox PH)")
        features_with_scores = features_df.copy()
        features_with_scores['intent_score'] = features_with_scores['company_id'].map(score_series)
        survival_df = prepare_survival_data(df1, df2, features_with_scores)
        
        cox_train = survival_df[survival_df['company_id'].isin(train_ids)].drop(columns=['company_id'])
        cox_test = survival_df[survival_df['company_id'].isin(test_ids)].drop(columns=['company_id'])
        
        cox_model = CapacityModel(penalizer=config['capacity_model']['penalizer'])
        try:
            cox_model.fit(cox_train)
        except Exception as e:
            logger.warning(f"Cox fit failed initial, trying heavier penalty: {e}")
            cox_model = CapacityModel(penalizer=1.0)
            cox_model.fit(cox_train)
            
        # 9. Report
        intent_metrics = evaluate_intent(y_test, test_probs, threshold=best_threshold)
        capacity_metrics = evaluate_capacity(cox_model.cph, cox_test)
        
        save_report(intent_metrics, capacity_metrics, "reports/evaluation.json")
        
        # Save models
        if model_type in ['lightgbm', 'ensemble']:
            import pickle
            model_filename = f"models/intent_{model_type}.pkl"
            with open(model_filename, 'wb') as f:
                pickle.dump(intent_model, f)
            logger.info(f"Saved {model_type.upper()} model to {model_filename}")
        else:
            torch.save(model_gnn.state_dict(), "models/intent_gnn.pt")
            logger.info("Saved GNN model to models/intent_gnn.pt")
            
        cox_model.save("models/capacity_cox.pkl")
        logger.info("Pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
