from typing import Dict, Any, List

import math
from candle import Candle
import credentials
import datetime as dt
import pandas as pd
import shift
from time import sleep
from datetime import datetime, timedelta, time
from threading import Thread
from multiprocessing import Manager
import multiprocessing as mp
from collections import deque
from components.routine_summary import routine_summary
import utils
tickers = ["AAPL"
, "XOM", "VZ", "UNH"
]
"""
TR=Max[(H − L),Abs(H − Cp),Abs(L − Cp)]
ATR=(1/n) = (i=1)∑(n)TR i
"""

import numpy as np
import pandas_datareader as pdr
import datetime as dt

candles_key = 'candles'
candle_size = 60
safe_sleep = 5
buffer = 200e3
def ATR(candles: List[Candle], length = 20):

    # https://www.learnpythonwithrune.org/calculate-the-average-true-range-atr-easy-with-pandas-dataframes/
    highs = pd.Series(map(lambda c : c.high, candles))
    lows = pd.Series(map(lambda c : c.low, candles))
    closes = pd.Series(map(lambda c : c.close, candles))

    # print("HIGHS")
    # print(type(highs))
    # print(highs)
    # print("LOWS")
    # print(type(lows))
    # print(lows)
    # print("CLOSES")
    # print(type(closes))
    # print(closes)
    # PRINT("closes shift")
    # print(type(closes.shift(axis = 0)))
    # print(closes.shift(axis = 0))

    high_low = highs - lows
    high_close = np.abs(highs - closes.shift())
    low_close = np.abs(lows - closes.shift())

    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)

    atr = true_range.rolling(length).sum()/length
    #atr = true_range.ewm(alpha=1/length, adjust=False).mean()
    return atr, true_range


def build_candles(ticker: str, trader: shift.Trader, state: Dict[str, Any], end_time):
    queue_size = 30
    
    while trader.get_last_trade_time() < end_time:

        s = 0
        price = trader.get_last_price(ticker)
        candle = Candle(price, price, price, price)
        while s < candle_size:
            price = trader.get_last_price(ticker)
            if price < candle.low:
                candle.setLow(price)
            if price > candle.high:
                candle.setHigh(price)

            sleep(1)
            s += 1
        price = trader.get_last_price(ticker)
        candle.setClose(price)

        try:
            state[candles_key][ticker] += [candle]
        except KeyError:
            state[candles_key][ticker] = deque(maxlen=queue_size)
            sleep(0.5)
            state[candles_key][ticker] += [candle]
        

def buy_back_shorted(ticker: str, trader: shift.Trader):

    item = trader.get_portfolio_item(ticker)
    while(item.get_shares() < 0):
        orders_placed = place_orders(shift.Order.Type.MARKET_BUY,ticker, int(-1* item.get_shares() / 100))
        sleep(10)
        item = trader.get_portfolio_item(ticker)
    print(f'submitted buy for {ticker}')
    # if item.get_shares() < 0:
        # buy = shift.Order(shift.Order.Type.MARKET_BUY,ticker, int(-1* item.get_shares() / 100)) # Order size in 100's of shares, strictly as an int
        # trader.submit_order(buy)
            
def sell_long(ticker: str, trader: shift.Trader):
    
    item = trader.get_portfolio_item(ticker)
    while(item.get_shares() > 0):
        orders_placed = place_orders(shift.Order.Type.MARKET_SELL,ticker, int(item.get_shares() / 100))
        sleep(10)
        item = trader.get_portfolio_item(ticker)
        # sell = shift.Order(shift.Order.Type.MARKET_SELL,ticker, int(item.get_shares() / 100)) # Order size in 100's of shares, strictly as an int
        # trader.submit_order(sell)
    print(f'submitted sell for {ticker}')

def get_unrealized_short_pnl(trader: shift.Trader):
    total_unrealized_short_pnl = 0
    for item, value in trader.get_portfolio_items().items():
        if(value.get_shares() < 0):
            total_unrealized_short_pnl += trader.get_unrealized_pl(item)

    return total_unrealized_short_pnl

def get_tickers_with_positions(trader: shift.Trader):
    t = []
    for ticker, item in trader.get_portfolio_items().items():
        if(item.get_shares() != 0 and len(item.get_symbol()) >= 1):
            t.append(ticker)
    return t

def place_orders(order_type: shift.Order.Type, ticker: str, size: int):
    order = shift.Order(order_type, ticker, size)
    trader.submit_order(order)
    # orders_to_place = []
    #78 => 7x10 + 1x8
    # placed = 0
    # for i in range(size):
    #     order = shift.Order(order_type, ticker, 1)
    #     trader.submit_order(order)
    #     orders_to_place.append(order)
        # placed += 10
        # sleep(1)
    # left = size - placed
    # if left > 0:
    #     # left < 10
    #     for i in range(left):
    #         order = shift.Order(order_type, ticker, 1)
    #         trader.submit_order(order)
    #         orders_to_place.append(order)
    #         sleep(1)
    
    return [order]

    
def run_volatility(ticker: str, state: Dict[str, Any], end_time, length = 20, factor = 2.25):
    

    while(len(state[candles_key][ticker]) < 21):
        sleep(candle_size)

    candles = state[candles_key][ticker]

    lastClose = candles[-1].close
    
    maximum = lastClose
    minimum = lastClose
    
    uptrend = None
    stop = 0.

    prev_uptrend = None
    
    while trader.get_last_trade_time() < end_time:

        atr, tr = ATR(state[candles_key][ticker], length)
        # print("ATR")
        # print(type(atr))
        # print(atr)

        """
        import pandas_datareader as pdr
        import datetime as dt

        start = dt.datetime(2020, 1, 1)
        data = pdr.get_data_yahoo("NFLX", start)

        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())

        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)

        atr = true_range.rolling(14).sum()/14
        """

        ATR_factor = atr.iloc[-1] * factor

        if ATR_factor == 0 or math.isnan(ATR_factor):
            ATR_factor = tr.iloc[-1]
    
        lastClose = state[candles_key][ticker][-1].close

        maximum = max(maximum, lastClose)
        minimum = min(minimum, lastClose)
        
        if uptrend == True:
            new_stop = max(stop, maximum - ATR_factor)
        elif uptrend == False:
            new_stop = min(stop, minimum + ATR_factor)
        else:
            new_stop = stop
        
        if new_stop == 0:
            stop = lastClose
        else:
            stop = new_stop 
            


        prev_uptrend = uptrend
        uptrend = (lastClose - stop >= 0)
        
        # checker = True if (prev_uptrend) == None else prev_uptrend
        checker = prev_uptrend


        #we have new stop value
        if uptrend != checker:
            maximum = lastClose
            minimum = lastClose
            # unrealized_short_pnl = get_unrealized_short_pnl(trader)            
            should_buy = False
            if checker == None:
                if uptrend:
                    should_buy = True
            elif checker == False:
                should_buy = True
            elif checker == True:
                should_buy == False

            # TODO - fix bp / shares, minimum of 200k and bp for buy
            # TODO - fix order of closing at day end

            if(should_buy):

            # elif checker == False:
                # prev was in downtrend, now in uptrend
                buy_back_shorted(ticker, trader)
                #sleep
                sleep(safe_sleep)
                #take longs with market order
                tickers_left_to_invest = len(tickers) - len(get_tickers_with_positions(trader))
                print(f"TICKERS WITH POSITIONS: {get_tickers_with_positions(trader)}")
                if(tickers_left_to_invest <= 0):
                    sleep(candle_size)
                    continue 

                bp = trader.get_portfolio_summary().get_total_bp() - get_unrealized_short_pnl(trader) - buffer
                if bp > 0:
                    amount = 200e3 if ((bp/tickers_left_to_invest) >= 200e3) else (bp/tickers_left_to_invest)
                    s = int((amount / trader.get_last_price(ticker)) / 100.)
                    orders_placed = place_orders(shift.Order.Type.MARKET_BUY, ticker, s)
                    # buy = shift.Order(shift.Order.Type.MARKET_BUY, ticker, s)
                    # trader.submit_order(buy)
                
            else:
            # elif checker == True:
                # prev was in uptrend, now in downtrend
                sell_long(ticker, trader)
                #sleep
                sleep(safe_sleep)
                #take shorts with market order
                tickers_left_to_invest = len(tickers) - len(get_tickers_with_positions(trader))
                print(f"TICKERS WITH POSITIONS: {get_tickers_with_positions(trader)}")
                if(tickers_left_to_invest <= 0):
                    sleep(candle_size)
                    continue 
                bp = trader.get_portfolio_summary().get_total_bp() - get_unrealized_short_pnl(trader) - buffer
                if bp > 0:
                    avail = 200e3 if ((bp/tickers_left_to_invest) > 200e3) else (bp/tickers_left_to_invest)
                    amount = (avail / 2) * 0.99
                    s = int((amount / trader.get_last_price(ticker)) / 100.)
                    orders_placed = place_orders(shift.Order.Type.MARKET_SELL, ticker, s)
                    # sell = shift.Order(shift.Order.Type.MARKET_SELL, ticker, s)
                    # trader.submit_order(sell)


                       
            

        sleep(candle_size)

def run_processes(trader: shift.Trader, state: Dict[str, Any], end_time) -> List[Thread]:
    """
    create all the threads
    """


    processes = []

    for ticker in tickers:
        processes.append(Thread(target=run_volatility, args=(ticker, state, end_time, 20, 2.25)))
    
    processes.append(Thread(target=routine_summary, args=(trader,end_time)))

    for process in processes:
       process.start()

    return processes


def stop_processes(processes: List[Thread]) -> None:
    """
    stop all the threads
    """
    for process in processes:
        process.join(timeout=1)

def main(trader):
    manager = Manager()
    list_of_shared_dicts = manager.list()
    list_of_shared_dicts.append({})
    state = list_of_shared_dicts[0]
    keys_in_state = [candles_key]
    for key in keys_in_state:
        state[key] = manager.dict()
        for ticker in tickers:
            if key == candles_key:
                state[key].setdefault(ticker, [])
    
    check_frequency = 60 
    current = trader.get_last_trade_time()
    start_time = datetime.combine(current, dt.time(9,52,0))
    end_time = datetime.combine(current, dt.time(15,30,0))


    processes = []

    for ticker in tickers:
        # 1 thread per ticker getting price data & saving it
        processes.append(Thread(target=build_candles, args=(ticker, trader, state, end_time)))
        
        # run_save_prices(ticker, trader, state)

    for process in processes:
        process.start()


    print(f"{len(processes)} processes created for run_save_prices")

    while trader.get_last_trade_time() < start_time:

        print(f"Checking for market open at {trader.get_last_trade_time()}")
        sleep(check_frequency)

    processes.extend(run_processes(trader, state, end_time))

    while trader.get_last_trade_time() < end_time: 
        print(f"Waiting for Market Close @ {trader.get_last_trade_time()}")
        sleep(check_frequency)


    stop_processes(processes)

    for order in trader.get_waiting_list():
        trader.submit_cancellation(order)

    
    for t in tickers:
        item = trader.get_portfolio_item(t)
        if item.get_shares() > 0:
            # orders_placed = place_orders(shift.Order.Type.MARKET_SELL, t, int(item.get_shares() / 100))
            # # sell = shift.Order(shift.Order.Type.MARKET_SELL,t, int(item.get_shares() / 100)) # Order size in 100's of shares, strictly as an int
            # # trader.submit_order(sell)
            print(f'CLOSING LONG {t}')
            # sleep(1)
            sell_long(t, trader)
            sleep(1)
    sleep(10)
    for t in tickers:
        item = trader.get_portfolio_item(t)
        if item.get_shares() < 0:
            # orders_placed = place_orders(shift.Order.Type.MARKET_BUY, t, int(-1* item.get_shares() / 100))
            # buy = shift.Order(shift.Order.Type.MARKET_BUY,t, int(-1* item.get_shares() / 100)) # Order size in 100's of shares, strictly as an int
            # trader.submit_order(buy)
            print(f'CLOSING SHORT {t}')
            buy_back_shorted(t, trader)
            sleep(1)

    sleep(15)
    utils.print_portfolio_information(trader)
    utils.print_all_submitted_order(trader)
    print(trader.get_last_trade_time())


if __name__ == '__main__':
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

    main(trader)
    trader.disconnect()

    

'''

-------------------------------------------------------------------------------------------------------------------------------------

study("Volatility Stop", "VStop", overlay=true, resolution="")
length = input(20, "Length", minval = 2) #lenght = 20
src = input(close, "Source") 
factor = input(2.0, "Multiplier", minval = 0.25, step = 0.25) #factor = 2
volStop(src, atrlen, atrfactor) =>
    var max     = src #max = curr close if there is no max already
    var min     = src #min = curr close if there is no min already
    var uptrend = true #initialize uptrend to true
    var stop    = 0.0 # initialize stop to 0
    atrM        = nz(atr(atrlen) * atrfactor, tr) # atr factor
    max         := max(max, src)
    min         := min(min, src)
    stop        := nz(uptrend ? max(stop, max - atrM) : min(stop, min + atrM), src) #new stop if uptrend or downtrend
    uptrend     := src - stop >= 0.0
    if uptrend != nz(uptrend[1], true)
        max    := src
        min    := src
        stop   := uptrend ? max - atrM : min + atrM
    [stop, uptrend]

[vStop, uptrend] = volStop(src, length, factor)

plot(vStop, "Volatility Stop", style=plot.style_cross, color= uptrend ? #007F0E : #872323)

----------------------------------------------------------------------------------------------------------------
'''