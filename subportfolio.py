from typing import Dict, List
from assetuniverse import AssetUniverse
import numpy as np
import pandas as pd

class Subportfolio(object):
    def __init__(self, params: Dict, au: AssetUniverse, assets: pd.DataFrame):
        self.lookback = params[0]
        self.momentum_metrics = params[1]
        self.qualitative_metrics = params[2]
        self.qualitative_thresholds = params[3]
        self.qualitative_min_keep = params[4]
        self.subportfolio_min_keep = params[5]
        self.max_ind_allocations = params[6]

        # 'asc' means that higher numbers are better 
        self.qualitative_metric_directions = {
            'Morningstar Star Rating (1-5)': 'asc',
            'Morningstar Price/FVE': 'desc',
            'Valueline 3-5 Year Proj. Return High': 'asc',
            'Valueline 3-5 Year Proj. Return Low': 'asc',
            'Valueline Timeliness (1-5)': 'desc',
            'Valueline Safety (1-5)': 'desc'
        }

        assets = self.sort_by_qualitative_metric()
        assets = self.sort_by_metric(assets)
        self.weights = self.minvar_optimization(assets)

    def sort_by_qualitative_metric(self) -> List:
        return list()

    def sort_by_metric(self, assets: List) -> List:
        return list()

    def minvar_optimization(self, assets: List) -> np.ndarray
        return np.zeros(3)

    def __add__(self)