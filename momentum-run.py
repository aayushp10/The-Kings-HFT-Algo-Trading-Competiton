import shift
from time import sleep
from datetime import datetime, timedelta, time
import numpy as np
from typing import Dict, Any, Tuple, List
from scipy.stats import linregress
from threading import Thread
from multiprocessing import Manager
import multiprocessing as mp
from collections import deque
from components.routine_summary import routine_summary
import math
import sys
sys.path.insert(1, '../')
import credentials
import datetime as dt
import pandas as pd

tickers = [
'AAPL',
'AXP',
'BA',
'CAT',
'CSCO',
'CVX',
'DIS',
'DWDP',
'GS',
'HD',
'IBM',
'INTC',
'JNJ',
'JPM',
'KO',
'MCD',
'MMM',
'MRK',
'MSFT',
'NKE',
'PFE',
'PG',
'TRV',
'UNH',
'UTX',
'V',
'VZ',
'WBA',
'WMT',
'XOM'
]
prices_key = 'prices'
stop_loss_key = 'stop_losses' 
# target_key = 'targets' 
target_key = 'target_hit_and_curr_stop_loss_perc' 
trader_key = 'trader' 
sys.path.append('../')

def run_save_prices(ticker: str, trader: shift.Trader, state: Dict[str, Any]) -> None:
    """
    save prices for a given ticker to the state
    """
    queue_size = 30
    frequency = 60
    # if prices_key not in state:
    #     state[prices_key] = {}

    print = False
    while True:
        price = trader.get_last_price(ticker)
        try:
            state[prices_key][ticker] += [trader.get_last_price(ticker)]
        except KeyError:
            state[prices_key][ticker] = deque(maxlen=queue_size)
            sleep(0.5)
            state[prices_key][ticker] += [trader.get_last_price(ticker)]
        
        
        #     # print(f"Prices Stored: {state[prices_key][ticker]}")
        #     print(f"Last Price: {trader.get_last_price(ticker)}")
            # print(f"updated prices for AAPL @ {trader.get_last_trade_time()} there are {len(state[prices_key][ticker])} entries for price - last price {price}")
        # print(f"{ticker} PRICE UPDATED")
        sleep(frequency)
        


def run_stop_loss_check(trader: shift.Trader, state: Dict[str, Any]) -> None:
    """
    check for stop loss hit
    """
    
    stop_loss_interval = 5 # seconds
    acceptable_loss = .2 # percent

    # if stop_loss_key not in stop_losses_state:
    #     stop_losses_state = {}
    '''
    Set original stop loss when originally buying to -.2%
    Set original target when originally buying to the bollinger band 
    Update target every minute to the most recent bollinger band 
    First time you hit target:
        remove half position
        update stop loss to original buy prices and make this a trailing stop
    Keep updating target
    

    Scenario:
    Buy 100 at 100
    Set stop loss to 99.8 and target to 101
    We hit 101 so we sell 50 (left with 50) and update stop loss to 100
    101 - 100 = stop loss

    Next minute upper band changes to 102: change target to 102 
    Next minute upper band changes to 99: sell everything
    ALREADY HIT TARGET ONCE: We hit 102 so we sell 25 (left with 25) and update stop loss to 101
    price goes to 101.50, stop loss is 101
    price hits target at 104, stop loss is 103.50
    

    begin position
    initial_buy_price = ...
    target = upper_bollinger_band[-1]
    stop_loss = initial_buy_price*-.002

    first target hits
    stop_loss = (1 - ((first_target_sell - initial_buy_price) / initial_buy_price))*current_price

    price goes up
    stop_loss = (1 - ((first_target_sell - initial_buy_price) / initial_buy_price))*current_price
    
    second target hits - just half, and reapply trailing stop loss
    
    
    stop_loss = (1 - ((first_target_sell - initial_buy_price) / initial_buy_price))*current_price

    price goes down
    stop_loss = stop_loss

    
    '''
    while True:

        sleep(stop_loss_interval)

        for item in trader.get_portfolio_items().values():
            ticker = item.get_symbol()
            current_price = state[prices_key][ticker][-1]
            new_stop_loss = current_price * ((100 - acceptable_loss) / 100.)
            has_stop_loss = ticker in state[stop_loss_key]
            if not has_stop_loss or new_stop_loss > state[stop_loss_key][ticker]:
                if has_stop_loss:
                    for order in trader.get_waiting_list():
                        if order.symbol == ticker and order.type == shift.Order.Type.LIMIT_SELL:
                            trader.submit_cancellation(order)
                limit_sell = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, item.get_shares())
                trader.submit_order(limit_sell)
                state[stop_loss_key][ticker] = new_stop_loss, limit_sell



def get_momentum(prices: np.array) -> float:
    """
    gets momentum given prices
    """
    returns = np.log(prices)
    x = np.arange(len(returns))
    slope, _, rvalue, _, _ = linregress(x, returns)
    return ((1 + slope) * (rvalue ** 2))


def get_should_long(prices: np.array) -> Tuple[float, float]:

    # use window to calculate moving avg and moving standard deviation
    prices_series = pd.Series(prices)
    if(len(prices) > 22):
        fast = 9
        slow = 21

        prev_moving_avg_slow = pd.Series(prices[:-1]).rolling(slow).mean()
        prev_moving_avg_fast = pd.Series(prices[:-1]).rolling(fast).mean()

        moving_avg_fast = pd.Series(prices).rolling(fast).mean()
        moving_avg_slow = pd.Series(prices).rolling(slow).mean()
        
        moving_std = pd.Series(prices).rolling(slow).std()
        
        bollinger_high = moving_avg_slow + (2 * moving_std)
        bollinger_low = moving_avg_slow - (2 * moving_std)
        return {
            "last_bollinger_band_high": bollinger_high,
            "last_bollinger_band_low": bollinger_low,
            "bollinger_band_high_difference":  (prices_series.iloc[-1] - bollinger_high.iloc[-1]),
            "bollinger_band_low_difference":  (prices_series.iloc[-1] - bollinger_low.iloc[-1]),
            "ema_difference": (moving_avg_fast.iloc[-1] - moving_avg_slow.iloc[-1])/prices_series.iloc[-1],
            "prev_ema_difference": (prev_moving_avg_fast.iloc[-1] - prev_moving_avg_slow.iloc[-1])/prices_series.iloc[-2],
        }
    return None

    # 21 EMA and 9 EMA cross? (If last period 9EMA-21EMA < 0, and current period 9EMA-21EMA > 0, then we take a start
    # long position)
    # Store initial buying price as a variable.
    # Store rbitrary stop loss price at buying point (0.2%) as a variable
    # If initial stop loss hits, sell all shares of the position
    # If price >= Upper 2-SD Bollinger Band, sell half of current position for profit
        # Then move intial stop loss to the initial buying price and make this a trailing stop loss until the entire
    # position is closed
    # If price >= Upper 2-SD Bollinger Band again, sell half of current position for profit
        # Contuinue this as long as current position >= 100 shares (make sure we never go below 100 shares or we won't
    # be able to close the position)
        # Or until it is 3:30
            # f it is 3:30, then close the entire position
    # If price <= trailing stop loss price, sell all of the current position


def run_trades(trader: shift.Trader, state: Dict[str, Any]) -> None:
    """
    run buy / sell trades
    """
    run_trades_interval = 60 # seconds
    maxLoss = 0.01
    while True:
        # if (len())
        unsorted_differences: List[float] = []
        unsorted_tickers: List[str] = []
        for ticker in tickers:
            print(f"entered run trades: {ticker}")
            if (ticker not in state[prices_key]) or len(list(state[prices_key][ticker])) < 22:
                # print(f"have {len(list(state[prices_key][ticker]))} prices for {ticker}...moving on")
                continue
            prices = np.array(list(state[prices_key][ticker]))
            # print(f"Prices({len(prices)}): {prices} ")
            should_long = get_should_long(prices)
            if(should_long is None):
                # print(f"should_long is None {ticker}")
                continue
            ema_difference = should_long["ema_difference"]
            prev_ema_difference = should_long["prev_ema_difference"]
            # print(f"emaaaaa {ticker}: {ema_difference}")
            unsorted_differences.append(ema_difference)  
            unsorted_tickers.append(ticker)  
        
        if(len(unsorted_differences) < 5):
            sleep(5)
            continue
        print(unsorted_differences)
        print(unsorted_tickers)
        _, ranked_tickers = (reversed(list(t)) for t in zip(*sorted(zip(unsorted_differences, unsorted_tickers))))

        for ticker in ranked_tickers:
            prices = np.array(list(state[prices_key][ticker]))
            should_long = get_should_long(prices)
            if(should_long is None):
                sleep(1)
                continue
            ema_difference = should_long["ema_difference"]
            price_minus_bollinger_high = should_long["bollinger_band_high_difference"]
            price_minus_bollinger_low = should_long["bollinger_band_low_difference"]
            last_upper_bollinger_band = should_long["last_bollinger_band_high"]
            last_lower_bollinger_band = should_long["last_bollinger_band_low"]
            item = trader.get_portfolio_item(ticker)
            if item.get_shares() > 0:
                # check to sell
                target_hit_count = state[target_key][ticker][0]
                if ema_difference < 0:
                    cancel_all_trades(trader, ticker)
                    sleep(2)
                    print(f"{ticker} : HAVE SHARES, EMA CROSSED DOWN, SELL")
                    sell = shift.Order(shift.Order.Type.MARKET_SELL, ticker, int(item.get_shares()/100.0))
                    trader.submit_order(sell)

                # over band, never hit
                elif price_minus_bollinger_high > 0 and target_hit_count == 0:
                    cancel_all_trades(trader, ticker)
                    sleep(2)
                    s = item.get_shares()                    
                    print(f"{ticker} : HAVE SHARES, FIRST TARGET HIT, SELL HALF")
                    sell = shift.Order(shift.Order.Type.MARKET_SELL, ticker, int(math.ceil((s/2) / 100.0)))
                    trader.submit_order(sell)
                    sleep(5)
                    #check if you didn't happen to sell all due to minimum lot
                    if int(math.ceil((item.get_shares()/2) / 100.0)) < int(s/100):

                        lastPrice = trader.get_last_price(ticker)
                        initial_buy_price = item.get_price()
                        #keep track of this in state
                        trailing_stop_perc = (lastPrice - initial_buy_price) / initial_buy_price
                        trailing_stop_price = (1 - trailing_stop_perc) * lastPrice
                        print(f"{ticker} : HAVE SHARES, FIRST TARGET HIT, RESETTING LIMIT SELL")
                        sell = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, int(math.ceil((item.get_shares()/2) / 100.0)), trailing_stop_price)
                        trader.submit_order(sell)
                        state[target_key][ticker] = [target_hit_count + 1, trailing_stop_perc]
                    
            
                elif target_hit_count > 0:
                    sold = 0
                    if price_minus_bollinger_low > 0:
                        cancel_all_trades(trader, ticker)
                        sleep(2)
                        sold = int(math.ceil((item.get_shares()/2) / 100.0))
                        print(f"{ticker} : HAVE SHARES, OVER FIRST TARGET HIT, TAKING MORE PROFIT SINCE STILL ABOVE BOLLINGER, SELL HALFT")
                        sell = shift.Order(shift.Order.Type.MARKET_SELL, ticker, sold)
                        trader.submit_order(sell)
                        sleep(5)
                    if sold < int(item.get_shares()/100):
                        
                        lastPrice = trader.get_last_price(ticker)

                        avg_last_two_prices = (state[prices_key][ticker][-2] + state[prices_key][ticker][-1]) / 2.
                        
                        if lastPrice >= avg_last_two_prices:
                            cancel_all_trades(trader, ticker)
                            sleep(2)
                            # keep same percentarange and update the loss PRICE
                            trailing_stop_perc = state[target_key][ticker][1]
                            trailing_stop_price = (1 - trailing_stop_perc) * lastPrice
                            print(f"{ticker} : HAVE SHARES, OVER FIRST TARGET HIT, SOLD MORE PROFIT SINCE STILL ABOVE BOLLINGER, STILL HAVE MORE, RESETTING LIMIT")
                            sell = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, item.get_shares() / 100.0, trailing_stop_price)
                            trader.submit_order(sell)
                            sleep(5)
                        else:
                            pass
            elif item.get_shares() < 0:
                #check to see if we need to exit short positions
                target_hit_count = state[target_key][ticker][0]

                if ema_difference > 0:
                    cancel_all_trades(trader, ticker)
                    sleep(2)
                    buy = Shift.Order(shift.Order.Type.MARKET_BUY, ticker, -1*int(item.get_shares()/100.0))
                    trader.submit_order(buy)


                elif price_minus_bollinger_low < 0 and target_hit_count == 0:
                    cancel_all_trades(trader, ticker)
                    sleep(2)
                    s = item.get_shares()
                    buy = shift.Order(shift.Order.Type.MARKET_BUY, ticker, -1*int(math.ceil((s/2) / 100.0)))
                    trader.submit_order(buy)
                    sleep(5)
                    #check if you happen to buy all back due to minimum lot
                    #if still have short positions, reset limit buy
                    if -1*int(math.ceil((item.get_shares()/2) / 100.0)) < -1*int(s/100) :
                        lastPrice = trader.get_last_price(ticker)
                        initial_sell_price = item.get_price()
                        trailing_stop_perc = (lastPrice - initial_sell_price) / initial_sell_price
                        trailing_stop_price = (1 + trailing_stop_perc) * lastPrice
                        buy = shift.Order(shift.Order.Type.LIMIT_BUY, ticker, int(math.ceil((item.get_shares()/2) / 100.0)), trailing_stop_price)
                        trader.submit_order(buy)
                        state[target_key][ticker] = [target_hit_count + 1, trailing_stop_perc]

                #no close of position at all, so we just wanna reset the trailing stop loss
                elif target_hit_count > 0:
                    bought = 0
                    if price_minus_bollinger_low < 0:
                        cancel_all_trades(trader, ticker)
                        sleep(2)
                        bought = -1*int(math.ceil((item.get_shares()/2) / 100.0))
                        buy = shift.Order(shift.Order.Type.MARKET_BUY, ticker, bought)
                        trader.submit_order(buy)
                        sleep(5)
                    if bought < -1*int(item.get_shares() / 100.0):
                        lastPrice = trader.get_last_price(ticker)
                        avg_last_two_prices = (state[prices_key][ticker][-2] + state[prices_key][ticker][-1]) / 2.
                        # keep same percentarange and update the loss PRICE
                        #TODO: fix a dollar amount instead of percentage
                        if lastPrice <= avg_last_two_prices:
                            cancel_all_trades(trader, ticker)
                            sleep(2)
                            trailing_stop_perc = state[target_key][1]
                            trailing_stop_price = (1 + trailing_stop_perc) * lastPrice
                            buy = shift.Order(shift.Order.Type.LIMIT_BUY, ticker, item.get_shares() / 100.0, trailing_stop_price)
                            trader.submit_order(buy)
                        else: 
                            pass         
            else:
                #reset target_hit_count because no shores no more
                state[target_key][ticker] = [0,0]
                for order in trader.get_waiting_list():
                    if order.symbol == ticker and order.type == shift.Order.Type.MARKET_BUY:
                        trader.submit_cancellation(order)
                sleep(2)
                if ema_difference > 0 and prev_ema_difference < 0:
                    bp = trader.get_portfolio_summary().get_total_bp()
                    amount = 200e3
                    if bp >= amount:
                        lastPrice = trader.get_last_price(ticker)
                        s = int((amount / lastPrice) / 100.)
                        buy = shift.Order(shift.Order.Type.MARKET_BUY, ticker, s)
                        initial_buy_price = trader.get_last_price(ticker)
                        initial_stop_loss = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, s, trader.get_last_price(ticker)*(1-maxLoss))
                        print(f"{ticker} : DONT HAVE SHARES, HIT TARGET, HAVE BP, BUY")
                        trader.submit_order(buy)
                        sleep(5)
                        print(f"{ticker} : DONT HAVE SHARES, HIT TARGET, HAVE BP, SETTING INITIAL STOP LOSS")
                        trader.submit_order(initial_stop_loss)
                elif ema_difference < 0:
                    bp = trader.get_portfolio_summary().get_total_bp()
                    short_profit, long_profit = get_unrealized_pl(trader)
                    #lost money on shorts
                    amount = (200e3 / 2)
                    amount_to_subtract = 0
                    if short_profit < 0:
                        amount_to_subtract += (-1*short_profit)
                    
                    if (0.995 * (amount - amount_to_subtract)) < bp:
                        lastPrice = trader.get_last_price()
                        s = int((amount / lastPrice) / 100.)
                        sell = shift.Order(shift.Order.Type.MARKET_SELL, ticker, s)
                        initial_sell_price = trader.get_last_price(ticker)
                        initial_stop_loss = shift.Order(shift.Order.Type.LIMIT_BUY, ticker, trader.get_last_price(ticker)*(1+maxLoss), s)
                        trader.submit_order(sell)
                        sleep(5)
                        trader.submit_order(initial_stop_loss)

            sleep(5)
        sleep(run_trades_interval)

def cancel_all_trades(trader: shift.Trader, ticker: str):
    for o in trader.get_waiting_list():
        if(o.symbol == ticker):
            trader.submit_cancellation(o)
    
def run_processes(trader: shift.Trader, state: Dict[str, Any]) -> List[Thread]:
    """
    create all the threads
    """


    processes = []

    #processes.append(Thread(target=run_stop_loss_check, args=(trader, state[prices_key], state[stop_loss_key])))
    processes.append(Thread(target=run_trades, args=(trader, state)))
    processes.append(Thread(target=routine_summary, args=(trader,)))

    for process in processes:
       process.start()

    return processes


def stop_processes(processes: List[Thread]) -> None:
    """
    stop all the threads
    """
    for process in processes:
        process.join(timeout=1)

# 1 thread to periodically calculate momentums & figure out if it's time to buy or sell
# 1 thread for stop losses

def main(trader: shift.Trader) -> None:
    """
    main entrypoint
    """
    # {

    #     "prices": {
    #         "AAPL": [234]
    #     },
        
    # }
    manager = Manager()
    list_of_shared_dicts = manager.list()
    list_of_shared_dicts.append({})
    # prices_state = list_of_shared_dicts[0]
    # stop_losses_state = list_of_shared_dicts[1]
    state = list_of_shared_dicts[0]
    keys_in_state = [prices_key, stop_loss_key, target_key]


    for key in keys_in_state:
        state[key] = manager.dict() 
        for ticker in tickers:
            if key == prices_key:
                state[key].setdefault(key, [])
            elif key == target_key:    
                state[key].setdefault(key, [0,0])
            # if key == stop_loss_key:
    # state[trader_key] = trader
    # trader_obj = state
    check_time = 1 # minutes
    current = trader.get_last_trade_time()
    start_time = datetime.combine(current, dt.time(10,0,0))
    end_time = datetime.combine(current, dt.time(15, 30, 0))

    print(trader.get_last_trade_time())


    pre_processes = []

    for ticker in tickers:
        # 1 thread per ticker getting price data & saving it
        pre_processes.append(Thread(target=run_save_prices, args=(ticker, trader, state)))
        # run_save_prices(ticker, trader, state)

    for process in pre_processes:
        process.start()


    print(f"{len(pre_processes)} processes created for run_save_prices")

    while trader.get_last_trade_time() < start_time:
        print(f"Waiting for Market Open @ {trader.get_last_trade_time()}")
        sleep(check_time * 60)


    processes = pre_processes.extend(run_processes(trader, state))

    while trader.get_last_trade_time() < end_time:
        print(f"Waiting for Market Close @ {trader.get_last_trade_time()}")
        sleep(check_time * 60)

    for order in trader.get_waiting_list():
        trader.submit_cancellation(order)

    for item in trader.get_portfolio_items().values():
        ticker = item.get_symbol()
        sell = shift.Order(shift.Order.Type.MARKET_SELL, ticker, item.get_shares())
        trader.submit_order(sell)

    time_wait_sell = 60 # seconds
    sleep(time_wait_sell)

    stop_processes(processes)

    # print stuff
    routine_summary(trader)

# bad_year = 1969

if __name__ == '__main__':
    # year = bad_year
    # curr_try, num_tries = 1, 1000

    sleep(5)
    trader = shift.Trader(credentials.my_username)


    try:
        trader.connect("initiator.cfg", credentials.my_password)
        trader.sub_all_order_book()
    except shift.IncorrectPasswordError as e:
        print(e)
    except shift.ConnectionTimeoutError as e:
        print(e)


    sleep(15)
    # while year == bad_year:
    #     print(f'try {curr_try}')
    #     if curr_try == num_tries:
    #         raise RuntimeError('1969 error...')
    #     trader = shift.Trader(credentials.my_username)
    #     try:
    #         trader.connect("initiator.cfg", credentials.my_password)
    #         trader.sub_all_order_book()
    #     except shift.IncorrectPasswordError as e:
    #         print(e)
    #     except shift.ConnectionTimeoutError as e:
    #         print(e)
    #     year = trader.get_last_trade_time().year
    #     sleep(2)
    #     curr_try += 1

    main(trader)
