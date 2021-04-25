import math
class Candle:

    def __init__(self, open_val, close_val, low_val, high_val):
        self.open = None if math.isnan(open_val) else open_val
        self.close = None if math.isnan(close_val) else close_val
        self.high = None if math.isnan(high_val) else high_val
        self.low = None if math.isnan(low_val) else low_val

    def setOpen(self, o):
        self.open = o
    def setClose(self, c):
        self.close = c
    def setHigh(self, h):
        self.high = h
    def setLow(self, l):
        self.low = l
        
