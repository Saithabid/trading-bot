"""
STRATEGY.PY
------------
Market analysis: trend + RSI + volatility (ATR) dekh kar BUY/SELL/WAIT decide karta hai.
Sirf tab signal deta hai jab confluence ho (multiple cheezein align hon) - isse
fizool trades kam hoti hain.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np


def get_candle_data(symbol, timeframe=mt5.TIMEFRAME_M15, count=100):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df


def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_atr(df, period=14):
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(window=period).mean()


def analyze_market(symbol):
    df = get_candle_data(symbol)
    if df is None or len(df) < 50:
        return {"signal": "WAIT", "reason": "Naakafi data mila"}

    df['ma20'] = df['close'].rolling(window=20).mean()
    df['ma50'] = df['close'].rolling(window=50).mean()
    df['rsi'] = calculate_rsi(df['close'])
    df['atr'] = calculate_atr(df)

    latest = df.iloc[-1]
    current_price = latest['close']
    ma20, ma50, rsi, atr = latest['ma20'], latest['ma50'], latest['rsi'], latest['atr']

    trend_up = ma20 > ma50 and current_price > ma20
    trend_down = ma20 < ma50 and current_price < ma20
    rsi_ok_for_buy = 40 < rsi < 70
    rsi_ok_for_sell = 30 < rsi < 60

    if trend_up and rsi_ok_for_buy:
        return {"signal": "BUY", "price": current_price, "atr": atr,
                "reason": f"Uptrend + RSI {rsi:.1f} healthy zone"}
    elif trend_down and rsi_ok_for_sell:
        return {"signal": "SELL", "price": current_price, "atr": atr,
                "reason": f"Downtrend + RSI {rsi:.1f} healthy zone"}
    else:
        return {"signal": "WAIT", "price": current_price, "atr": atr,
                "reason": "Signals align nahi hue"}
