from typing import Dict, List
from assetuniverse import AssetUniverse
import numpy as np
import scipy.optimize as opt
import pandas as pd

class Subportfolio(object):
    def __init__(self, params: Dict, au: AssetUniverse, assets: pd.DataFrame, total_weight: float, id: int, total_ids: int):
        self.lookback = params[0]
        self.momentum_metric = params[1]
        self.subportfolio_num_long_positions_portion = params[2]
        self.subportfolio_num_short_positions_portion = params[3]
        self.subportfolio_min_long_positions = params[4]
        self.subportfolio_min_short_positions = params[5]
        self.max_ind_long_allocation = params[6]
        self.max_ind_short_allocation = params[7]
        self.total_short_allocation = params[8]
        self.min_ind_long_allocation = 0.0
        self.min_ind_short_allocation = 0.0
        self.total_weight = total_weight
        self.au = au
        self.assets = assets
        self.id = id
        self.total_ids = total_ids

    def run(self):
        self.long_assets = self.sort_long_assets_by_metric(self.assets['ticker'].to_list())
        self.short_assets = self.sort_short_assets_by_metric(self.assets['ticker'].to_list())
        self.weights = self.optimize()
        if self.id % 100 == 0 and self.id > 0:
            # print(f'Finished subportfolio: {self.id} of {self.total_ids}')
            print('.', flush=True, end='')

    def sort_long_assets_by_metric(self, assets: List[str]) -> List:
        prices = self.au.prices(assets, normalize=True)
        returns = self.au.returns(assets)
        metric, ascending = self.momentum_metric(prices[assets], returns[assets], self.lookback)
        metric = metric.sort_values(ascending=ascending)
        num_keep = int(np.ceil(max(self.subportfolio_num_long_positions_portion*len(assets), self.subportfolio_min_long_positions)))
        return metric[-num_keep:].index.to_list()

    def sort_short_assets_by_metric(self, assets: List[str]) -> List:
        if self.total_short_allocation > 0:
            prices = self.au.prices(assets, normalize=True)
            returns = self.au.returns(assets)
            metric, ascending = self.momentum_metric(prices[assets], returns[assets], self.lookback)
            metric = metric.sort_values(ascending=not ascending)        # Opposite direction of long positions
            num_keep = int(np.ceil(max(self.subportfolio_num_short_positions_portion*len(assets), self.subportfolio_min_short_positions)))
            if num_keep > 0:
                return metric[-num_keep:].index.to_list()
        return []

    def optimize(self) -> np.ndarray:
        all_assets = self.long_assets + self.short_assets
        covmatrix = self.au.covariance_matrix(tickers=all_assets)
        cons = [
            {'type': 'eq', 'fun': self._sum_weights}, # total weight constraint
            ]
        if self.short_assets:
            cons = cons + [
                {'type': 'ineq', 'fun': self._sum_short_weights}, # total short weight constraint
            ]

        # Set initial weights and bounds
        nlong = len(self.long_assets)
        nshort = len(self.short_assets)
        bound_left = np.ones(nlong + nshort)
        bound_right = np.ones(nlong + nshort)
        bound_left[:] = self.min_ind_long_allocation
        bound_right[:] = self.max_ind_long_allocation
        if self.short_assets:
            bound_left[-nshort:] = self.max_ind_short_allocation
            bound_right[-nshort:] = self.min_ind_short_allocation
        bounds = opt.Bounds(bound_left, bound_right)
        initial_weights = self._rand_initial_weights(bounds, nshort)
        
        result = opt.minimize(
            fun=self._expected_variance,
            x0=initial_weights,
            args=covmatrix,
            method='SLSQP',
            constraints=cons,
            bounds=bounds,
            tol=1e-13,
            options={'maxiter': 1000, 'disp': False}
        )
        optimized_weights = result.x.transpose()

        weights = pd.Series(
            data=np.zeros(len(all_assets)), 
            index=all_assets
            )
        weights.loc[all_assets] = optimized_weights
        return weights

    def _rand_initial_weights(self, bounds: opt.Bounds, nshort: int):
        """Set an initial array of weights that safisfy the bounds and constraints

        Parameters
        ----------
        bounds : opt.Bounds
            Bounds for each individual asset
        nshort : number of short assets
        
        Returns
        -------
        initial_weights : np.ndarray
            Initial weights that satisfy the bounds and constraints
        """
        initial_weights = np.ones(bounds.lb.shape)
        if nshort > 0:
            initial_weights[-nshort:] = 0
        initial_weights = initial_weights*self.total_weight/np.sum(initial_weights)
        if self._sum_weights(initial_weights) == 0 and self._sum_short_weights(initial_weights) > 0:
            return initial_weights
        for _ in range(1000000):
            initial_weights = np.random.uniform(
                low=bounds.lb,
                high=bounds.ub
            )
            initial_weights = initial_weights*self.total_weight/np.sum(initial_weights)
            if self._sum_weights(initial_weights) == 0 and self._sum_short_weights(initial_weights) > 0:
                return initial_weights
        raise RuntimeError(f'Could not set initial random weights.\nBounds: {bounds}\nTotal Weight Constraint: {self.total_weight}\nMax ind. long weight: {self.max_ind_long_allocation}\nTotal Short Weight Constraint: {self.total_short_allocation}\nMax ind. short weight: {self.max_ind_short_allocation}')


    def _expected_variance(self, weights, covmatrix):
        return np.matmul(weights, np.matmul(covmatrix, weights.T))

    def _sum_weights(self, weights):
        """Sum all weights and subtract total weight. 
        This sum must be == 0.
        """
        return np.sum(weights) - self.total_weight

    def _sum_short_weights(self, weights):
        """Sum all short weights and add total short weight.
        This sum must be > 0.
        """
        nshort = len(self.short_assets)
        return np.sum(weights[-nshort:]) + self.total_short_allocation + 1e-6
