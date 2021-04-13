import shift
from time import sleep
from datetime import datetime, timedelta, time
import numpy as np
from typing import Dict, Any, Tuple
from scipy.stats import linregress
from multiprocessing import Process, Manager
from collections import deque
from routine_summary import routine_summary
import math

tickers = ['AAPL']
prices_key = 'prices'
stop_loss_key = 'stop_losses' 


def run_save_prices(ticker: str, trader: shift.Trader, state: Dict[str, Any]) -> None:
    """
    save prices for a given ticker to the state
    """
    queue_size = 30
    get_data_interval = 60 # seconds
    save_interval = timedelta(seconds=1) # minimum time in between saving to state

    if prices_key not in state:
        state[prices_key] = {}
    last_save_time = datetime.now()
    current_data = []
    while True:
        sleep(get_data_interval)
        current_data.append(trader.get_last_price(ticker))
        curr_time = datetime.now()
        if curr_time > last_save_time + save_interval:
            if ticker not in state[prices_key]:
                state[prices_key][ticker] = deque(maxlen=queue_size)
            state[prices_key][ticker].extend(current_data)
            current_data = []
            last_save_time = curr_time


def run_stop_loss_check(trader: shift.Trader, state: Dict[str, Any]) -> None:
    """
    check for stop loss hit
    """
    stop_loss_interval = 5 # seconds
    acceptable_loss = .2 # percent

    if stop_loss_key not in state:
        state[stop_loss_key] = {}
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

    return (moving_avg_fast[-1] - moving_avg_slow[-1])/prices[-1], (prices[-1] - bollinger_high[-1])

    #21 EMA and 9 EMA cross? (If last period 9EMA-21EMA < 0, and current period 9EMA-21EMA > 0, then we take a start long position)
    #Store initial buying price as a variable.
    #Store rbitrary stop loss price at buying point (0.2%) as a variable
    #If initial stop loss hits, sell all shares of the position
    #If price >= Upper 2-SD Bollinger Band, sell half of current position for profit
        #Then move intial stop loss to the initial buying price and make this a trailing stop loss until the entire position is closed
    #If price >= Upper 2-SD Bollinger Band again, sell half of current position for profit
        #Contuinue this as long as current position >= 100 shares (make sure we never go below 100 shares or we won't be able to close the position)
        #Or until it is 3:30
            #If it is 3:30, then close the entire position
    #If price <= trailing stop loss price, sell all of the current position


def run_trades(trader: shift.Trader, state: Dict[str, Any]) -> None:
    """
    run buy / sell trades
    """
    run_trades_interval = 60 # seconds

    while True:
        sleep(run_trades_interval)

        unsorted_differences: List[float] = []
        unsorted_tickers: List[str] = []
        for ticker in tickers:
            prices = np.array(list(state[prices_key][ticker]))
            ema_difference, price_minus_bollinger = get_should_long(prices)
            unsorted_differences.append(ema_difference)  
            unsorted_tickers.append(ticker)  

        _, ranked_tickers = map(list, zip(*sorted(zip(unsorted_differences, unsorted_tickers))))

        for ticker in ranked_tickers:
            prices = np.array(list(state[prices_key][ticker]))
            ema_difference, price_minus_bollinger = get_should_long(prices)
            item = trader.get_portfolio_item(ticker)
            if item.get_shares() > 0:
                # check to sell
                if price_minus_bollinger > 0 or ema_difference < 0:
                    sell = shift.Order(shift.Order.Type.MARKET_SELL, ticker, int(math.ceil((item.get_shares()/2) / 100.0)))
                    trader.submit_order(sell)
            else:
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
                        trader.submit_order(buy)


def run_processes(trader: shift.Trader) -> List[Process]:
    """
    create all the threads
    """
    state = Manager.dict()
    processes = []

    for ticker in tickers:
        # 1 thread per ticker getting price data & saving it
        processes.append(Process(target=run_save_prices, args=(ticker, trader, state)))

    processes.append(Process(target=run_stop_loss_check, args=(trader, state)))
    processes.append(Process(target=run_trades, args=(trader, state)))
    processes.append(Process(target=routine_summary, args=(trader)))

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
    check_time = 5 # minutes
    start_time = time(9, 35, 0)
    end_time = time(15, 30, 0)

    while trader.get_last_trade_time() < start_time:
        sleep(check_time * 60)

    run_processes(trader)

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

