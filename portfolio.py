from typing import List
import pandas as pd

from subportfolio import Subportfolio
from assetuniverse import AssetUniverse

class Portfolio:
    def __init__(self, subportfolios: List[Subportfolio]):
        self.weights = subportfolios[0].weights
        for i in range(1, len(subportfolios)):
            self.weights = self.weights.add(
                subportfolios[i].weights, 
                fill_value=0
                )
    
    def __str__(self):
        return self.weights.to_string()
