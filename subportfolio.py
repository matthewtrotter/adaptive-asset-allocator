from typing import Dict, List
from assetuniverse import AssetUniverse
import numpy as np
import pandas as pd

class Subportfolio(object):
    def __init__(self, params: Dict, au: AssetUniverse, assets: pd.DataFrame):
        self.lookback = params[0]
        self.momentum_metric = params[1]
        self.qualitative_metric = params[2]
        self.qualitative_threshold = params[3]
        self.qualitative_min_keep = params[4]
        self.subportfolio_threshold = params[5]
        self.subportfolio_min_keep = params[6]
        self.max_ind_allocation = params[7]

        self.au = au

        # True means that higher numbers are better 
        self.qualitative_metric_ascending = {
            'Morningstar Star Rating (1-5)': True,
            'Morningstar Price/FVE': False,
            'Valueline 3-5 Year Proj. Return High': True,
            'Valueline 3-5 Year Proj. Return Low': True,
            'Valueline Timeliness (1-5)': False,
            'Valueline Safety (1-5)': False
        }

        keep_assets = self.sort_by_qualitative_metric(assets)
        assets = self.sort_by_metric(keep_assets)
        self.weights = self.minvar_optimization(assets)

    def sort_by_qualitative_metric(self, assets: pd.DataFrame) -> List:
        without_rating = assets[['Stock/ETF', self.qualitative_metric]].loc[assets[self.qualitative_metric].isna()]
        with_rating = assets[['Stock/ETF', self.qualitative_metric]].loc[assets[self.qualitative_metric].notna()]
        with_rating = with_rating[['Stock/ETF', self.qualitative_metric]].sort_values(
            by=self.qualitative_metric, 
            ascending=self.qualitative_metric_ascending[self.qualitative_metric], 
            ignore_index=True
            )
        num_keep = int(np.ceil(max(self.qualitative_threshold*len(with_rating), self.qualitative_min_keep)))
        keep_assets = with_rating['Stock/ETF'].loc[:num_keep].to_list() + without_rating['Stock/ETF'].to_list()
        return keep_assets

    def sort_by_metric(self, assets: List) -> List:
        metric, ascending = self.momentum_metric(self.au.p[assets], self.lookback)
        metric = metric.sort_values(ascending=ascending)
        num_keep = int(np.ceil(max(self.subportfolio_threshold*len(assets), self.subportfolio_min_keep)))
        return metric[-num_keep:].index.to_list()

    def minvar_optimization(self, assets: List) -> np.ndarray:
        return np.zeros(3)

    # def __add__(self, other):
    #     pass
        