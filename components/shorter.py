import shift
import datetime as dt
import time
import sys
import math
import utils


def shorter(trader: shift.Trader, tickers):
    today = trader.get_last_trade_time()
    endTime = dt.time(15, 30, 0)
    dayEnd = dt.datetime.combine(today, endTime)
    tickSize = 0.01
    bp = (trader.get_portfolio_summary().get_total_bp())/2
    dpa = bp/float(len(tickers))

    for t in tickers:
        lastPrice = trader.get_last_price(t)
        while lastPrice == 0:
            lastPrice = trader.get_last_price(t)
        s = int((dpa/lastPrice)/100)

        for i in range(0,s):
            limitSellPrice = lastPrice + tickSize
            limit_sell = shift.Order(shift.Order.Type.MARKET_SELL, t, 1)
            trader.submit_order(limit_sell)

    while trader.get_last_trade_time() < dayEnd:
        time.sleep(1)
        
    for order in trader.get_waiting_list():
        trader.submit_cancellation(order)

    for t in tickers:
        print(t)
        lastPrice = trader.get_last_price(t)
        item = trader.get_portfolio_item(t)
        if item.get_shares() > 0:
            sell = shift.Order(shift.Order.Type.MARKET_SELL,t, int(item.get_shares() / 100)) # Order size in 100's of shares, strictly as an int
            trader.submit_order(sell)
        elif item.get_shares() < 0:
            buy = shift.Order(shift.Order.Type.MARKET_BUY,t, int(-1* item.get_shares() / 100)) # Order size in 100's of shares, strictly as an int
            trader.submit_order(buy)
            print(f'submitted buy for {t}')
    
    time.sleep(5)
    utils.print_portfolio_information(trader)
    utils.print_all_submitted_order(trader)
    print(trader.get_last_trade_time())
    
    

    return