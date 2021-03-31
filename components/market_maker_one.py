import shift
import time
import sys
import datetime as dt


def print_submitted_orders(trader: shift.Trader):

    """
    This method prints all submitted orders information.
    :param trader:
    :return:
    """

    print(
        "Symbol\t\t\t\tType\t  Price\t\tSize\tExecuted\tID\t\t\t\t\t\t\t\t\t\t\t\t\t\t Status\t\tTimestamp"
    )
    for o in trader.get_submitted_orders():
        if o.status == shift.Order.Status.FILLED:
            price = o.executed_price
        else:
            price = o.price
        print(
            "%6s\t%16s\t%7.2f\t\t%4d\t\t%4d\t%36s\t%23s\t\t%26s"
            % (
                o.symbol,
                o.type,
                price,
                o.size,
                o.executed_size,
                o.id,
                o.status,
                o.timestamp,
            )
        )

    return


def market_maker_one(trader: shift.Trader, ticker: str):
    tickSize = 0.01
    # james code need to change maybe?
    today = trader.get_last_trade_time()
    endTime = dt.time(15,50,0)
    dayEnd = dt.datetime.combine(today,endTime)
    rightNow =  trader.get_last_trade_time() 

    #right < the end of day at 3:50
    while today < dayEnd:

        '''
        check inventory here 
        '''

        trader.sub_all_order_book()

        lastPrice = trader.get_last_price("AAPL")

        limitBuyPrice = lastPrice - tickSize
        limitSellPrice = lastPrice + tickSize

        limit_buy = shift.Order(shift.Order.Type.LIMIT_BUY, "AAPL", 2, limitBuyPrice)
        limit_sell = shift.Order(shift.Order.Type.LIMIT_SELL, "AAPL", 1, limitSellPrice)

        # market_buy = shift.Order(shift.Order.Type.MARKET_BUY, "AAPL", 1)
        # trader.submit_order(market_buy)

        trader.submit_order(limit_buy)
        trader.submit_order(limit_sell)


        time.sleep(10)
        
    return
        # print_portfolio_information()
