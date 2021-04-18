import pandas as pd


def buy_limit_order(client, pair_symbol, time_in_force, buy_volume, buy_price):
    order = client.order_limit_buy(symbol=pair_symbol,
                                   timeInForce=time_in_force,
                                   quantity=buy_volume,
                                   price=buy_price)
    order_id = order["orderId"]
    return order_id


def sell_limit_order(client, pair_symbol, time_in_force, sell_volume, sell_price):
    order = client.order_limit_sell(symbol=pair_symbol,
                                    timeInForce=time_in_force,
                                    quantity=sell_volume,
                                    price=sell_price)
    order_id = order["orderId"]
    return order_id


def buy_market_order(client, pair_symbol, buy_volume):
    order = client.order_market_buy(symbol=pair_symbol,
                                    quantity=buy_volume)
    order_id = order["orderId"]
    return order_id


def sell_market_order(client, pair_symbol, sell_volume):
    order = client.order_market_sell(symbol=pair_symbol,
                                     quantity=sell_volume)
    order_id = order["orderId"]
    return order_id


def cancel_order(client, pair_symbol, order_id):
    client.cancel_order(symbol=pair_symbol, orderId=order_id)


def is_order_filled(client, pair_symbol, order_id):
    all_orders = pd.DataFrame(client.get_all_orders(symbol=pair_symbol))
    current_order = all_orders[all_orders['orderId'] == order_id]
    is_filled = 'FILLED' in list(current_order['status'])
    return is_filled

