import shift
from time import sleep
from datetime import datetime, timedelta, time
import numpy as np
from typing import Dict, Any, Tuple, List, String
from scipy.stats import linregress
from multiprocessing import Process, Manager
from collections import deque
from routine_summary import routine_summary
import math
import sys
sys.path.insert(1, '../')
from credentials import credentials
import datetime as dt

ticker = "AAPL"

def run_market_maker(trader: shift.Trader, ticker: String):

    maximum_allocation = .15

    for item in trader.get_portfolio_items().values():
        ticker = item.get_symbol()
        current_shares = item.get_shares()

    bid = trader.get_best_price(ticker).get_bid_price()
    ask = trader.get_best_price(ticker).get_ask_price()
    mid_price = (bid + ask) / 2 

    current_position_value = current_shares * mid_price

    

    minimum_spread = 0.05

    if (ask-bid )* 0.25 < minimum_spread:
    