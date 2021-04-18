from binance.client import Client
import json
import pandas as pd


def get_binance_client():
    # get api credentials and start binance client
    with open('config.txt') as f:
        json_data = json.load(f)
    api_key = json_data['key']
    api_secret = json_data['secret_key']
    return Client(api_key, api_secret)


def get_trading_info(client, symbol, base, quote):
    """
    Get "general trading info from binance api
    """
    fees = pd.DataFrame(client.get_trade_fee()['tradeFee'])
    symbol_fee = fees[fees['symbol'] == symbol]

    symbol_info = client.get_symbol_info(symbol)
    filters = pd.DataFrame(symbol_info['filters'])
    min_notional = float(filters[filters['filterType'] == 'MIN_NOTIONAL']['minNotional'])
    min_price = float(filters[filters['filterType'] == 'PRICE_FILTER']['minPrice'])
    min_quantity = float(filters[filters['filterType'] == 'LOT_SIZE']['minQty'])
    stepsize = float(filters[filters['filterType'] == 'LOT_SIZE']['stepSize'])
    stepsize_index = str(stepsize).split('.')[-1].find('1') + 1
    tick_index = (filters[filters['filterType'] == 'PRICE_FILTER'].iloc[0]
                  ['tickSize'].split('.')[1]
                  .find('1'))  # find index of '1' in string (e.g. in 0.0001)
    ticksize = tick_index + 1  # add 1 because of zero index in find method

    balance = pd.DataFrame(client.get_account()['balances'])
    base_balance = float(balance[balance['asset'] == base]['free'])
    quote_balance = float(balance[balance['asset'] == quote]['free'])
    return {
        'symbol_fee': symbol_fee,
        'min_notional': min_notional,
        'min_price': min_price,
        'min_quantity': min_quantity,
        'stepsize': stepsize,
        'stepsize_index': stepsize_index,
        'tick_index': tick_index,
        'ticksize': ticksize,
        'base_balance': base_balance,
        'quote_balance': quote_balance
    }