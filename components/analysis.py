import pandas as pd
import yfinance as yf
import pandas_datareader.data as dr
import numpy as np
from pandas_datareader._utils import RemoteDataError

def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    return np.exp(x) / np.sum(np.exp(x), axis=0)

tickers = {
    'AAPL': 'Apple Inc.',  
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
    'XOM': 'Exxon Mobil Corporation'
}


'''
['TRV', 'DIS', 'VZ', 'MSFT', 'KO', 'V', 'JNJ', 'CVX', 'IBM', 'AXP', 'INTC', 'WMT', 'MRK', 'JPM', 'XOM', 'PFE', 'HD', 'MCD', 'GS', 'NKE', 'UNH', 'AAPL', 'CSCO', 'WBA', 'PG', 'BA', 'CAT', 'MMM']
AVG
[0.006804165014295144, 0.0069162006893653954, 0.006979930534064563, 0.007021098234166199, 0.007071759915277254, 0.007303446173000455, 0.007796492778031174, 0.007881286428098476, 0.008271589663688374, 0.008447865808300002, 0.008847976531230834, 0.008941326216667373, 0.009035064761455555, 0.009169194013520333, 0.009221572191817042, 0.009728065526704108, 0.009972094907628574, 0.010028822692407407, 0.010066230324484185, 0.010996511114825178, 0.011284139056102774, 0.011356935306649541, 0.011707276490378308, 0.011824644454985267, 0.011850617098153762, 0.01261207743630266, 0.013308770464007788, 0.014729161858995629]

volumes
{'TRV': 630620.0, 'GS': 1241400.0, 'MMM': 1615540.0, 'IBM': 1879400.0, 'CAT': 1917140.0, 'UNH': 1984040.0, 'AXP': 1996060.0, 'MCD': 2234320.0, 'HD': 2446080.0, 'WBA': 2575100.0, 'CVX': 2771360.0, 'BA': 2878760.0, 'WMT': 3477820.0, 'NKE': 3645720.0, 'JNJ': 3934680.0, 'MRK': 4261940.0, 'DIS': 4415320.0, 'V': 4420900.0, 'PG': 4658660.0, 'KO': 6274020.0, 'JPM': 6287120.0, 'XOM': 6456220.0, 'VZ': 7372640.0, 'PFE': 8672860.0, 'INTC': 10606100.0, 'CSCO': 11377800.0, 'MSFT': 12484140.0, 'AAPL': 66018640.0}


'''

days = ['2019-12-24', '2019-07-03', '2019-12-26', '2019-11-29', '2019-10-14']

max_max = list(tickers.keys())[0]
max_avg = list(tickers.keys())[0]
min_avg = list(tickers.keys())[0]

data = {}
used_tickers = []
avgs = []
maxs = []

volume = {}
for ticker in tickers.keys():
    rets = []
    volumes = []
    for day in days:
        try:
            df = dr.DataReader(ticker, start=day, end=day, data_source='yahoo')
            rets.append((df.iloc[0]['High'] - df.iloc[0]['Low'])/df.iloc[0]['Low'])
            volumes.append(df.iloc[0]['Volume'])
        except Exception:
            print("ERROR ON DAY")
            print(day)
            break
    data[ticker] = rets
    
    if len(volumes) > 0:
        avg_volume = sum(volumes)/float(len(volumes))
        volume[ticker] = avg_volume
    if len(rets) > 0:
        avg = sum(rets)/float(len(rets))
        used_tickers.append(ticker)
        avgs.append(avg)
        
        print(ticker + "::::::AVG:::::::" + f"{avg}" )
        
        # if(max(rets) < max(data[max_max])):
        #     max_max = ticker
        # if(avg > sum(data[max_avg])/float(len(data[max_avg]))):
        #     max_avg = ticker
        # if(avg < sum(data[max_avg])/float(len(data[max_avg]))):
            # min_avg = ticker

softmax_weights = softmax(maxs)

avgs, final_tickers = (list(t) for t in zip(*sorted(zip(avgs, used_tickers))))

print("TICKERS")
print(final_tickers)
print("AVG")
print(avgs)
print("Volumes")
print(volume)
# print("SOFTMAX")
# print(softmax_weights)

# print(f"MAX-AVG:::{max_avg}:::{sum(data[max_avg])/float(len(data[max_avg]))}")
# print(f"MIN-AVG:::{min_avg}:::{sum(data[min_avg])/float(len(data[min_avg]))}")
# print(f"MIN-MIN:::{min_min}:::{min(data[min_min])}")
