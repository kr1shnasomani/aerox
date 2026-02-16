import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def prepare_survival_data(df1, df2, company_features):
    """
    Prepare data for Cox Proportional Hazards Model.
    
    Args:
        df1: Dataset 1 (Company Profiles) - contains targets
        df2: Dataset 2 (Transactions) - contains time-to-event info
        company_features: Engineered features (covariates)
    
    Returns:
        pd.DataFrame: Survival dataset with columns 'T', 'E', and covariates.
    """
    logger.info("Preparing survival data...")
    
    # 1. Calculate Time (T) and Event (E) per company
    # Event: default_flag from DS1
    # Time: max(days_to_payment) observed or time since first booking?
    
    survival_df = df1[['company_id', 'default_flag', 'days_since_first_booking']].copy()
    survival_df = survival_df.rename(columns={'default_flag': 'E'})
    
    # For defaulted companies (E=1), T is the time until default.
    # For non-defaulted (E=0), T is the observation window (days since first booking).
    
    # However, DS2 gives specific payment info. Let's refine T.
    # T = max(days_to_payment) for observed payments?
    # Or T = days_since_first_booking if no default?
    
    # Better approach from context:
    # "Companies that haven't defaulted yet = right-censored data"
    # "Event indicator: default_flag from Dataset 1"
    # "Time-to-event data: days_to_payment from Dataset 2"
    
    # Group DS2 by company to get max observed payment delay
    max_delay = df2.groupby('company_id')['days_to_payment'].max()
    
    # Merge max delay into survival_df
    survival_df = survival_df.merge(max_delay, on='company_id', how='left')
    
    # Logic for T:
    # If E=1 (Default): T = Time from first booking to default event? 
    # Or just use the max observed delay as a proxy for "how long they survived"?
    # The requirement says: "Input Data: Time-series payment data from Dataset 2: days_to_payment"
    
    # Let's use T = max(days_to_payment) if observed, else fallback to days_since_first_booking?
    # No, days_to_payment is per-transaction. Survival analysis usually tracks "time until default".
    # If they haven't defaulted, they survived for `days_since_first_booking`.
    
    # Let's use:
    # T = days_since_first_booking 
    # (assuming this represents the duration of the relationship/survival)
    survival_df['T'] = survival_df['days_since_first_booking']
    
    # Filter out companies with T <= 0 (shouldn't happen but defensive)
    survival_df = survival_df[survival_df['T'] > 0]
    
    # 2. Merge Covariates
    # Drop E and T from features to avoid leakage if they were there (they shouldn't be)
    features_to_merge = company_features.drop(columns=['default_flag', 'fraud_flag'], errors='ignore')
    
    final_df = survival_df[['company_id', 'T', 'E']].merge(features_to_merge, on='company_id', how='inner')
    
    logger.info(f"Survival data prepared: {final_df.shape} rows.")
    return final_df
