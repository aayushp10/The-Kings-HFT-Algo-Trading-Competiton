

import shift
import time
import datetime as dt
import utils
def routine_summary(trader: shift.Trader):
    today = trader.get_last_trade_time()
    endTime = dt.time(15, 50, 0)
    dayEnd = dt.datetime.combine(today, endTime)
    rightNow = trader.get_last_trade_time()
    print(today)
    print(dayEnd)
    while today < dayEnd:
        # utils.print_all_submitted_order(trader)
        utils.print_portfolio_information(trader)
        time.sleep(15)
    return