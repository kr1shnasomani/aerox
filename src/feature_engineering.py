import pandas as pd
import numpy as np
import logging
from sklearn.preprocessing import RobustScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

logger = logging.getLogger(__name__)

def engineer_features(df1, df2, df3, config):
    """
    Main function to execute feature engineering pipeline.
    """
    logger.info("Engineering features...")
    
    # 1. Clean DS1
    df1_clean = clean_ds1(df1, config)
    
    # 2. Aggregate DS2
    df2_agg = aggregate_ds2(df2)
    
    # 3. Graph Features from DS3
    ds3_feats = compute_graph_features(df3)
    
    # 4. Merge all together on company_id
    full_features = df1_clean.merge(df2_agg, on='company_id', how='left')
    full_features = full_features.merge(ds3_feats, on='company_id', how='left')
    
    # Fill any NaNs from left joins (companies with no history/graph - unlikely but safe)
    numerical_cols = full_features.select_dtypes(include=np.number).columns
    full_features[numerical_cols] = full_features[numerical_cols].fillna(0)
    
    logger.info(f"Feature engineering complete. Final shape: {full_features.shape}")
    return full_features

def clean_ds1(df, config):
    """
    Apply transformations to Dataset 1 (Static Company Profiles).
    """
    df = df.copy()
    
    # 1. Drop unused columns
    cols_to_drop = config['feature_engineering']['drop_columns']
    cols_present = [c for c in cols_to_drop if c in df.columns]
    if cols_present:
        logger.info(f"Dropping columns: {cols_present}")
        df = df.drop(columns=cols_present)
    
    # 2. One-Hot Encoding
    categorical_cols = ['segment', 'region']
    # Create simple OHE, drop_first=False to keep all categories explicitly
    ohe = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    
    encoded_features = ohe.fit_transform(df[categorical_cols])
    encoded_cols = ohe.get_feature_names_out(categorical_cols)
    encoded_df = pd.DataFrame(encoded_features, columns=encoded_cols, index=df.index)
    
    df = df.drop(columns=categorical_cols).join(encoded_df)
    
    # 3. Log Transforms
    log_cols = config['feature_engineering']['log_transform_columns']
    for col in log_cols:
        if col in df.columns:
            # log1p handles 0s
            df[f'log_{col}'] = np.log1p(df[col])
            df = df.drop(columns=[col]) # Drop original
            
    # 4. Scaling (RobustScaler)
    # MOVED to train_pipeline.py to prevent leakage (fit on train, transform val/test)
    # We just ensure the columns are clean/ready here.
    
    # 5. EXPLICITLY Drop Target Columns to prevent Leakage
    # These must NOT be in the feature set for the graph model
    targets_to_drop = ['fraud_flag', 'default_flag']
    present_targets = [t for t in targets_to_drop if t in df.columns]
    if present_targets:
        logger.info(f"Dropping target columns from features to prevent leakage: {present_targets}")
        df = df.drop(columns=present_targets)

    return df

def aggregate_ds2(df):
    """
    Aggregate Dataset 2 (Transactions) to company level with temporal velocity features.
    """
    # Defensive copy
    df = df.copy()
    
    # Convert booking_date to datetime if not already
    if 'booking_date' in df.columns:
        df['booking_date'] = pd.to_datetime(df['booking_date'], errors='coerce')
    
    # Add helper columns
    df['is_paid'] = (df['payment_status'] == 'paid').astype(int)
    df['is_pending'] = (df['payment_status'] == 'pending').astype(int)
    df['is_defaulted'] = (df['payment_status'] == 'defaulted').astype(int)
    
    # Group By Company
    agg_funcs = {
        'booking_id': 'count', # Total bookings
        'chargeback_flag': 'sum', # Total chargebacks
        'days_to_payment': ['mean', 'max', 'std'],
        'booking_amount_inr': ['sum', 'mean', 'std'],
        'settled_amount_inr': 'sum',
        'is_paid': 'mean', # Pct paid
        'is_pending': 'mean',
        'is_defaulted': 'mean',
    }
    
    agg_df = df.groupby('company_id').agg(agg_funcs)
    
    # Flatten multi-level columns
    agg_df.columns = [f"{col[0]}_{col[1]}" for col in agg_df.columns]
    agg_df = agg_df.reset_index()
    
    # Rename for clarity
    rename_map = {
        'booking_id_count': 'total_bookings_ds2',
        'chargeback_flag_sum': 'total_chargebacks_ds2',
        'days_to_payment_mean': 'avg_days_to_payment',
        'days_to_payment_max': 'max_days_to_payment',
        'days_to_payment_std': 'std_days_to_payment',
        'booking_amount_inr_sum': 'total_booking_val',
        'booking_amount_inr_mean': 'avg_booking_val',
        'booking_amount_inr_std': 'std_booking_val',
        'settled_amount_inr_sum': 'total_settled_val',
        'is_paid_mean': 'pct_paid',
        'is_pending_mean': 'pct_pending',
        'is_defaulted_mean': 'pct_defaulted_ds2'
    }
    agg_df = agg_df.rename(columns=rename_map)
    
    # Derived features
    agg_df['chargeback_rate_ds2'] = agg_df['total_chargebacks_ds2'] / (agg_df['total_bookings_ds2'] + 1e-6)
    agg_df['settlement_ratio'] = agg_df['total_settled_val'] / (agg_df['total_booking_val'] + 1e-6)
    
    # === TEMPORAL VELOCITY FEATURES ===
    # Add temporal trends if booking_date available
    if 'booking_date' in df.columns and not df['booking_date'].isna().all():
        velocity_features = compute_temporal_velocity(df)
        agg_df = agg_df.merge(velocity_features, on='company_id', how='left')
    
    return agg_df

def compute_temporal_velocity(df):
    """
    Compute temporal velocity features showing behavior trends over time.
    """
    df = df.copy()
    df = df.sort_values(['company_id', 'booking_date'])
    
    # Get latest date for recency calculations
    max_date = df['booking_date'].max()
    
    velocity_list = []
    
    for company_id, group in df.groupby('company_id'):
        if len(group) < 2:
            # Not enough data for trends
            velocity_list.append({
                'company_id': company_id,
                'booking_velocity_trend': 0,
                'recent_vs_old_bookings_ratio': 1.0,
                'payment_speed_trend': 0,
                'chargeback_acceleration': 0,
                'amount_trend': 0,
                'recent_default_rate': 0,
                'historical_default_rate': 0,
            })
            continue
        
        group = group.sort_values('booking_date')
        
        # Split into early half and late half
        mid_idx = len(group) // 2
        early_half = group.iloc[:mid_idx]
        late_half = group.iloc[mid_idx:]
        
        # Split by recency (last 30 days vs older)
        days_from_max = (max_date - group['booking_date']).dt.days
        recent = group[days_from_max <= 30]
        old = group[days_from_max > 30]
        
        # 1. Booking velocity trend (late vs early bookings per day)
        early_days = (early_half['booking_date'].max() - early_half['booking_date'].min()).days + 1
        late_days = (late_half['booking_date'].max() - late_half['booking_date'].min()).days + 1
        early_velocity = len(early_half) / max(early_days, 1)
        late_velocity = len(late_half) / max(late_days, 1)
        booking_velocity_trend = (late_velocity - early_velocity) / (early_velocity + 1e-6)
        
        # 2. Recent vs old bookings ratio
        recent_count = len(recent)
        old_count = len(old)
        recent_vs_old_ratio = recent_count / max(old_count, 1)
        
        # 3. Payment speed trend (days_to_payment: negative trend = getting faster)
        early_payment_days = early_half['days_to_payment'].mean()
        late_payment_days = late_half['days_to_payment'].mean()
        payment_speed_trend = (late_payment_days - early_payment_days) / (early_payment_days + 1e-6)
        
        # 4. Chargeback acceleration
        early_cb_rate = early_half['chargeback_flag'].mean()
        late_cb_rate = late_half['chargeback_flag'].mean()
        chargeback_acceleration = late_cb_rate - early_cb_rate
        
        # 5. Amount trend (increasing or decreasing booking amounts)
        early_amount = early_half['booking_amount_inr'].mean()
        late_amount = late_half['booking_amount_inr'].mean()
        amount_trend = (late_amount - early_amount) / (early_amount + 1e-6)
        
        # 6. Recent default rate vs historical
        recent_default_rate = (recent['payment_status'] == 'defaulted').mean() if len(recent) > 0 else 0
        old_default_rate = (old['payment_status'] == 'defaulted').mean() if len(old) > 0 else 0
        
        velocity_list.append({
            'company_id': company_id,
            'booking_velocity_trend': booking_velocity_trend,
            'recent_vs_old_bookings_ratio': recent_vs_old_ratio,
            'payment_speed_trend': payment_speed_trend,
            'chargeback_acceleration': chargeback_acceleration,
            'amount_trend': amount_trend,
            'recent_default_rate': recent_default_rate,
            'historical_default_rate': old_default_rate,
        })
    
    return pd.DataFrame(velocity_list)

def compute_graph_features(df):
    """
    Compute static graph features from Dataset 3.
    """
    g = df.groupby('company_id')
    
    features = pd.DataFrame()
    features['unique_devices'] = g['device_fingerprint'].nunique()
    features['unique_pms'] = g['payment_method_id'].nunique()
    features['unique_ips'] = g['ip_address'].nunique()
    
    # We could add "shared" features here, but that requires
    # analyzing the full graph -> expensive in pandas? 
    # Let's do a simple version:
    # 1. Count how many companies share a device
    dev_counts = df.groupby('device_fingerprint')['company_id'].nunique()
    shared_devs = dev_counts[dev_counts > 1].index
    
    # 2. Filter DS3 for shared devices and count per company
    df_shared_dev = df[df['device_fingerprint'].isin(shared_devs)]
    shared_dev_counts = df_shared_dev.groupby('company_id')['device_fingerprint'].nunique()
    features['shared_device_count'] = shared_dev_counts
    
    # Fill NAs with 0 (companies with no shared devices)
    features.fillna(0, inplace=True)
    
    return features.reset_index()
