import sys
import time
import shift
from components.market_maker_one import market_maker_one
import threading
import utils
def main(argv):
    trader = shift.Trader("democlient")
    try:
        trader.connect("initiator.cfg", "password")
        trader.sub_all_order_book()
    except shift.IncorrectPasswordError as e:
        print(e)
    except shift.ConnectionTimeoutError as e:
        print(e)

    ticker = "AAPL" 
    long_and_short_aapl = threading.Thread(target=market_maker_one, args=[trader, ticker], name='long_and_short')
    # routine_summary_thread = threading.Thread(target=routine_summary, args=[trader], name='routine_summary')

    # routine_summary_thread.start()
    long_and_short_aapl.start()
    long_and_short_aapl.join()

    trader.on_portfolio_summary_updated(utils.print_portfolio_information(trader))

    # routine_summary_thread.join()

    trader.disconnect()


if __name__ == '__main__':
    main(sys.argv)


