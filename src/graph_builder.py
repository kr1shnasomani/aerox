import torch
import numpy as np
import pandas as pd
from torch_geometric.data import HeteroData
import torch_geometric.transforms as T
import logging

logger = logging.getLogger(__name__)

class GraphBuilder:
    def __init__(self, df3, company_features_df):
        self.df3 = df3
        self.company_features_df = company_features_df
        self.data = HeteroData()
        
        # Mappings
        self.company_map = {}
        self.device_map = {}
        self.pm_map = {}
        self.ip_map = {}
        
    def build(self):
        logger.info("Building heterogeneous graph...")
        
        # 1. Create Node Indices
        self._create_node_mappings()
        
        # 2. Add Node Features
        self._add_node_features()
        
        # 3. Add Edges
        self._add_edges()
        
        # 4. Add Reverse Edges
        self.data = T.ToUndirected()(self.data)
        
        logger.info(f"Graph built: {self.data}")
        return self.data
    
    def _create_node_mappings(self):
        # Unique entities
        companies = self.company_features_df['company_id'].unique()
        devices = self.df3['device_fingerprint'].unique()
        pms = self.df3['payment_method_id'].unique()
        ips = self.df3['ip_address'].unique()
        
        self.company_map = {id: i for i, id in enumerate(companies)}
        self.device_map = {id: i for i, id in enumerate(devices)}
        self.pm_map = {id: i for i, id in enumerate(pms)}
        self.ip_map = {id: i for i, id in enumerate(ips)}
        
        logger.info(f"Nodes: {len(companies)} companies, {len(devices)} devices, {len(pms)} PMs, {len(ips)} IPs")
        
    def _add_node_features(self):
        # Company Features
        # Ensure order matches company_map
        ordered_companies = [c for c, i in sorted(self.company_map.items(), key=lambda item: item[1])]
        
        # Filter for features only (drop IDs)
        feat_df = self.company_features_df.set_index('company_id')
        feat_df = feat_df.loc[ordered_companies]
        
        # Drop non-numeric for tensor conversion
        numeric_feats = feat_df.select_dtypes(include=np.number)
        x = torch.from_numpy(numeric_feats.values).float()
        
        self.data['company'].x = x
        self.data['company'].num_nodes = len(ordered_companies)
        
        # For other nodes, use integer indices for learnable embeddings
        self.data['device'].x = torch.arange(len(self.device_map), dtype=torch.long)
        self.data['payment_method'].x = torch.arange(len(self.pm_map), dtype=torch.long)
        self.data['ip'].x = torch.arange(len(self.ip_map), dtype=torch.long)

    def _add_edges(self):
        # Helper to map columns to indices with deduplication
        def map_edges(src_col, dst_col, src_map, dst_map):
            # Extract pairs and drop duplicates to prevent weight inflation
            pairs = self.df3[[src_col, dst_col]].drop_duplicates()
            
            src_indices = [src_map[x] for x in pairs[src_col]]
            dst_indices = [dst_map[x] for x in pairs[dst_col]]
            return torch.tensor([src_indices, dst_indices], dtype=torch.long)
        
        # Company -> Device
        edge_index = map_edges('company_id', 'device_fingerprint', self.company_map, self.device_map)
        self.data['company', 'uses', 'device'].edge_index = edge_index
        
        # Company -> Payment Method
        edge_index = map_edges('company_id', 'payment_method_id', self.company_map, self.pm_map)
        self.data['company', 'uses', 'payment_method'].edge_index = edge_index
        
        # Company -> IP
        edge_index = map_edges('company_id', 'ip_address', self.company_map, self.ip_map)
        self.data['company', 'from', 'ip'].edge_index = edge_index
