import pandas as pd

def total_return(prices: pd.DataFrame, lookback: int):
    """[summary]

    Returns
    -------
    metric
        The computed metric values for each asset.
    ascending: bool
        True means "higher numbers are better", otherwise False.
    """
    metric = prices.iloc[-1] - prices.iloc[-(lookback-1)]
    ascending = True
    return metric, ascending

def sharpe_ratio(prices: pd.DataFrame, lookback: int):
    pass
