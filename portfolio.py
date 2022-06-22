import numpy as np
import pandas as pd
from typing import List

from subportfolio import Subportfolio
from assetuniverse import AssetUniverse

class Portfolio:
    def __init__(self, subportfolios: List[Subportfolio], au: AssetUniverse, nav: float, targetvol: float, leverage: float=1.0):
        self.leverage = leverage
        self.au = au
        self.weights = self.combine_weights(subportfolios)
        self.scaled_weights = self.scale_to_target_vol(targetvol)
        self.allocations = self.calculate_allocations(self.weights, self.scaled_weights, au, nav)
    
    def combine_weights(self, subportfolios: List[Subportfolio]):
        weights = subportfolios[0].weights
        for i in range(1, len(subportfolios)):
            weights = weights.add(
                subportfolios[i].weights, 
                fill_value=0
                )
        return weights/len(subportfolios)

    def scale_to_target_vol(self, targetvol:float=0.10):
        covmatrix = self.au.covariance_matrix(tickers=self.weights.index.to_list())
        w = self.weights.to_numpy()
        annualvol = np.sqrt(np.matmul(w, np.matmul(covmatrix, w.T))*252)

        # debug - ensure scaling actually produces desired target volatility
        # w = w*targetvol/annualvol
        # annualvol2 = np.sqrt(np.matmul(w, np.matmul(covmatrix, w.T))*252)

        scaled_weights = self.weights.copy(deep=True)*targetvol/annualvol
        return scaled_weights

    def calculate_allocations(self, weights: pd.Series, scaled_weights: pd.Series, au: AssetUniverse, nav: float):
        allocations = pd.DataFrame(
            data=0*weights.sort_values(ascending=False),
            columns=['Name']
        )
        prices = au.prices(allocations.index, normalize=False)
        allocations.loc[:,'Name'] = [self.au.assets[ticker].readable_name for ticker in allocations.index]
        allocations.loc[:,'Alternate Tickers'] = [self.au.assets[ticker].alternate_tickers for ticker in allocations.index]
        allocations.loc[:,'Recent Price ($)'] = round(prices[allocations.index].iloc[-1], 2)
        allocations.loc[:,'Allocation (%)'] = weights.sort_values(ascending=False)
        allocations.loc[:,'Allocation ($)'] = nav*allocations['Allocation (%)']
        allocations.loc[:,'Allocation (%)'] = round(100*allocations.loc[:,'Allocation (%)'], 1)
        allocations.loc[:,'Allocation ($)'] = round(allocations.loc[:,'Allocation ($)'], 2)
        # allocations.loc[:,'Shares'] = round(allocations['Allocation ($)']/prices[allocations.index].iloc[-1], 0)
        # allocations.loc[:,'Shares'] = allocations.loc[:,'Shares'].astype(int)
        allocations.loc[:,'Scaled (%)'] = scaled_weights.sort_values(ascending=False)
        allocations.loc[:,'Scaled ($)'] = nav*allocations['Scaled (%)']
        allocations.loc[:,'Scaled (%)'] = round(100*allocations.loc[:,'Scaled (%)'], 1)
        allocations.loc[:,'Scaled ($)'] = round(allocations.loc[:,'Scaled ($)'], 2)
        return allocations

    def __str__(self):
        return self.allocations.to_string()
