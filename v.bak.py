def run_volatility(ticker: str, state: Dict[str, Any], length = 20, factor = 2.25):
    

    while(len(state[candles_key][ticker]) < 21):
        sleep(candle_size)

    candles = state[candles_key][ticker]

    lastClose = candles[-1].close
    
    maximum = lastClose
    minimum = lastClose
    
    uptrend = True
    stop = 0.

    prev_uptrend = None
    
    while True:

        atr, tr = ATR(state[candles_key][ticker], length)
        # print("ATR")
        # print(type(atr))
        # print(atr)

        """
        import pandas_datareader as pdr
        import datetime as dt

        start = dt.datetime(2020, 1, 1)
        data = pdr.get_data_yahoo("NFLX", start)

        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())

        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)

        atr = true_range.rolling(14).sum()/14
        """

        ATR_factor = atr.iloc[-1] * factor

        if ATR_factor == 0 or math.isnan(ATR_factor):
            ATR_factor = tr.iloc[-1]
    
        lastClose = state[candles_key][ticker][-1].close

        maximum = max(maximum, lastClose)
        minimum = min(minimum, lastClose)
        
        if uptrend == True:
            new_stop = max(stop, maximum - ATR_factor)
        else:
            new_stop = min(stop, minimum + ATR_factor)

        if new_stop == 0:
            stop = lastClose
        else:
            stop = new_stop 
            
    
        

        prev_uptrend = uptrend
        uptrend = (lastClose - stop >= 0)
        
        checker = True if (prev_uptrend) == None else prev_uptrend


        if uptrend != checker:
            #shit flipped on us 
            maximum = lastClose
            minimum = lastClose
            stop = maximum - ATR_factor if uptrend else minimum + ATR_factor

        #we have new stop value
        if uptrend != checker:

            # unrealized_short_pnl = get_unrealized_short_pnl(trader)            
            
            if checker == False:
                # prev was in downtrend, now in uptrend
                buy_back_shorted(ticker, trader)
                #sleep
                sleep(safe_sleep)
                #take longs with market order
                tickers_left_to_invest = len(tickers) - len(get_tickers_with_positions(trader))
                bp = trader.get_portfolio_summary().get_total_bp() - get_unrealized_short_pnl(trader)
                if bp > 0:
                    amount = (bp/tickers_left_to_invest)
                    s = int((amount / trader.get_last_price(ticker)) / 100.)
                    buy = shift.Order(shift.Order.Type.MARKET_BUY, ticker, s)
                    trader.submit_order(buy)
                
            elif checker == True:
                # prev was in uptrend, now in downtrend
                sell_long(ticker, trader)
                #sleep
                sleep(safe_sleep)
                #take shorts with market order
                tickers_left_to_invest = len(tickers) - len(get_tickers_with_positions(trader))
                bp = trader.get_portfolio_summary().get_total_bp() - get_unrealized_short_pnl(trader)
                if bp > 0:
                    amount = ((bp/tickers_left_to_invest) / 2) * 0.99
                    s = int((amount / trader.get_last_price(ticker)) / 100.)
                    sell = shift.Order(shift.Order.Type.MARKET_SELL, ticker, s)
                    trader.submit_order(sell)


                       
            

        sleep(candle_size)
