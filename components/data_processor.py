import time
import datetime as dt
import shift
import statistics

def collect_data(trader: shift.Trader, ticker: str):
    today = trader.get_last_trade_time()
    print(today)
    endTime = dt.time(9, 35, 0)
    end_of_data_collection_period = dt.datetime.combine(today, endTime)

    prices = []
    while (trader.get_last_trade_time() < end_of_data_collection_period):
        prices.append(trader.get_last_price(ticker))
        print(trader.get_last_trade_time())
        time.sleep(5)

    return {
        "prices": prices,
        **calculate_statistics(prices)
    }

def calculate_statistics(prices):
    variance = 0
    if(len(prices)> 2):

        variance = statistics.variance(prices)

    return {
        "variance": variance,
        "long": True
    }


