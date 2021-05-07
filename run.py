import shift
from time import sleep
from datetime import datetime, timedelta, time
import numpy as np
from typing import Dict, Any, Tuple, List
from scipy.stats import linregress
from multiprocessing import Process, Manager
from collections import deque
from components.routine_summary import routine_summary
from threading import Thread
import math
import sys
sys.path.insert(1, '../')
import credentials
import datetime as dt
import utils
from inventory import manageInventory 
tickers = ["IBM", "AXP"]

frequency = 3
safe_sleep = 5
buffer = 200e3

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

def buy_back_half(ticker: str, trader: shift.Trader):

    item = trader.get_portfolio_item(ticker)

    if item.get_shares() == -100:
        orders_placed = place_orders(shift.Order.Type.MARKET_BUY,ticker, int(-1* item.get_shares() / 100))
    else:
        orders_placed = place_orders(shift.Order.Type.MARKET_BUY,ticker, int((-1* item.get_shares() / 100)/2))
    sleep(10)

    print(f'submitted buy for {ticker}')
    # if item.get_shares() < 0:
        # buy = shift.Order(shift.Order.Type.MARKET_BUY,ticker, int(-1* item.get_shares() / 100)) # Order size in 100's of shares, strictly as an int
        # trader.submit_order(buy)
            
def sell_half(ticker: str, trader: shift.Trader):
    
    item = trader.get_portfolio_item(ticker)

    if item.get_shares() == 100:
        orders_placed = place_orders(shift.Order.Type.MARKET_SELL,ticker, int(item.get_shares() / 100))
    else:
        orders_placed = place_orders(shift.Order.Type.MARKET_SELL,ticker, int((item.get_shares() / 100)/2))
    sleep(10)

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
    return [order]

def place_limit_order(order_type: shift.Order.Type, ticker: str, size: int, price: float):
    order = shift.Order(order_type, ticker, size, price)
    trader.submit_order(order)
    return order

def get_prices(ticker):
    best_price = trader.get_best_price(ticker)
    ask = best_price.get_ask_price()
    bid = best_price.get_bid_price()
    
    return ask, bid, (best_price.get_bid_price()+best_price.get_ask_price())/2

def get_order_status(order):
    return trader.get_order(order.id).status

def run_mm_short(ticker: str, trader: shift.Trader, end_time):
    minimum_spread = 0.02
    maximum_allocation = 0.15
    while trader.get_last_trade_time() < end_time:
        
        sleep(frequency)       

        item = trader.get_portfolio_item(ticker)
        shares = item.get_shares()
        ask,bid,mid = get_prices(ticker)
        if int(ask) == 0 or int(bid) == 0:
            continue

        spread = (ask-bid)
        
        portfolio_value_of_ticker = shares*mid
        allocation = maximum_allocation*1000000
        
        if allocation > -portfolio_value_of_ticker:
            
            lots = 3
            price = ask
            if spread < minimum_spread:
                price += 0.01        

                
            order = place_limit_order(shift.Order.Type.LIMIT_SELL, ticker, lots, price)
            check_order(order, trader)

        else: 
            continue

def check_order(order, trader: shift.Trader):
    sleep(1)
    status = get_order_status(order)
    tries = 0
    while status != shift.Order.Status.REJECTED and status != shift.Order.Status.FILLED and tries < 10:
        sleep(1)
        tries += 1
        status = get_order_status(order)
    if status != shift.Order.Status.REJECTED and status != shift.Order.Status.FILLED:
        trader.submit_cancellation(order)

def run_mm_long(ticker: str, trader: shift.Trader, end_time):
    
    minimum_spread = 0.02
    maximum_allocation = 0.15

    while trader.get_last_trade_time() < end_time:
        
        sleep(frequency)       

        item = trader.get_portfolio_item(ticker)
        shares = item.get_shares()
        ask,bid,mid = get_prices(ticker)

        if bid == 0 or ask == 0:
            continue

        spread = (ask-bid)
        
        portfolio_value_of_ticker = shares*mid
        allocation = maximum_allocation*1000000
        
        if allocation > portfolio_value_of_ticker:
            lots = 3
            price = bid
            if spread < minimum_spread:
                price -= 0.01
                
            order = place_limit_order(shift.Order.Type.LIMIT_BUY, ticker, lots, price)
            status = get_order_status(order)
            check_order(order, trader)
        else: 
            continue

def get_unrealized_pl(ticker: str, trader: shift.Trader):

    p = trader.get_last_price(ticker)
    item = trader.get_portfolio_item(ticker)
    upl = -1 if item.get_shares() < 0 else 1
    currValue = item.get_shares() * p
    cost = item.get_shares() * item.get_price()
    if cost == 0:
        return 0
    upl = upl*((currValue - cost)/cost)
    return upl

def manage_inventory(ticker: str, trader: shift.Trader, end_time):
    while trader.get_last_trade_time() < end_time:            
        sleep(frequency)
        upl = get_unrealized_pl(ticker, trader)
        item = trader.get_portfolio_item(ticker)
        if int(item.get_price()) != 0:
            if upl >= 0.4 or upl <= -0.2:
                print(f"Closing positions on {ticker} for {'loss' if upl <= -0.2 else 'profit'}")
                if item.get_shares() > 0:
                    sell_long(ticker)
                elif item.get_shares() < 0:
                    buy_back_shorted(ticker)

def run_processes(trader: shift.Trader, end_time) -> List[Thread]:
    """
    create all the threads
    """

    processes = []

    for ticker in tickers:
        processes.append(Thread(target=run_mm_short, args=(ticker, trader, end_time)))
        processes.append(Thread(target=run_mm_long, args=(ticker, trader, end_time)))
        processes.append(Thread(target=manage_inventory, args=(ticker, trader, end_time)))
        # processes.append(Thread(target=manageInventory, args=(ticker, trader, end_time)))
    
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
    
    check_frequency = 60 
    current = trader.get_last_trade_time()
    start_time = datetime.combine(current, dt.time(10,0,0))
    end_time = datetime.combine(current, dt.time(15,30,0))


    processes = []


    while trader.get_last_trade_time() < start_time:

        print(f"Checking for market open at {trader.get_last_trade_time()}")
        sleep(check_frequency)

    processes.extend(run_processes(trader, end_time))

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