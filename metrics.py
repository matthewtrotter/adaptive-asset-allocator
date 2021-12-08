import pandas as pd

def total_return(prices: pd.DataFrame, returns: pd.DataFrame, lookback: int):
    """Calculate the total return over the time period.

    Returns
    -------
    metric
        The computed metric values for each asset.
    ascending: bool
        True means "higher numbers are better", otherwise False.
    """
    r = 1 + returns.iloc[-lookback:,:]
    metric = r.prod(axis=0) - 1
    ascending = True
    return metric, ascending

def sharpe_ratio(prices: pd.DataFrame, returns: pd.DataFrame, lookback: int):
    """Calculate the Sharpe ratio over the time period.

    Returns
    -------
    metric
        The computed metric values for each asset.
    ascending: bool
        True means "higher numbers are better", otherwise False.
    """
    r = 1 + returns.iloc[-lookback:,:]
    total_return = r.prod(axis=0) - 1
    stddev = returns.iloc[-lookback:].std()
    metric = total_return/stddev
    ascending = True
    return metric, ascending

def exponentially_weighted_mean_return_light_bias(prices: pd.DataFrame, returns: pd.DataFrame, lookback: int):
    """Calculate the exponentially weighted mean return with light bias towards recent 
    history over the time period.

    Returns
    -------
    metric
        The computed metric values for each asset.
    ascending: bool
        True means "higher numbers are better", otherwise False.
    """
    metric = returns.iloc[-lookback:].ewm(halflife=0.8*lookback).mean()
    metric = metric.iloc[-1,:]
    ascending = True
    return metric, ascending


def exponentially_weighted_mean_return_heavy_bias(prices: pd.DataFrame, returns: pd.DataFrame, lookback: int):
    """Calculate the exponentially weighted mean return with light bias towards recent 
    history over the time period.

    Returns
    -------
    metric
        The computed metric values for each asset.
    ascending: bool
        True means "higher numbers are better", otherwise False.
    """
    metric = returns.iloc[-lookback:].ewm(halflife=0.2*lookback).mean()
    metric = metric.iloc[-1,:]
    ascending = True
    return metric, ascending
