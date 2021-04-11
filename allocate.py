import datetime.datetime
import argparse
import pandas as pd
import itertools

from assetuniverse import AssetUniverse
import metrics
from subportfolio import Subportfolio
from portfolio import Portfolio

parser = argparse.ArgumentParser(description='Allocate portfolio using adaptive asset allocation principals.')
parser.add_argument('assetsfile', type=argparse.FileType('r'))
args = parser.parse_args()

# Define subportfolio parameters
lookbacks = [30, 60, 90, 180, 365]
momentum_metrics = [
    metrics.total_return,
    metrics.sharpe_ratio
]
qualitative_metrics = [
    'Morningstar Star Rating (1-5)',
    'Morningstar Price/FVE',
    'Valueline 3-5 Year Proj. Return High',
    'Valueline 3-5 Year Proj. Return Low',
    'Valueline Timeliness (1-5)',
    'Valueline Safety (1-5)'
]
qualitative_thresholds = [0.2, 0.3, 0.4, 0.5, 0.6]
qualitative_min_keep = [2,]
subportfolio_min_keep = [4,]
max_ind_allocations = [0.25, 0.333, 0.5, 0.667, 0.75]


# Define asset universe
assets = pd.read_excel(args.assetsfile)
end = datetime.datetime.today()
start = end - max(lookbacks) - 1
au = AssetUniverse(start, end, assets.index)

# Create subportfolios
subportfolios = [Subportfolio(params, au) for params in itertools(
    lookbacks,
    momentum_metrics,
    qualitative_thresholds,
    qualitative_min_keep,
    subportfolio_min_keep,
    max_ind_allocations
)]

# Combine subportfolios
portfolio = Portfolio(subportfolios)

# Display
print(portfolio)
au.plot_prices()

