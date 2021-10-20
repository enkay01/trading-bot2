import ccxt
import sys
import websocket, json, pprint, numpy as np, talib as tlb, pandas as pd, matplotlib.pyplot as plt
from dependencies import secrets

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
RSI_PERIOD = 14
BOLL_PERIOD = 5
EMA_SHORT = 12
EMA_MID = 100
EMA_LONG = 200
RSI_HIGH = 70
RSI_LOW = 30


class streamer:
    def get_exchange(self, exchange_id):
        if "binance" in exchange_id:
            return ccxt.binance();
        return ccxt.binanceus();
    def get_ohlc(self, pair, timeframe, since=None, limit=None):
        ohlc = self.exchange.get_ohlc(pair, timeframe, limit, since)
        return ohlc
    def __init__(self, exchange_id='binance'):
        self.exchange_class = getattr(ccxt, exchange_id)
        self.exchange = self.exchange_class({
            'apiKey': secrets.API_KEY,
            'secret': secrets.API_SECRET,
            'timeout': 30000
        })

def get_ohlc(pair, timeframe, limit):
    exchange=ccxt.binance()
    data = exchange.fetch_ohlcv(pair, timeframe, limit)
    return pd.DataFrame(data, columns=["Date", "Open", "High", "Low", "Close", "Volume"])

def get_all_indicators(data):
    data["rsi"] = tlb.RSI(data["close"], timeperiod=RSI_PERIOD)
    data["macd"], data["macd signal"], data["macd hist"] = tlb.MACD(data["close"], fastperiod=MACD_FAST, slowperiod=MACD_SLOW, signalperiod=MACD_SIGNAL)
    data["boll upper"], data["boll middle"], data["boll lower"] = tlb.BBANDS(data["close"], timeperiod=BOLL_PERIOD, nbdevup=2, nbdevdn=2, matype=0)
    #data["ema 10"] = tlb.EMA(data["close"], timeperiod=EMA_SHORT)
    data[f"ema {EMA_MID}"] = tlb.EMA(data["close"], timeperiod=EMA_MID)
    data[f"ema {EMA_LONG}"] = tlb.EMA(data["close"], timeperiod=EMA_LONG)

    return data
#Converts each indicator value into a binary decision, buy or sell
def get_price_signals(data):
    rsi_bs = [0]
    macd_bs = [0]
    boll_bs = [0]
    for current in range(1,len(data["date"])):
        previous = current -1
        rsi_bs.append( eval_rsi(data["rsi"][current], data["rsi"][previous]) )
        macd_bs.append( eval_macd(data["macd"][current], data["macd"][previous]) )
        boll_bs.append( eval_boll(data["high"][current], data["boll upper"][current], data["boll lower"][current]) )
    
    data["rsi buy/sell"] = rsi_bs
    data["macd buy/sell"] = macd_bs
    data["boll buy/sell"] = boll_bs
    return data

def eval_rsi(value, prev):
    if value > RSI_HIGH and prev < RSI_HIGH: 
        return -1
    elif value < RSI_LOW and prev > RSI_LOW:
        return 1
    return 0
def eval_macd(value, prev):
    if value > 0:
        return 1
    return -1
def eval_boll(value, boll_high, boll_low):
    if value > boll_high:
        return -1
    elif value < boll_low:
        return 1
    return 0

if __name__ == '__main__':
    strm = streamer()
    exchange = ccxt.binance();
    #Get price points and volume
    eth_data = pd.DataFrame(exchange.fetch_ohlcv('ETH/USDT', timeframe='1d', limit=1000), columns=["date", "open", "high", "low", "close", "volume"] )
    eth_data["date"] = pd.to_datetime(eth_data["date"], unit='ms')
    btc_data = pd.DataFrame(exchange.fetch_ohlcv('BTC/USDT', timeframe='1d', limit=1000), columns=["date", "open", "high", "low", "close", "volume"])
    btc_data["date"] = pd.to_datetime(btc_data["date"], unit='ms')
    ada_data =pd.DataFrame(exchange.fetch_ohlcv('ADA/USDT', timeframe='1d', limit=1000), columns=["date", "open", "high", "low", "close", "volume"])
    ada_data["date"] = pd.to_datetime(ada_data["date"], unit='ms')
    sol_data = pd.DataFrame(exchange.fetch_ohlcv('SOL/USDT', timeframe='1d', limit=1000), columns=["date", "open", "high", "low", "close", "volume"])
    sol_data["date"] = pd.to_datetime(sol_data["date"], unit='ms')
    
    #Calculate indicator values
    eth_data = get_all_indicators(eth_data)
    btc_data = get_all_indicators(btc_data.dropna())
    ada_data = get_all_indicators(ada_data)
    sol_data = get_all_indicators(sol_data)
    
    eth_data = get_price_signals(eth_data)
    btc_data = get_price_signals(btc_data)
    ada_data = get_price_signals(ada_data)
    sol_data = get_price_signals(ada_data)

    eth_data = eth_data.dropna()
    btc_data = btc_data.dropna()
    ada_data = ada_data.dropna()
    sol_data = sol_data.dropna()

    fig, a = plt.subplots(nrows=2, ncols=1)
    a[0].plot(btc_data["date"], btc_data["close"])
    a[1].plot(btc_data["date"], btc_data["rsi"])
    a[1].axhline(y=70, linestyle="--")
    a[1].axhline(y=30, linestyle="--")    
    plt.show()