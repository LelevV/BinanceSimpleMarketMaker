# PingPong

A simple marketmaking algorithm using the Binance trading api. 

USE AT YOUR OWN RISK!!!

## Trading Strategy
Using a stable-coin pair with the same underlying (i.e., BUSD/USDT, with the dollar as underlying) run a 'PingPong' algorithm, where you place a bid and then an ask just ticks away from the midpoint (and by continuing this after each transaction, you create a pingpong movement :) ). The idea being that the midpoint will (in theory) always stabalize for same-underlying-stable-coin pair.

Got decent returns when no transaction costs applied. 

## Ussage
See trading.py to run the bot. The binance api keys should be stored in a config.txt file in the base folder, containing: 

{'key':<YOUR_API_KEY>, 'secret_key':<YOUR_SECRET_KEY>}. 
