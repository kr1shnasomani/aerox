import logging
import yaml
import os
import random
import numpy as np
import torch
import joblib
from pathlib import Path

def setup_logger(name='aerox_logger', log_file='aerox_training.log', level=logging.INFO):
    """Function to setup as many loggers as you want"""
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    
    # console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def load_config(config_path='configs/config.yaml'):
    """Load configuration variables from a YAML file."""
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def set_seed(seed=42):
    """Set random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    os.environ['PYTHONHASHSEED'] = str(seed)

def save_object(obj, filepath):
    """Save Python object using joblib."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(obj, filepath)

def load_object(filepath):
    """Load Python object using joblib."""
    return joblib.load(filepath)
