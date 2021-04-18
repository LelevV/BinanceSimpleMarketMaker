from account import get_binance_client, get_trading_info
from staticPingPong import StaticPingPong
from binance.client import Client
import matplotlib.pyplot as plt
from ta.momentum import RSIIndicator
import pandas as pd

if __name__ == '__main__':

    BASE_SYMBOL = 'BUSD'
    QUOTE_SYMBOL = 'USDT'
    PAIR_SYMBOL = 'BUSDUSDT'

    UPDATE_INTERVAL = 10
    N_ITERATIONS = 10000

    client = get_binance_client()
    kline_interval = Client.KLINE_INTERVAL_1MINUTE
    trading_info = get_trading_info(client, PAIR_SYMBOL, 'BUSD', 'USDT')
    for key, value in trading_info.items():
        print(key, value)

    pingpong = StaticPingPong(client)
    pingpong.set_trading_parameters(UPDATE_INTERVAL,
                                    N_ITERATIONS)

    pingpong.set_symbols(PAIR_SYMBOL,
                         BASE_SYMBOL,
                         QUOTE_SYMBOL)

    pingpong.start_trading_session()













