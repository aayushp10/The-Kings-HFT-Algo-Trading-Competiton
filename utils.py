import shift
from threading import Thread



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


def print_portfolio_information(trader: shift.Trader):
    """
    This method provides information on the structure of PortfolioSummary and PortfolioItem objects:
     get_portfolio_summary() returns a PortfolioSummary object with the following data:
     1. Total Buying Power (get_total_bp())
     2. Total Shares (get_total_shares())
     3. Total Realized Profit/Loss (get_total_realized_pl())
     4. Timestamp of Last Update (get_timestamp())

     get_portfolio_items() returns a dictionary with "symbol" as keys and PortfolioItem as values,
     with each providing the following information:
     1. Symbol (get_symbol())
     2. Shares (get_shares())
     3. Price (get_price())
     4. Realized Profit/Loss (get_realized_pl())
     5. Timestamp of Last Update (get_timestamp())
    :param trader:
    :return:
    """

    print("Buying Power\tTotal Shares\tTotal P&L\tTimestamp")
    print(
        "%12.2f\t%12d\t%9.2f\t%26s"
        % (
            trader.get_portfolio_summary().get_total_bp(),
            trader.get_portfolio_summary().get_total_shares(),
            trader.get_portfolio_summary().get_total_realized_pl(),
            trader.get_portfolio_summary().get_timestamp(),
        )
    )

    upl = {}
    for item in list(trader.get_portfolio_items().keys()):
        upl[item] = trader.get_unrealized_pl(item)

        
    print("Symbol\t\tShares\t\tPrice\t\t  P&L\t\t Unrealized P&L \nTimestamp")
    for item in trader.get_portfolio_items().values():
        print(
            "%6s\t\t%6d\t%9.2f\t%9.2f\t%26s"
            % (
                item.get_symbol(),
                item.get_shares(),
                item.get_price(),
                item.get_realized_pl(),
                item.get_timestamp(),
            )
        )
    print("UNREALIZED PNL")
    print(upl)
    return


def print_all_submitted_order(trader):
    print(
        "Symbol\t\t\t\tType\t  Price\t\tSize\tExecuted\tID\t\t\t\t\t\t\t\t\t\t\t\t\t\t Status\t\tTimestamp"
    )
    orders = trader.get_submitted_orders()
    filled_orders = 0;
    for o in orders:
        if o.status == shift.Order.Status.FILLED or o.status == shift.Order.Status.PARTIALLY_FILLED:
            filled_orders += 1
    
    print(f"Filled/Partially Filled Order : {filled_orders}")

    if len(orders) > 10:
        orders = orders[-10:]
        
    
    for o in orders:

        
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

def print_bid_order_book(trader):
    print("  Price\t\tSize\t  Dest\t\tTime")
    # print("----------------------TRV---------------------------")
    # for order in trader.get_order_book("TRV", shift.OrderBookType.GLOBAL_BID, 10):
    #     print(
    #         "%7.2f\t\t%4d\t%6s\t\t%19s"
    #         % (order.price, order.size, order.destination, order.time)
    #     )
    print("-----------------------IBM--------------------------")    
    for order in trader.get_order_book("IBM", shift.OrderBookType.GLOBAL_BID, 10):
        print(
            "%7.2f\t\t%4d\t%6s\t\t%19s"
            % (order.price, order.size, order.destination, order.time)
        )
    print("-----------------------AXP--------------------------")    
    for order in trader.get_order_book("AXP", shift.OrderBookType.GLOBAL_BID, 10):
        print(
            "%7.2f\t\t%4d\t%6s\t\t%19s"
            % (order.price, order.size, order.destination, order.time)
        )
def print_ask_order_book(trader):
    print("  Price\t\tSize\t  Dest\t\tTime")
    # print("----------------------TRV---------------------------")
    # for order in trader.get_order_book("TRV", shift.OrderBookType.GLOBAL_ASK, 10):
    #     print(
    #         "%7.2f\t\t%4d\t%6s\t\t%19s"
    #         % (order.price, order.size, order.destination, order.time)
    #     )
    print("----------------------IBM---------------------------")
    for order in trader.get_order_book("IBM", shift.OrderBookType.GLOBAL_ASK, 10):
        print(
            "%7.2f\t\t%4d\t%6s\t\t%19s"
            % (order.price, order.size, order.destination, order.time)
        )
    print("--------------------AXP-----------------------------")
    for order in trader.get_order_book("AXP", shift.OrderBookType.GLOBAL_ASK, 10):
        print(
            "%7.2f\t\t%4d\t%6s\t\t%19s"
            % (order.price, order.size, order.destination, order.time)
        )