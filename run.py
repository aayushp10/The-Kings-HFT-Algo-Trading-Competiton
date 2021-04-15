import shift
from time import sleep
from datetime import datetime, timedelta, time
import numpy as np
from typing import Dict, Any, Tuple, List
from scipy.stats import linregress
from multiprocessing import Process, Manager
import multiprocessing as mp
from collections import deque
from components.routine_summary import routine_summary
import math
import sys
sys.path.insert(1, '../')
import credentials
import datetime as dt

tickers = [
'AAPL',
'AXP',
'BA',
# 'CAT',
# 'CSCO',
# 'CVX',
# 'DIS',
# 'DWDP',
# 'GS',
# 'HD',
# 'IBM',
# 'INTC',
# 'JNJ',
# 'JPM',
# 'KO',
# 'MCD',
# 'MMM',
# 'MRK',
# 'MSFT',
# 'NKE',
# 'PFE',
# 'PG',
# 'TRV',
# 'UNH',
# 'UTX',
# 'V',
# 'VZ',
# 'WBA',
# 'WMT',
# 'XOM'
]
prices_key = 'prices'
stop_loss_key = 'stop_losses' 
# target_key = 'targets' 
target_key = 'target_hit_and_curr_stop_loss_perc' 
sys.path.append('../')

def run_save_prices(ticker: str, trader: shift.Trader, state: Dict[str, Any]) -> None:
    """
    save prices for a given ticker to the state
    """
    queue_size = 30

    # if prices_key not in state:
    #     state[prices_key] = {}

    
    while True:
        price = trader.get_last_price(ticker)
        try:
            state[prices_key][ticker].extend([price])
        except KeyError:
            state[prices_key][ticker] = deque(maxlen=queue_size)
            sleep(0.5)
            state[prices_key][ticker].extend([price])
        
        sleep(5)
        


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

    fast = 9
    slow = 20

    moving_avg_fast = np.Series(prices).rolling(fast).mean()
    moving_avg_slow = np.Series(prices).rolling(slow).mean()
    
    moving_std = np.Series(prices).rolling(slow).std()
    
    bollinger_high = moving_avg_slow + (2 * moving_std)
    bollinger_low = moving_avg_slow - (2 * moving_std)

    return {
        "last_bollinger_band_high": bollinger_high[-1],
        "bollinger_band_difference":  (prices[-1] - bollinger_high[-1]),
        "ema_difference": (moving_avg_fast[-1] - moving_avg_slow[-1])/prices[-1],
    }
    

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
    run_trades_interval = 30 # seconds
    maxLoss = 0.002
    while True:

        unsorted_differences: List[float] = []
        unsorted_tickers: List[str] = []
        for ticker in tickers:
            if (ticker not in state[price_key]) or len(list(state[prices_key][ticker])) < 21:
                sleep(5)
                continue
            prices = np.array(list(state[prices_key][ticker]))
            should_long = get_should_long(prices)
            ema_difference = should_long["ema_difference"]
            unsorted_differences.append(ema_difference)  
            unsorted_tickers.append(ticker)  

        _, ranked_tickers = map(list, zip(*sorted(zip(unsorted_differences, unsorted_tickers))))

        for ticker in ranked_tickers:
            prices = np.array(list(state[prices_key][ticker]))
            should_long = get_should_long(prices)
            ema_difference = should_long["ema_difference"]
            price_minus_bollinger = should_long["bollinger_band_difference"]
            last_upper_bollinger_band = should_long["last_bollinger_band_high"]
            item = trader.get_portfolio_item(ticker)
            if item.get_shares() > 0:
                # check to sell
                if ema_difference < 0:
                    cancel_all_trades(trader, ticker)
                    sell = shift.Order(shift.Order.Type.MARKET_SELL, ticker, int(item.get_shares()/100.0))
                    trader.submit_order(sell)
                    
                
                target_hit_count = state[target_key][ticker][0]

                # over band, never hit
                if price_minus_bollinger > 0 and target_hit_count == 0:
                    cancel_all_trades(trader, ticker)
                    s = item.get_shares()
                    sell = shift.Order(shift.Order.Type.MARKET_SELL, ticker, int(math.ceil((s/2) / 100.0)))
                    trader.submit_order(sell)

                    #check if you happen to sell all due to minimum lot
                    if int(math.ceil((item.get_shares()/2) / 100.0)) < int(s/100):
                        lastPrice = trader.get_last_price(ticker)
                        initial_buy_price = item.get_price()
                        #keep track of this in state
                        trailing_stop_perc = (lastPrice - initial_buy_price) / initial_buy_price
                        trailing_stop_price = (1 - trailing_stop_perc) * lastPrice
                        sell = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, int(math.ceil((item.get_shares()/2) / 100.0)), trailing_stop_price)
                        state[target_key][ticker] = [target_hit_count + 1, trailing_stop_perc]
                    
                sold = 0
                if target_hit_count > 0:
                    sold = 0
                    if price_minus_bollinger > 0:
                        cancel_all_trades(trader, ticker)
                        sold = int(math.ceil((item.get_shares()/2) / 100.0))
                        sell = shift.Order(shift.Order.Type.MARKET_SELL, ticker, sold)
                        trader.submit_order(sell)
                    if sold < int(item.get_shares()/100):
                        
                        lastPrice = trader.get_last_price(ticker)

                        avg_last_two_prices = (state[prices_key][ticker][-2] + state[prices_key][ticker][-1]) / 2.
                        
                        if lastPrice >= avg_last_two_prices:
                            cancel_all_trades(trader, ticker)
                            # keep same percentarange and update the loss PRICE
                            trailing_stop_perc = state[target_key][ticker][1]
                            trailing_stop_price = (1 - trailing_stop_perc) * lastPrice
                            sell = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, item.get_shares() / 100.0, trailing_stop_price)
                            trader.submit_order(sell)
                        else:
                            pass
                        
                    
            else:
                #reset target_hit_count because no shores no more
                state[target_key][ticker] = [0,0]
                for order in trader.get_waiting_list():
                    if order.symbol == ticker and order.type == shift.Order.Type.MARKET_BUY:
                        trader.submit_cancellation(order)
                if ema_difference > 0:
                    bp = trader.get_portfolio_summary().get_total_bp()
                    amount = 200e3
                    if bp >= amount:
                        lastPrice = trader.get_last_price(ticker)
                        s = int((amount / lastPrice) / 100.)
                        buy = shift.Order(shift.Order.Type.MARKET_BUY, ticker, s)
                        initial_buy_price = trader.get_last_price(ticker)
                        initial_stop_loss = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, trader.get_last_price(ticker)*(1-maxLoss), s)
                        trader.submit_order(buy)
                        trader.submit_order(initial_stop_loss)
        sleep(run_trades_interval)

def cancel_all_trades(trader: shift.Trader, ticker: str):
    for o in trader.get_waiting_list():
        if(o.symbol == ticker):
            trader.submit_cancellation(o)
    
def run_processes(trader: shift.Trader, state: Dict[str, Any]) -> List[Process]:
    
    """
    create all the threads
    """


    processes = []

    # for ticker in tickers:
    #     # 1 thread per ticker getting price data & saving it
    #     processes.append(Process(target=run_save_prices, args=(ticker, trader, state)))

    processes.append(Process(target=run_stop_loss_check, args=(trader, state[prices_key], state[stop_loss_key])))
    processes.append(Process(target=run_trades, args=(trader, state[price_key])))
    processes.append(Process(target=routine_summary, args=[trader]))

    for process in processes:
        process.start()

    return processes


def stop_processes(processes: List[Process]) -> None:
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
            if key == price_key:
                state[key].setdefault(key, [])
            elif key == target_key:    
                state[key].setdefault(key, [0,0])
            # if key == stop_loss_key:

    check_time = 1 # minutes
    current = trader.get_last_trade_time()
    start_time = datetime.combine(current, dt.time(9,32,0))
    end_time = datetime.combine(current, dt.time(15, 30, 0))

    print(trader.get_last_trade_time())
    pre_processes = []

    for ticker in tickers:
        # 1 thread per ticker getting price data & saving it
        pre_processes.append(Process(target=run_save_prices, args=(ticker, trader, state)))

    for process in pre_processes:
        process.start()


    print(f"{len(pre_processes)} processes created for run_save_prices")

    while trader.get_last_trade_time() < start_time:
        print(f"Waiting for Market Open @ {trader.get_last_trade_time()}")
        sleep(check_time * 60)


    processes = pre_processes.extend(run_processes(trader, state))

    while trader.get_last_trade_time() < end_time:
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

if __name__ == '__main__':

    trader = shift.Trader(credentials.my_username)

    try:
        trader.connect("initiator.cfg", credentials.my_password)
        trader.sub_all_order_book()
    except shift.IncorrectPasswordError as e:
        print(e)
    except shift.ConnectionTimeoutError as e:
        print(e)

    sleep(2)

    main(trader)
