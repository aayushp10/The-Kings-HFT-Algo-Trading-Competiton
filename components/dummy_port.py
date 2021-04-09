import pandas as pd
import pandas_datareader as dr
from pandas_datareader._utils import RemoteDataError

# port = {'AAPL': 0.0036018203741732574, 'AXP': 0.00964639725376874, 'BA': 0.7213856282008926, 'CAT': 0.008236015068300838, 'CSCO': 0.004290179655046926, 'CVX': 0.007423323120303128, 'DIS': 0.00685694334215154, 'GS': 0.019414354788615355, 'HD': 0.05795630826623566, 'IBM': 0.0165876420819983, 'INTC': 0.003910008794326724, 'JNJ': 0.006436303626780968, 'JPM': 0.004728034343079771, 'KO': 0.0030210133102177824, 'MCD': 0.012756898154372035, 'MMM': 0.024163821793494362, 'MRK': 0.004397983805951055, 'MSFT': 0.01169880717389495, 'NKE': 0.0057539821379696265, 'PFE': 0.0025628785364548447, 'PG': 0.008665650194975838, 'TRV': 0.008672119801953164, 'UNH': 0.019602323453073656, 'V': 0.011137610684253958, 'VZ': 0.0026896728635883373, 'WBA': 0.005561381440607512, 'WMT': 0.0043780717776686654, 'XOM': 0.00446482595585055}
tickers = ["WBA", "CSCO", "BA", "CAT"]
ts = ['AAPL', 'AXP', 'BA', 'CAT', 'CSCO', 'CVX', 'DIS', 'GS', 'HD', 'IBM', 'INTC', 'JNJ', 'JPM', 'KO', 'MCD', 'MMM', 'MRK', 'MSFT', 'NKE', 'PFE', 'PG', 'TRV', 'UNH', 'V', 'VZ', 'WBA', 'WMT', 'XOM']
avgs = [-0.014229110731044171, -0.015364818981689492, -0.016386232944043667, -0.013376504931063389, -0.02045143854240294, -0.013181590674958239, -0.011184412115872866, -0.012286477634447047, -0.015488882482471095, -0.016321154085811695, -0.01740382773529333, -0.010349513673295023, -0.009281042945570347, -0.011393456794019324, -0.009898134966532326, -0.017171167473417653, -0.011956099527086744, -0.014469973282474657, -0.0137962076974184, -0.013546501557688335, -0.01356667185683433, -0.011545675704908775, -0.011509114721540288, -0.01113516399214566, -0.008399774570199338, -0.02251776159012775, -0.008421255155692885, -0.014768965249368708]
print(list(zip(*sorted(zip(avgs, ts)))))
exit()
port = {}
for t in tickers:
    port[t] = 1/float(len(tickers))

days = ['2019-05-07', '2019-05-13', '2019-08-05', 
        '2019-08-14', '2019-10-02', '2018-12-24', '2019-01-03',
        '2018-12-17', '2018-12-19', '2018-12-20', '2019-05-28']
# days = ['2019-10-02']
# days = ['2018-12-24', '2019-01-03',
#         '2018-12-17', '2018-12-19', '2018-12-20', '2019-05-28']
ret_per_day = {}
port_rets = []
for day in days:
    rets = []
    for ticker in port.keys():
        try:
            df = dr.DataReader(ticker, start=day, end=day, data_source='yahoo')
            current_return = -1*(df.iloc[0]['Close'] - df.iloc[0]['Open'])/df.iloc[0]['Open']
            rets.append(current_return*port[ticker])
            # rets.append(curret_return)
            
            # limitSellPrice = df.iloc[0]['Close'] * port[ticker]
            # limitBuyPrice = df.iloc[0]['Open'] * port[ticker]
            # limit_sell = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, 1, limitSellPrice)
            # limit_buy = shift.Order(shift.Order.Type.LIMIT_BUY, ticker, 1, limitBuyPrice)
            print(ticker)
        except RemoteDataError:
            break
    if day not in rets:
        ret_per_day[day] = []
    ret_per_day[day].append(sum(rets))
    port_rets.append(sum(rets))
    print(day)

print(ret_per_day)
print(f"Total $ P/L: {1000000*(sum(port_rets)/float(len(port_rets)))}")
