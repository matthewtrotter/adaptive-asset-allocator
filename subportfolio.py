from typing import Dict, List
from assetuniverse import AssetUniverse
import numpy as np
import scipy.optimize as opt
import pandas as pd

class Subportfolio(object):
    def __init__(self, params: Dict, au: AssetUniverse, assets: pd.DataFrame, id: int, total_ids: int):
        self.lookback = params[0]
        self.momentum_metric = params[1]
        self.qualitative_metric = params[2]
        self.qualitative_threshold = params[3]
        self.qualitative_min_keep = params[4]
        self.subportfolio_threshold = params[5]
        self.subportfolio_min_keep = params[6]
        self.max_ind_allocation = params[7]
        self.min_ind_allocation = 0.0

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
        self.weights = self.optimize(assets)
        if id % 100 == 0 and id > 0:
            print(f'Finished subportfolio: {id} of {total_ids}')

    def sort_by_qualitative_metric(self, assets: pd.DataFrame) -> List:
        without_rating = assets[['symbol', self.qualitative_metric]].loc[assets[self.qualitative_metric].isna()]
        with_rating = assets[['symbol', self.qualitative_metric]].loc[assets[self.qualitative_metric].notna()]
        with_rating = with_rating[['symbol', self.qualitative_metric]].sort_values(
            by=self.qualitative_metric, 
            ascending=self.qualitative_metric_ascending[self.qualitative_metric], 
            ignore_index=True
            )
        num_keep = int(np.ceil(max(self.qualitative_threshold*len(with_rating), self.qualitative_min_keep)))
        keep_assets = with_rating['symbol'].iloc[-num_keep:].to_list() + without_rating['symbol'].to_list()
        if self.qualitative_metric == 'Valueline 3-5 Year Proj. Return High':
            x = 1
        return keep_assets

    def sort_by_metric(self, assets: List) -> List:
        metric, ascending = self.momentum_metric(self.au.p[assets], self.au.r[assets], self.lookback)
        metric = metric.sort_values(ascending=ascending)
        num_keep = int(np.ceil(max(self.subportfolio_threshold*len(assets), self.subportfolio_min_keep)))
        return metric[-num_keep:].index.to_list()

    def optimize(self, assets: List) -> np.ndarray:
        covmatrix = self.au.covariance_matrix(symbols=assets, rand_drop_percent=0.10)
        cons = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0},           # sum of weights must match 1.0
            ]

        result = opt.minimize(
            fun=self._expected_variance,
            x0=np.ones(len(assets))/len(assets),
            args=covmatrix,
            method='SLSQP',
            constraints=cons,
            bounds=opt.Bounds(self.min_ind_allocation, self.max_ind_allocation),
            tol=1e-13,
            options={'maxiter': 1000, 'disp': False}
        )
        optimized_weights = result.x.transpose()

        weights = pd.Series(
            data=np.zeros(len(self.au.sym_list)), 
            index=self.au.sym_list
            )
        weights.loc[assets] = optimized_weights
        return weights

    def _expected_variance(self, weights, covmatrix):
        return np.matmul(weights, np.matmul(covmatrix, weights.T))
