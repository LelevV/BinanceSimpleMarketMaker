from account import get_binance_client, get_trading_info
from data import get_historic_klines
from staticPingPong import StaticPingPong
from binance.client import Client
import matplotlib.pyplot as plt
from ta.momentum import RSIIndicator
import pandas as pd

symbol = 'BUSDUSDT'
client = get_binance_client()
kline_interval = Client.KLINE_INTERVAL_1MINUTE
trading_info = get_trading_info(client, symbol, 'BUSD', 'USDT')
for key, value in trading_info.items():
    print(key, value)

start_date = '1 day ago UTC' #'2021-04-01'
candles = get_historic_klines(client, kline_interval, symbol, start_date)
rsi_window = 10
rsi_col_name = f'RSI{str(rsi_window)}'
candles[rsi_col_name] = RSIIndicator(close=candles["Close"], window=rsi_window).rsi()
print(candles.iloc[0])

fig, axes = plt.subplots(nrows=2, ncols=1)
title = f'{symbol} - {kline_interval}'
ax = candles.plot('OpenTimeCEST', 'Close', title=title, ax=axes[0])
candles.plot('OpenTimeCEST', rsi_col_name, alpha=0.6, secondary_y=True, ax=ax)
plt.axhline(100, linestyle='--', alpha=0.1)
plt.axhline(80, linestyle='--')
plt.axhline(60, linestyle='--', alpha=0.2)
plt.axhline(40, linestyle='--', alpha=0.2)
plt.axhline(20, linestyle='--')
plt.axhline(0, linestyle='--', alpha=0.1)

rsi_buy_signal = 40
rsi_sell_signal = 60
df = (candles
      .assign(buySignal=lambda x: x[rsi_col_name] <= rsi_buy_signal,
              sellSignal=lambda x: x[rsi_col_name] >= rsi_sell_signal,
              rollingMedian=lambda x: x['Close'].rolling(100).median()))

gross_capital = 0
net_capital = 0
static_capital = 0
in_position = False
in_position_price = 0
in_position_col = []
gross_capital_col = []
net_capital_col = []
in_position_static = False
in_position_price_static = 0
static_capital_col = []
for index, row in df.iterrows():
    # rsi
    if row['buySignal'] and not in_position:
        in_position = True
        in_position_price = row['Close']
    elif in_position and row['sellSignal']:
        in_position = False
        profit = (row['Close'] - in_position_price)
        gross_capital += profit
        net_capital += profit - (0.0001 + (row['Close'] - in_position_price) * 0.001)

    # static limits
    if not in_position_static:
        static_buy = row['rollingMedian'] #- 0.0001
        static_sell = row['rollingMedian'] + 0.0001
    # static_buy = 0.9984
    # static_sell = 0.9985
    print(row['OpenTimeCEST'], 'Close', row['Close'], ' - buy:', static_buy, ' - sell:', static_sell)
    if row['Close'] <= static_buy and not in_position_static:
        in_position_static = True
        in_position_price_static = row['Close']
    elif in_position_static and row['Close'] >= static_sell:
        in_position_static = False
        profit = (row['Close'] - in_position_price_static)
        static_capital += profit

    in_position_col.append(in_position)
    gross_capital_col.append(gross_capital)
    net_capital_col.append(net_capital)
    static_capital_col.append(static_capital)
    # print(capital)

df['inPosition'] = in_position_col
df['GrossCapital'] = gross_capital_col
df['NetCapital'] = net_capital_col
df['StaticCapital'] = static_capital_col

df.plot('OpenTimeCEST', ['GrossCapital', 'NetCapital', 'StaticCapital'], ax=axes[1])
plt.show()