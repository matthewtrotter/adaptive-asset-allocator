import datetime
import argparse
import assetuniverse
import pandas as pd
import itertools
from multiprocessing import Pool, set_start_method

from assetuniverse import AssetUniverse
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
            alternate_tickers=asset['alternate tickers'],
            display_name=asset['display name'],
            data_source=asset['data source']
        )
        contracts.append(au_contract)
    return contracts

def run_subportfolio(subportfolio: Subportfolio):
    subportfolio.run()
    return subportfolio


parser = argparse.ArgumentParser(description='Allocate portfolio using adaptive asset allocation principals.')
parser.add_argument('assetsfile', type=str)
parser.add_argument('-n', '--nav', type=float, default=100000, help='Portfolio net asset value ($)')
parser.add_argument('-t', '--totalweight', type=float, default=1.0, help='Total portfolio weight (Default: 1.0)')
args = parser.parse_args()

# Define subportfolio parameters
lookbacks = [42, 63, 125, 252]
momentum_metrics = [
    metrics.total_return,
    metrics.sharpe_ratio,
    metrics.exponentially_weighted_mean_return_light_bias,
    metrics.exponentially_weighted_mean_return_heavy_bias
]
# subportfolio_num_long_positions_portion =  [0.1, 0.2, 0.3, 0.4]       # Portion of number of targeted long assets (e.g. 0.2 = 20% of the assets)
subportfolio_num_long_positions_portion =  [0.2, 0.4]       # Portion of number of targeted long assets (e.g. 0.2 = 20% of the assets)
# subportfolio_num_short_positions_portion = [0.0, 0.1, 0.2, 0.3]       # Portion of number of targeted short assets (e.g. 0.2 = 20% of the assets)
subportfolio_num_short_positions_portion = [0.0, 0.3]       # Portion of number of targeted short assets (e.g. 0.2 = 20% of the assets)
# subportfolio_min_long_positions = [2, 3, 4]
subportfolio_min_long_positions = [2, 4]
# subportfolio_min_short_positions = [0, 1, 2, 3]
subportfolio_min_short_positions = [0, 3]
# max_ind_long_allocations = [0.75, 1.0, 1.25, 1.5]
max_ind_long_allocations = [1.0, 1.5]
# max_ind_short_allocations = [-0.05, -0.1, -0.15, -0.2]
max_ind_short_allocations = [-0.1, -0.2]
# total_short_allocations = [0.0, 0.05, 0.10, 0.15, 0.2]
total_short_allocations = [0.0, 0.2]

# Define asset universe
assets = pd.read_excel(args.assetsfile)
end = datetime.date.today()
start = end - datetime.timedelta(days=(8/5)*max(lookbacks) + 10)
sym = parse_to_contracts(assets, start, end)
au = AssetUniverse(start, end, sym, offline=False, borrow_spread=1.5)
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
subportfolios = [Subportfolio(params, au, assets, args.totalweight, i, num_subportfolios) 
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

# Combine subportfolios
portfolio = Portfolio(subportfolios, au, args.nav)

# Display
print(portfolio)
au.plot_prices()
