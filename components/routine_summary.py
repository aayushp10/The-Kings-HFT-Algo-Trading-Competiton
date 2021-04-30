import shift
import time
import datetime as dt


import utils


# def routine_summary(trader: shift.Trader) -> None:
#     while True:
#         utils.print_all_submitted_order(trader)
#         utils.print_portfolio_information(trader)
#         ct = dt.datetime.now()
#         print("current time:-", trader.get_last_trade_time())
#         time.sleep(15)


def routine_summary(trader: shift.Trader, end_time):
    # today = trader.get_last_trade_time()
    # endTime = dt.time(9, 50, 0)
    # dayEnd = dt.datetime.combine(today, endTime)
    # rightNow = trader.get_last_trade_time()
    while trader.get_last_trade_time() < end_time:
        print(f"----------{trader.get_last_trade_time()}-------------")
        utils.print_all_submitted_order(trader)
        utils.print_portfolio_information(trader)
        ct = dt.datetime.now()
        print("current time:-", ct)
        time.sleep(60)
    return 0