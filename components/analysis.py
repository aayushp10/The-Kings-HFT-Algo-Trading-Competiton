import pandas as pd
import yfinance as yf
import pandas_datareader.data as dr
from pandas_datareader._utils import RemoteDataError

tickers = {'AAPL': 'Apple Inc.',  
'AXP': 'American Express Company',  
'BA': 'The Boeing Company',  
'CAT': 'Caterpillar Inc.',  
'CSCO': 'Cisco Systems, Inc.',  
'CVX': 'Chevron Corporation',  
'DIS': 'The Walt Disney Company',  
'DWDP': 'DowDuPont Inc.',  
'GS': 'The Goldman Sachs Group, Inc.',  
'HD': 'The Home Depot, Inc.',  
'IBM': 'International Business Machines Corporation',  
'INTC': 'Intel Corporation',  
'JNJ': 'Johnson & Johnson',  
'JPM': 'JPMorgan Chase & Co.',  
'KO': 'The Coca-Cola Company',  
'MCD': "McDonald's Corporation",  
'MMM': '3M Company',  
'MRK': 'Merck & Co., Inc.',  
'MSFT': 'Microsoft Corporation',  
'NKE': 'NIKE, Inc.',  
'PFE': 'Pfizer Inc.',  
'PG': 'The Procter & Gamble Company',  
'TRV': 'The Travelers Companies, Inc.',  
'UNH': 'UnitedHealth Group Incorporated',  
'UTX': 'United Technologies Corporation',  
'V': 'Visa Inc.',  
'VZ': 'Verizon Communications Inc.',  
'WBA': 'Walgreens Boots Alliance, Inc.',  
'WMT': 'Walmart Inc.',  
'XOM': 'Exxon Mobil Corporation'}

market_days = ['2019-05-07', '2019-05-13', '2019-08-05', '2019-08-14', '2019-10-02']
days = ['2019-08-23', '2018-12-04', '2018-10-10','2019-05-07', '2019-05-13', '2019-08-05', '2019-08-14', '2019-10-02', '2018-02-05', '2018-02-08',
        '2018-03-22', '2018-04-24', '2018-05-29', '2018-11-12']
min_min = list(tickers.keys())[0]
max_avg = list(tickers.keys())[0]
min_avg = list(tickers.keys())[0]

data = {}
for ticker in tickers.keys():
    rets = []
    for day in days:
        try:
            df = dr.DataReader(ticker, start=day, end=day, data_source='yahoo')
            rets.append((df.iloc[0]['Close'] - df.iloc[0]['Open'])/df.iloc[0]['Open'])
        except RemoteDataError:
            break
    data[ticker] = rets
    if len(rets) > 0:
        avg = sum(rets)/float(len(rets))
        print(ticker + "::::::AVG:::::::" + f"{avg}::::::MAX::::::{max(rets)}:::::{min(rets)}" )
        
        if(min(rets) < min(data[min_min])):
            min_min = ticker
        if(avg > sum(data[max_avg])/float(len(data[max_avg]))):
            max_avg = ticker
        if(avg < sum(data[max_avg])/float(len(data[max_avg]))):
            min_avg = ticker

print(f"MAX-AVG:::{max_avg}:::{sum(data[max_avg])/float(len(data[max_avg]))}")
print(f"MIN-AVG:::{min_avg}:::{sum(data[min_avg])/float(len(data[min_avg]))}")
print(f"MIN-MIN:::{min_min}:::{min(data[min_min])}")