import datetime
import argparse
import assetuniverse
import pandas as pd
import itertools

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



parser = argparse.ArgumentParser(description='Allocate portfolio using adaptive asset allocation principals.')
parser.add_argument('assetsfile', type=str)
parser.add_argument('-n', '--nav', type=float, default=100000, help='Portfolio net asset value ($)')
parser.add_argument('-l', '--lev', type=float, default=1.0, help='Total portfolio leverage (Default: 1.0)')
args = parser.parse_args()

# Define subportfolio parameters
lookbacks = [21, 42, 63, 125, 252]
momentum_metrics = [
    metrics.total_return,
    metrics.sharpe_ratio,
    metrics.z_score
]
qualitative_thresholds = [0.2, 0.333, 0.5]
qualitative_min_keep = [2,]
subportfolio_thresholds = [0.2, 0.333, 0.5]
subportfolio_min_keep = [3,]
max_ind_allocations = [0.4, 0.5, 0.6, 0.7]

# Define asset universe
assets = pd.read_excel(args.assetsfile)
end = datetime.date.today()
start = end - datetime.timedelta(days=(8/5)*max(lookbacks) + 10)
sym = parse_to_contracts(assets, start, end)
au = AssetUniverse(start, end, sym, offline=False, borrow_spread=1.5)

# Create subportfolios
num_subportfolios = len(lookbacks)* \
                    len(momentum_metrics)* \
                    len(subportfolio_thresholds)* \
                    len(subportfolio_min_keep)* \
                    len(max_ind_allocations)

subportfolios = [Subportfolio(params, au, assets, i, num_subportfolios) 
    for i, params in enumerate(itertools.product(
        lookbacks,
        momentum_metrics,
        subportfolio_thresholds,
        subportfolio_min_keep,
        max_ind_allocations
    ))
]

# Combine subportfolios
portfolio = Portfolio(subportfolios, au, args.nav, args.lev)

# Display
print(portfolio)
au.plot_prices()
