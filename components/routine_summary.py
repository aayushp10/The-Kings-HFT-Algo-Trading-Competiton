import shift
import time
import datetime as dt
import utils

def routine_summary(trader: shift.Trader) -> None:
    while True:
        utils.print_all_submitted_order(trader)
        utils.print_portfolio_information(trader)
        ct = dt.datetime.now()
        print("current time:-", trader.get_last_trade_time())
        time.sleep(15)
