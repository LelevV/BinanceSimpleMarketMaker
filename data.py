import pandas as pd


def get_historic_klines(client, client_kline, symbol, start_date):
    # get klines from api
    candles = client.get_historical_klines(symbol=symbol,
                                           interval=client_kline,
                                           start_str=start_date)
    kline_cols = [
        'OpenTime',
        'Open',
        'High',
        'Low',
        'Close',
        'Volume',
        'CloseTime',
        'QuoteAssetVolume',
        'NumberOfTrades',
        'TakerBuyBaseAssetVolume',
        'TakerBuyQuoteAssetVolume',
        'Ignore'
    ]
    candles = (pd.DataFrame(candles, columns=kline_cols)
        .assign(
        # process time cols
        OpenTime=lambda x: pd.to_datetime(x['OpenTime'], unit='ms').dt.tz_localize('utc'),
        CloseTime=lambda x: pd.to_datetime(x['CloseTime'], unit='ms').dt.tz_localize('utc'),
        OpenTimeCEST=lambda x: x['OpenTime'].dt.tz_convert('Europe/Amsterdam'),
        CloseTimeCEST=lambda x: x['CloseTime'].dt.tz_convert('Europe/Amsterdam'),
        # process price cols
        Open=lambda x: x['Open'].astype(float),
        High=lambda x: x['High'].astype(float),
        Low=lambda x: x['Low'].astype(float),
        Close=lambda x: x['Close'].astype(float),
        # process quantity cols
        QuoteAssetVolume=lambda x: x['QuoteAssetVolume'].astype(float),
        NumberOfTrades=lambda x: x['NumberOfTrades'].astype(float),
        TakerBuyBaseAssetVolume=lambda x: x['TakerBuyBaseAssetVolume'].astype(float),
        TakerBuyQuoteAssetVolume=lambda x: x['TakerBuyQuoteAssetVolume'].astype(float))
    )
    return candles


def get_all_pairs_containing_coin(client, coin):
    info = client.get_exchange_info()
    symbols = pd.DataFrame(info['symbols'])
    active_symbols = symbols[symbols['status'] == 'TRADING']
    return active_symbols[active_symbols['symbol'].str.contains(coin)]


def get_rate_limit(client):
    info = client.get_exchange_info()
    return pd.DataFrame(info['rateLimits'])
