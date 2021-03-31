import sys
import time
import shift
from components.market_maker_one import market_maker_one
import threading
import credentials
import utils
from components.routine_summary import routine_summary


def main(argv):
    trader = shift.Trader(credentials.my_username)
    try:
        trader.connect("initiator.cfg", credentials.my_password)
        trader.sub_all_order_book()
    except shift.IncorrectPasswordError as e:
        print(e)
    except shift.ConnectionTimeoutError as e:
        print(e)

    time.sleep(2)

    ticker = "AAPL"

    long_and_short_aapl = threading.Thread(target=market_maker_one, args=[trader, ticker], name='long_and_short')
    routine_summary_thread = threading.Thread(target=routine_summary, args=[trader], name='routine_summary')

    routine_summary_thread.start()
    long_and_short_aapl.start()

    long_and_short_aapl.join()
    routine_summary_thread.join()

    trader.disconnect()


if __name__ == '__main__':
    main(sys.argv)


