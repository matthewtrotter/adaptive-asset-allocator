from typing import List
import pandas as pd

from subportfolio import Subportfolio
from assetuniverse import AssetUniverse

class Portfolio:
    def __init__(self, subportfolios: List[Subportfolio], au: AssetUniverse, nav: float):
        self.weights = self.combine_weights(subportfolios)
        self.allocations = self.calculate_allocations(self.weights, au, nav)
    
    def combine_weights(self, subportfolios: List[Subportfolio]):
        weights = subportfolios[0].weights
        for i in range(1, len(subportfolios)):
            weights = weights.add(
                subportfolios[i].weights, 
                fill_value=0
                )
        return weights/len(subportfolios)

    def calculate_allocations(self, weights: pd.Series, au: AssetUniverse, nav: float):
        allocations = pd.DataFrame(
            data=0*weights.sort_values(ascending=False),
            columns=['Shares']
        )
        allocations.loc[:,'Price ($)'] = round(au.originalprices[allocations.index].iloc[-1], 2)
        allocations.loc[:,'Allocation (%)'] =  weights.sort_values(ascending=False)
        allocations.loc[:,'Allocation ($)'] = nav*allocations['Allocation (%)']
        allocations.loc[:,'Shares'] = round(allocations['Allocation ($)']/au.originalprices[allocations.index].iloc[-1], 0)
        allocations.loc[:,'Shares'] = allocations.loc[:,'Shares'].astype(int)
        allocations.loc[:,'Allocation (%)'] = round(100*allocations.loc[:,'Allocation (%)'], 2)
        allocations.loc[:,'Allocation ($)'] = round(allocations.loc[:,'Allocation ($)'], 2)
        return allocations

    def __str__(self):
        return self.allocations.to_string()
