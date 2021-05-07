
import shift
import time

def sell_long(ticker: str, trader: shift.Trader):
    
    item = trader.get_portfolio_item(ticker)
    while(item.get_shares() > 0):
        orders_placed = place_orders(shift.Order.Type.MARKET_SELL,ticker, int(item.get_shares() / 100))
        sleep(10)
        item = trader.get_portfolio_item(ticker)
        # sell = shift.Order(shift.Order.Type.MARKET_SELL,ticker, int(item.get_shares() / 100)) # Order size in 100's of shares, strictly as an int
        # trader.submit_order(sell)
        print(f'submitted sell for {ticker}')

def buy_back_shorted(ticker: str, trader: shift.Trader):

    item = trader.get_portfolio_item(ticker)
    while(item.get_shares() < 0):
        orders_placed = place_orders(shift.Order.Type.MARKET_BUY,ticker, int(-1* item.get_shares() / 100))
        sleep(10)
        item = trader.get_portfolio_item(ticker)
        print(f'submitted buy for {ticker}')
    # if item.get_shares() < 0:
        # buy = shift.Order(shift.Order.Type.MARKET_BUY,ticker, int(-1* item.get_shares() / 100)) # Order size in 100's of shares, strictly as an int
        # trader.submit_order(buy)

def manageInventory(ticker, trader: shift.Trader,  dayEnd):


    # While the time is before end of day...
    while(trader.get_last_trade_time() < dayEnd):

        time.sleep(5) # Give prices time to fluctuate

        item = trader.get_portfolio_item(ticker)
        if item.get_shares() != 0:
            
            unrealizedPL = 0
            tradedPrice = item.get_price()
            numShares = int(item.get_shares() / 100) # Order size in 100's of shares, strictly as an int

            if numShares > 0:
                unrealizedPL = ((trader.get_close_price(ticker, False, numShares) - tradedPrice)/tradedPrice)*100

            else:# numShares < 0:
                unrealizedPL = -((trader.get_close_price(ticker, True, -numShares) - tradedPrice)/tradedPrice)*100

            print(ticker, "Unrealized P/L:", unrealizedPL,"%")
            if unrealizedPL >= 0.40: # Target met, take profit
                #if unrealizedPL >= 3.0: # Target met, take profit
                if item.get_shares() > 0:
                    sell_long(ticker, trader)
                    """
                    closeLong = shift.Order(shift.Order.Type.MARKET_SELL, item.get_symbol(), numShares)
                    trader.submit_order(closeLong)
                    """
                    print(ticker, "take profit on long")
                    time.sleep(5) # Don't act on volatile spikes and dips, only identify longer trends
                elif item.get_shares() < 0:
                    buy_back_shorted(ticker, trader)
                    """
                    coverShort = shift.Order(shift.Order.Type.MARKET_BUY, item.get_symbol(), -numShares)
                    trader.submit_order(coverShort)
                    """
                    print(ticker, "take profit on short")
                    time.sleep(5) # Don't act on volatile spikes and dips, only identify longer trends

            elif unrealizedPL <= -0.30: # Stop loss met, sell risk
                #elif unrealizedPL <= -0.50: # Stop loss met, sell risk
                if item.get_shares() > 0:
                    closePositions(trader, ticker)
                    """
                    closeLong = shift.Order(shift.Order.Type.MARKET_SELL, item.get_symbol(), numShares)
                    trader.submit_order(closeLong)
                    """
                    print(ticker, "stop loss on long")
                    time.sleep(5) # Don't act on volatile spikes and dips, only identify longer trends
                elif item.get_shares() < 0:
                    closePositions(trader, ticker)
                    """
                    coverShort = shift.Order(shift.Order.Type.MARKET_BUY, item.get_symbol(), -numShares)
                    trader.submit_order(coverShort)
                    """
                    print(ticker, "stop loss on short")
                    time.sleep(5) # Don't act on volatile spikes and dips, only identify longer trends


        # rightNow =  trader.get_last_trade_time() # Reset datetime of right now