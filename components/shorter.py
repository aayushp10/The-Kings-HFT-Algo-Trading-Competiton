import shift
import datetime as dt
import time
import sys
import math
def shorter(trader: shift.Trader, tickers):

    today = trader.get_last_trade_time()
    endTime = dt.time(15, 30, 0)
    dayEnd = dt.datetime.combine(today, endTime)
    tickSize = 0.01
    bp = trader.get_portfolio_summary().get_total_bp()
    dpa = bp/float(len(tickers))

    for t in tickers:
        lastPrice = trader.get_last_price(t)
        s = math.floor((bpa/last_price)/100)
        limitSellPrice = lastPrice + tickSize
        limit_sell = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, s, limitSellPrice)

    while today < dayEnd:
        pass
    