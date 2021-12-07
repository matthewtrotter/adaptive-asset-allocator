from typing import Dict, List
from assetuniverse import AssetUniverse
import numpy as np
import scipy.optimize as opt
import pandas as pd

class Subportfolio(object):
    def __init__(self, params: Dict, au: AssetUniverse, assets: pd.DataFrame, id: int, total_ids: int):
        self.lookback = params[0]
        self.momentum_metric = params[1]
        self.subportfolio_threshold = params[2]
        self.subportfolio_min_keep = params[3]
        self.max_ind_allocation = params[4]
        self.min_ind_allocation = 0.0
        self.au = au

        keep_assets = self.sort_by_metric(assets['ticker'].to_list())
        self.weights = self.optimize(keep_assets)
        if id % 100 == 0 and id > 0:
            print(f'Finished subportfolio: {id} of {total_ids}')

    def sort_by_metric(self, assets: List[str]) -> List:
        prices = self.au.prices(assets, normalize=True)
        returns = self.au.returns(assets)
        metric, ascending = self.momentum_metric(prices[assets], returns[assets], self.lookback)
        metric = metric.sort_values(ascending=ascending)
        num_keep = int(np.ceil(max(self.subportfolio_threshold*len(assets), self.subportfolio_min_keep)))
        return metric[-num_keep:].index.to_list()

    def optimize(self, assets: List) -> np.ndarray:
        covmatrix = self.au.covariance_matrix(tickers=assets)
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
            data=np.zeros(len(assets)), 
            index=assets
            )
        weights.loc[assets] = optimized_weights
        return weights

    def _expected_variance(self, weights, covmatrix):
        return np.matmul(weights, np.matmul(covmatrix, weights.T))
