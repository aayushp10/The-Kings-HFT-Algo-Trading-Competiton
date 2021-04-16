import sys
import time
import shift
import threading
import credentials
import queue

from components.market_maker_one import market_maker_one
from components.routine_summary import routine_summary
from components.data_processor import collect_data
from components.shorter import shorter
from components.longer import longer
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
    ticker_data = {}
    que = queue.Queue()
    t = threading.Thread(target=que.put(collect_data(trader, ticker)), name='ticker_data_one')
    t.start()
    t.join()

    ticker_data[ticker] = que.get()

    should_long = ticker_data[ticker]["long"]
    if should_long:
        tickers = ["NKE", "INTC", "AAPL", "BA"]
        long_thread = threading.Thread(target=longer, args=[trader, tickers], name='longer_thread')
        long_thread.start()
        routine_summary_thread = threading.Thread(target=routine_summary, args=[trader], name='routine_summary')
        routine_summary_thread.start()

        long_thread.join()
        routine_summary_thread.join()
        
    else:
        long_and_short_aapl = threading.Thread(target=market_maker_one, args=[trader, ticker], name='long_and_short')
        routine_summary_thread = threading.Thread(target=routine_summary, args=[trader], name='routine_summary')

        routine_summary_thread.start()
        long_and_short_aapl.start()

        long_and_short_aapl.join()
        routine_summary_thread.join()

    trader.disconnect()

if __name__ == '__main__':
    main(sys.argv)