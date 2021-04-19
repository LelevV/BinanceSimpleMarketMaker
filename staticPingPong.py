from binance.client import Client
from binance.enums import ORDER_TYPE_LIMIT, TIME_IN_FORCE_GTC
import pandas as pd
import time
import datetime
from order_functions import buy_limit_order, sell_limit_order, is_order_filled, cancel_order
from data import get_historic_klines


class StaticPingPong(object):

    def __init__(self, binance_client):
        self.client = binance_client

    def __str__(self):
        return f'Class: PingPongDeltaHedge instance'

    def general_test_bot(self):
        """
        Place list of general assertions to check before trading
        """
        # client status
        assert self.client.get_system_status()['msg'] == 'normal'
        assert self.client.get_account_status()['msg'] == 'Normal'
        # symbols
        assert self.main_pair_base in self.main_pair and self.main_pair_quote in self.main_pair
        # trading parameters
        assert float(self.update_interval)
        assert float(self.n_iterations)

    def order_test_bot(self):
        """
        Place list of assertions to check before order.
        """
        assert self.sell_volume >= self.min_quantity, \
            f'Not meeting min quantity for sell: {self.min_quantity}'
        assert self.buy_volume >= self.min_quantity, \
            f'Not meeting min quantity for buy: {self.min_quantity}'
        assert self.sell_volume * self.sell_price >= self.min_notional, \
            f'Not meeting min notional for sell: {self.min_notional}'
        assert self.buy_volume * self.buy_price >= self.min_notional, \
            f'Not meeting min notional for buy: {self.min_notional}'
        assert self.buy_volume >= self.min_quantity, \
            f'Not meeting min qty for buy: {self.buy_volume}'
        assert self.sell_volume >= self.min_quantity, \
            f'Not meeting min qty for sell: {self.sell_volume}'

    def print_trading_info(self):
        """
        Print trading info and print to user
        """
        self.set_trading_info()
        print('----- General Info -----')
        print()
        print('--- Fees ---')
        print(self.symbol_fee)
        print()
        print('--- Restrictions ---')
        print('Min notional:', '%f' % self.min_notional)
        print('Min price:', '%f' % self.min_price)
        print('Min quantity:', '%f' % self.min_quantity)
        print('Ticksize:', self.ticksize)
        print()
        print('--- Starting Balance --- ')
        print(f'Base balance/{self.main_pair_base}: {self.base_balance}')
        print(f'Quote balance/{self.main_pair_quote}: {self.quote_balance}')
        print()

    def print_order_info(self):
        """
        Print order info
        """
        print()
        # balance
        print('--- Balance ---')
        print('Current Balance', self.main_pair_base, self.base_balance)
        print('Current Balance', self.main_pair_quote, self.quote_balance)
        print()
        # order info
        print('--- Order Info ---')
        print('Buy Order')
        print('  Buy price:    ', self.buy_price)
        print('  Buy volume:   ', self.buy_volume)
        print('  Buy notional: ', self.buy_price * self.buy_volume)
        print('Sell Order')
        print('  Sell price:   ', self.sell_price)
        print('  Sell volume:  ', self.sell_volume)
        print('  Sell notional:', self.sell_price * self.sell_volume)
        print()

    def set_trading_parameters(self,
                               update_interval,
                               n_iterations,
                               max_order_quantity=False,
                               update_buy_if_not_filled_after=100):
        self.update_interval = update_interval
        self.n_iterations = n_iterations
        self.max_order_quantity = max_order_quantity
        self.update_buy_if_not_filled_after = update_buy_if_not_filled_after

    def set_symbols(self,
                    main_pair,
                    main_pair_base,
                    main_pair_quote):
        # main pair
        self.main_pair = main_pair
        self.main_pair_base = main_pair_base
        self.main_pair_quote = main_pair_quote

    def set_trading_info(self):
        """
        Get "general trading info from binance api
        """
        fees = pd.DataFrame(self.client.get_trade_fee()['tradeFee'])
        self.symbol_fee = fees[fees['symbol'] == self.main_pair]
        assert float(self.symbol_fee['maker']) == 0, 'fee is not zero!'

        symbol_info = self.client.get_symbol_info(self.main_pair)
        filters = pd.DataFrame(symbol_info['filters'])
        self.min_notional = float(filters[filters['filterType'] == 'MIN_NOTIONAL']['minNotional'])
        self.min_price = float(filters[filters['filterType'] == 'PRICE_FILTER']['minPrice'])
        self.min_quantity = float(filters[filters['filterType'] == 'LOT_SIZE']['minQty'])
        self.stepsize = float(filters[filters['filterType'] == 'LOT_SIZE']['stepSize'])
        self.stepsize_index = str(self.stepsize).split('.')[-1].find('1') + 1
        self.tick_index = (filters[filters['filterType'] == 'PRICE_FILTER'].iloc[0]
                           ['tickSize'].split('.')[1]
                           .find('1'))  # find index of '1' in string (e.g. in 0.0001)
        self.ticksize = self.tick_index + 1  # add 1 because of zero index in find method

        balance = pd.DataFrame(self.client.get_account()['balances'])
        self.base_balance = float(balance[balance['asset'] == self.main_pair_base]['free'])
        self.quote_balance = float(balance[balance['asset'] == self.main_pair_quote]['free'])

    def set_order_parameters(self, update_order_price=True):
        """
        Calculate and set new orders parameters
        """
        # skip price update if update_only_order_quantity == True
        if update_order_price:
            start_date = "1 day ago UTC"
            kline_interval = Client.KLINE_INTERVAL_1MINUTE
            candles = get_historic_klines(self.client,
                                          kline_interval,
                                          self.main_pair,
                                          start_date)

            price = candles['Close'].iloc[-100:].median()
            self.sell_price = round(price, self.ticksize) + 0.0001
            self.buy_price = round(price, self.ticksize)

        balance = pd.DataFrame(self.client.get_account()['balances'])
        self.base_balance = float(balance[balance['asset'] == self.main_pair_base]['free'])
        self.quote_balance = float(balance[balance['asset'] == self.main_pair_quote]['free'])

        # determine if to use min or max order quantity
        if self.max_order_quantity:
            self.sell_volume = round((self.base_balance * 0.95) / self.sell_price,
                                     self.stepsize_index)
            self.buy_volume = round((self.quote_balance * 0.95) / self.buy_price,
                                    self.stepsize_index)
        else:
            self.sell_volume = round(self.min_notional / self.sell_price + self.stepsize,
                                     self.stepsize_index)
            self.buy_volume = round(self.min_notional / self.buy_price + self.stepsize,
                                    self.stepsize_index)

    def get_current_price(self, symbol):
        return float(pd.DataFrame(self.client.get_all_tickers())
                     [lambda x: x['symbol'] == symbol]
                     ['price'])

    def set_in_position(self):
        if len(self.main_orders) == 0:
            self.main_in_position = False
        elif is_order_filled(self.client, self.main_pair, self.current_order_id):
            if self.current_order_side == 'BUY':
                self.main_in_position = True
            elif self.current_order_side == 'SELL':
                self.main_in_position = False

    def bot_limit_buy_order(self):
        self.set_order_parameters()
        self.order_test_bot()
        self.print_order_info()
        print('Placing limit buy order...')
        order_id = buy_limit_order(self.client,
                                   pair_symbol=self.main_pair,
                                   time_in_force=TIME_IN_FORCE_GTC,
                                   buy_volume=self.buy_volume,
                                   buy_price=self.buy_price)
        self.current_order_id = order_id
        self.current_order_side = 'BUY'
        self.main_orders.append(order_id)

    def bot_limit_sell_order(self):
        self.order_test_bot()
        self.set_order_parameters(update_order_price=False)
        self.print_order_info()
        print('Placing limit sell order...')
        order_id = sell_limit_order(self.client,
                                    pair_symbol=self.main_pair,
                                    time_in_force=TIME_IN_FORCE_GTC,
                                    sell_volume=self.sell_volume,
                                    sell_price=self.sell_price)
        self.current_order_id = order_id
        self.current_order_side = 'SELL'
        self.main_orders.append(order_id)

    def trading_cycle(self):
        self.set_in_position()
        if len(self.main_orders) == 0:
            # 1) place main buy limit order
            self.bot_limit_buy_order()
        elif self.current_order_side == 'SELL':
            # if main sell was filled
            if is_order_filled(self.client, self.main_pair, self.current_order_id):
                # 1) set new main buy limit order
                self.bot_limit_buy_order()
        elif self.current_order_side == 'BUY':
            # update counter for buy order
            self.n_rounds_buy_not_filled += 1
            # if main buy was filled
            if is_order_filled(self.client, self.main_pair, self.current_order_id):
                # 1) set last buy price
                self.last_buy_price = self.buy_price
                # 2) set new main sell limit order
                self.bot_limit_sell_order()
                # 3) set counter to zero
                self.n_rounds_buy_not_filled = 0
            # if buy was not filled after given rounds; cancel order and update
            elif self.n_rounds_buy_not_filled >= self.update_buy_if_not_filled_after:
                # set counter to zero
                self.n_rounds_buy_not_filled = 0
                try:
                    # 1) cancel current buy limit
                    cancel_order(self.client, self.main_pair, self.current_order_id)
                    # 2) set new main buy limit
                    self.bot_limit_buy_order()
                except Exception as e:
                    print('Error occured during order cancel:', e)

    def start_trading_session(self):
        self.general_test_bot()
        self.set_trading_info()
        self.n_rounds_buy_not_filled = 0
        self.main_orders = []
        self.current_order_id = None
        self.current_order_side = None
        self.main_in_position = False

        self.print_trading_info()
        for i in range(self.n_iterations):
            print(f'\n------- Tradin Cycle {i + 1} -------')
            print(datetime.datetime.now())
            print('Trading cycle...')
            try:
                self.trading_cycle()
            except Exception as e:
                print('Error during trading cycle occured:', e)
            print(f'Main in position: {self.main_in_position}')
            if not self.main_in_position:
                print(f'{self.n_rounds_buy_not_filled} of max {self.update_buy_if_not_filled_after} rounds not filled.')
            print(f'Cycle is Done, wait for {self.update_interval} seconds.')
            time.sleep(self.update_interval)
        print('--- FINISHED ---')
