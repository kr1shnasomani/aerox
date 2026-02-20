"""Dependency injection for AEROX API"""

import sys
from pathlib import Path
from functools import lru_cache
import pandas as pd

# Add project root to path so agents can be imported
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.meta_agent import MetaAgent


@lru_cache(maxsize=1)
def get_meta_agent() -> MetaAgent:
    """Get or create MetaAgent singleton (expensive: loads ML models)"""
    return MetaAgent()


@lru_cache(maxsize=1)
def get_dataset1() -> pd.DataFrame:
    """Load dataset1.csv (1000 companies)"""
    path = PROJECT_ROOT / "dataset" / "dataset1.csv"
    return pd.read_csv(path)
