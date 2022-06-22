import datetime
import argparse
import assetuniverse
import pandas as pd
import itertools
from multiprocessing import Pool, set_start_method

from assetuniverse import AssetUniverse, Asset
import metrics
from subportfolio import Subportfolio
from portfolio import Portfolio


def parse_to_contracts(assets: pd.DataFrame, start, end):
    """Parse the symbols in the dataframe into assetuniverse contracts

    Parameters
    ----------
    assets : pd.DataFrame
        import from excel with assets
    """
    contracts = list()
    for _, asset in assets.iterrows():
        au_contract = assetuniverse.Asset(
            start=start,
            end=end,
            ticker=asset['ticker'],
            exchange=asset['Exchange'],
            sectype=asset['Security Type'],
            alternate_tickers=asset['alternate tickers'],
            readable_name=asset['display name'],
            data_source=asset['data source']
        )
        contracts.append(au_contract)
    return contracts

def run_subportfolio(subportfolio: Subportfolio):
    subportfolio.run()
    return subportfolio


parser = argparse.ArgumentParser(description='Allocate portfolio using adaptive asset allocation principals.')
parser.add_argument('assetsfile', type=str)
parser.add_argument('-v', '--nav', type=float, default=100000, help='Portfolio net asset value ($)')
parser.add_argument('-n', '--minweight', type=float, default=0.1, help='Minimum portfolio weight (Default: 0.1)')
parser.add_argument('-x', '--maxweight', type=float, default=4.0, help='Total portfolio weight (Default: 4.0)')
parser.add_argument('-t', '--targetvol', type=float, default=10.0, help='Target annual volatility (Default: 10.0)')
args = parser.parse_args()

# Define subportfolio parameters
lookbacks = [125, 180, 250]
momentum_metrics = [
    metrics.total_return,
    metrics.sharpe_ratio,
    metrics.exponentially_weighted_mean_return_light_bias,
    metrics.exponentially_weighted_mean_return_heavy_bias
]
subportfolio_num_long_positions_portion =  [0.1, 0.4]       # Portion of number of targeted long assets (e.g. 0.2 = 20% of the assets)
subportfolio_num_short_positions_portion = [0.0, 0.2]       # Portion of number of targeted short assets (e.g. 0.2 = 20% of the assets)
subportfolio_min_long_positions = [2, 3, 4]
subportfolio_min_short_positions = [1, 2, 3]
max_ind_long_allocations = [0.5, 0.75, 1.0]
max_ind_short_allocations = [-0.2, -0.3]
total_short_allocations = [0.1, 0.2, 0.3]

# subportfolio_num_long_positions_portion =  [0.2, 0.4]       # Portion of number of targeted long assets (e.g. 0.2 = 20% of the assets)
# subportfolio_num_short_positions_portion = [0.0, 0.3]       # Portion of number of targeted short assets (e.g. 0.2 = 20% of the assets)
# subportfolio_min_long_positions = [2, 4]
# subportfolio_min_short_positions = [0, 3]
# max_ind_long_allocations = [1.0, 1.5]
# max_ind_short_allocations = [-0.1, -0.2]
# total_short_allocations = [0.0, 0.2]

# Define asset universe
assets = pd.read_excel(args.assetsfile)
end = datetime.date.today()
start = end - datetime.timedelta(days=(8/5)*max(lookbacks) + 10)
sym = parse_to_contracts(assets, start, end)
cashasset = Asset(start, end, None)
au = AssetUniverse(start, end, sym, offline=False, borrow_spread=1.5, cashasset=cashasset)
au.download()

# Create subportfolios
num_subportfolios = len(lookbacks)* \
                    len(momentum_metrics)* \
                    len(subportfolio_num_long_positions_portion)* \
                    len(subportfolio_num_short_positions_portion)* \
                    len(subportfolio_min_long_positions)* \
                    len(subportfolio_min_short_positions)* \
                    len(max_ind_long_allocations)* \
                    len(max_ind_short_allocations)* \
                    len(total_short_allocations)

print(f'Optimizing {num_subportfolios} subportfolios... (one . represents 100 subportfolios)')
subportfolios = [Subportfolio(params, au, assets, 1.0, i, num_subportfolios) 
    for i, params in enumerate(itertools.product(
        lookbacks,
        momentum_metrics,
        subportfolio_num_long_positions_portion,
        subportfolio_num_short_positions_portion,
        subportfolio_min_long_positions,
        subportfolio_min_short_positions,
        max_ind_long_allocations,
        max_ind_short_allocations,
        total_short_allocations
    ))
]

set_start_method('fork')
with Pool() as p:
    subportfolios = p.map(run_subportfolio, subportfolios)
# subportfolios = list(map(run_subportfolio, subportfolios))        # single-threaded for debugging

# Combine subportfolios
portfolio = Portfolio(subportfolios, au, args.nav, args.targetvol/100.0)

# Display
print()
print()
print(portfolio)
au.plot_prices()
