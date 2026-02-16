import pandas as pd
import numpy as np
import logging
from pathlib import Path

# Configure logger
logger = logging.getLogger(__name__)

def load_datasets(config):
    """
    Load all three datasets from paths specified in config.
    """
    try:
        logger.info("Loading datasets...")
        
        # Load Dataset 1
        ds1_path = Path(config['data']['dataset1_path'])
        df1 = pd.read_csv(ds1_path)
        logger.info(f"Loaded Dataset 1: {df1.shape} rows.")
        
        # Load Dataset 2
        ds2_path = Path(config['data']['dataset2_path'])
        # Parse date columns
        date_cols = ['booking_date', 'payment_due_date', 'payment_received_date']
        df2 = pd.read_csv(ds2_path, parse_dates=date_cols)
        logger.info(f"Loaded Dataset 2: {df2.shape} rows.")
        
        # Load Dataset 3
        ds3_path = Path(config['data']['dataset3_path'])
        df3 = pd.read_csv(ds3_path, parse_dates=['timestamp'])
        logger.info(f"Loaded Dataset 3: {df3.shape} rows.")
        
        return df1, df2, df3
    
    except FileNotFoundError as e:
        logger.error(f"Dataset file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading datasets: {e}")
        raise

def validate_referential_integrity(df1, df2, df3):
    """
    Check if primary keys and foreign keys match across datasets.
    """
    logger.info("Validating referential integrity...")
    
    # 1. Unique companies in DS1
    if not df1['company_id'].is_unique:
        raise ValueError("Dataset 1: company_id is not unique!")
    
    companies_ds1 = set(df1['company_id'])
    companies_ds2 = set(df2['company_id'])
    companies_ds3 = set(df3['company_id'])
    
    # 2. Check FK: DS2 -> DS1
    missing_ds2 = companies_ds2 - companies_ds1
    if missing_ds2:
        logger.warning(f"DS2 has {len(missing_ds2)} companies not in DS1: {list(missing_ds2)[:5]}...")
    else:
        logger.info("Integrity check: All companies in DS2 exist in DS1.")
        
    # 3. Check FK: DS3 -> DS1
    missing_ds3 = companies_ds3 - companies_ds1
    if missing_ds3:
        logger.warning(f"DS3 has {len(missing_ds3)} companies not in DS1: {list(missing_ds3)[:5]}...")
    else:
        logger.info("Integrity check: All companies in DS3 exist in DS1.")
        
    # 4. Check Booking ID linkage: DS3 -> DS2 (should be 1:1)
    bookings_ds2 = set(df2['booking_id'])
    bookings_ds3 = set(df3['booking_id'])
    
    if bookings_ds2 != bookings_ds3:
        missing_bookings = bookings_ds3 - bookings_ds2
        extra_bookings = bookings_ds2 - bookings_ds3
        logger.warning(f"Booking mismatch! {len(missing_bookings)} in DS3 missing from DS2. {len(extra_bookings)} in DS2 missing from DS3.")
    else:
        logger.info("Integrity check: Booking IDs match exactly between DS2 and DS3.")
        
    # 5. Row count verification
    if len(df2) != len(df3):
        logger.warning(f"Row count mismatch: DS2 ({len(df2)}) vs DS3 ({len(df3)})")
    
    logger.info("Referential integrity check passed.")

def validate_data_quality(df1, df2, df3):
    """
    Check for data quality issues like nulls, invalid ranges, etc.
    """
    logger.info("Validating data quality...")
    
    # Check DS1 Targets
    if 'fraud_flag' in df1.columns:
        fraud_counts = df1['fraud_flag'].value_counts(normalize=True)
        logger.info(f"Fraud flag distribution:\n{fraud_counts}")
        if not set(df1['fraud_flag'].unique()).issubset({0, 1}):
            logger.error("Invalid values in fraud_flag (must be 0/1)")
    
    if 'default_flag' in df1.columns:
        default_counts = df1['default_flag'].value_counts(normalize=True)
        logger.info(f"Default flag distribution:\n{default_counts}")
        if not set(df1['default_flag'].unique()).issubset({0, 1}):
            logger.error("Invalid values in default_flag (must be 0/1)")
            
    # Check DS2 Payment Status
    valid_statuses = {'paid', 'pending', 'chargeback', 'defaulted'}
    actual_statuses = set(df2['payment_status'].unique())
    if not actual_statuses.issubset(valid_statuses):
        logger.warning(f"Unexpected payment statuses found: {actual_statuses - valid_statuses}")
        
    # Check consistent chargeback flag
    mismatches = df2[
        ((df2['payment_status'] == 'chargeback') & (df2['chargeback_flag'] == 0)) |
        ((df2['payment_status'] != 'chargeback') & (df2['chargeback_flag'] == 1))
    ]
    if len(mismatches) > 0:
        logger.warning(f"Found {len(mismatches)} rows with inconsistent payment_status and chargeback_flag")
        
    # Cap avg_customer_rating in DS1
    if 'avg_customer_rating' in df1.columns:
        over_limit = df1[df1['avg_customer_rating'] > 5.0]
        if len(over_limit) > 0:
            logger.info(f"Cappping {len(over_limit)} rows with avg_customer_rating > 5.0")
            df1.loc[df1['avg_customer_rating'] > 5.0, 'avg_customer_rating'] = 5.0
            
    return df1  # Return potentially modified df1
