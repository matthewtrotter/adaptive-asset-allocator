import datetime
import argparse
import pandas as pd
import itertools

from assetuniverse import AssetUniverse
import metrics
from subportfolio import Subportfolio
from portfolio import Portfolio

parser = argparse.ArgumentParser(description='Allocate portfolio using adaptive asset allocation principals.')
parser.add_argument('assetsfile', type=str)
parser.add_argument('-n', '--nav', type=float, default=100000, help='Portfolio net asset value ($)')
args = parser.parse_args()

# Define subportfolio parameters
lookbacks = [21, 42, 63, 125, 252]
momentum_metrics = [
    metrics.total_return,
    metrics.sharpe_ratio,
    metrics.z_score
]
qualitative_metrics = [
    'Morningstar Star Rating (1-5)',
    'Morningstar Price/FVE',
    'Valueline 3-5 Year Proj. Return High',
    'Valueline 3-5 Year Proj. Return Low',
    'Valueline Timeliness (1-5)',
    'Valueline Safety (1-5)'
]
qualitative_thresholds = [0.2, 0.333, 0.5]
qualitative_min_keep = [2,]
subportfolio_thresholds = [0.2, 0.333, 0.5]
subportfolio_min_keep = [3,]
max_ind_allocations = [0.4, 0.5, 0.6]

# Define asset universe
assets = pd.read_excel(args.assetsfile)
end = datetime.datetime.today()
start = end - datetime.timedelta(days=(8/5)*max(lookbacks) + 10)
au = AssetUniverse(start, end, assets['Stock/ETF'].to_list())

# Create subportfolios
num_subportfolios = len(lookbacks)* \
                    len(momentum_metrics)* \
                    len(qualitative_metrics)* \
                    len(qualitative_thresholds)* \
                    len(qualitative_min_keep)* \
                    len(subportfolio_thresholds)* \
                    len(subportfolio_min_keep)* \
                    len(max_ind_allocations)

subportfolios = [Subportfolio(params, au, assets, i, num_subportfolios) 
    for i, params in enumerate(itertools.product(
        lookbacks,
        momentum_metrics,
        qualitative_metrics,
        qualitative_thresholds,
        qualitative_min_keep,
        subportfolio_thresholds,
        subportfolio_min_keep,
        max_ind_allocations
    ))
]

# Combine subportfolios
portfolio = Portfolio(subportfolios, au, args.nav)

# Display
print(portfolio)
au.plotprices()
