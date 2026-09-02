"""
NSE Intraday Stock Screener & Signal Engine
--------------------------------------------
Fetches intraday price data for a list of NSE stocks and generates
rule-based BUY / SELL / HOLD signals using RSI, MACD and EMA indicators.

Author: Dorilal Pandey
"""

import yfinance as yf
import pandas as pd


# ---------------------------------------------------------
# Indicator functions
# ---------------------------------------------------------

def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD line and Signal line."""
    ema_fast = calculate_ema(series, fast)
    ema_slow = calculate_ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    return macd_line, signal_line


# ---------------------------------------------------------
# Signal generation
# ---------------------------------------------------------

def generate_signal(df: pd.DataFrame) -> str:
    """
    Simple rule-based signal:
    BUY  -> RSI < 40 (not oversold-extreme), MACD above signal line,
            and price above short-term EMA (uptrend confirmation)
    SELL -> RSI > 60, MACD below signal line, price below short-term EMA
    Else -> HOLD
    """
    latest = df.iloc[-1]

    bullish = (
        latest["RSI"] < 40
        and latest["MACD"] > latest["MACD_Signal"]
        and latest["Close"] > latest["EMA20"]
    )
    bearish = (
        latest["RSI"] > 60
        and latest["MACD"] < latest["MACD_Signal"]
        and latest["Close"] < latest["EMA20"]
    )

    if bullish:
        return "BUY"
    elif bearish:
        return "SELL"
    else:
        return "HOLD"


# ---------------------------------------------------------
# Main screener
# ---------------------------------------------------------

def screen_stock(symbol: str, period: str = "5d", interval: str = "15m") -> dict:
    """Download data for one NSE symbol and return its latest signal."""
    ticker = symbol if symbol.endswith(".NS") else symbol + ".NS"
    data = yf.download(ticker, period=period, interval=interval, progress=False)

    if data.empty or len(data) < 30:
        return {"symbol": symbol, "signal": "NO DATA", "close": None}

    data["EMA20"] = calculate_ema(data["Close"], 20)
    data["RSI"] = calculate_rsi(data["Close"], 14)
    data["MACD"], data["MACD_Signal"] = calculate_macd(data["Close"])
    data.dropna(inplace=True)

    if data.empty:
        return {"symbol": symbol, "signal": "NO DATA", "close": None}

    signal = generate_signal(data)
    latest_close = round(float(data["Close"].iloc[-1]), 2)

    return {"symbol": symbol, "signal": signal, "close": latest_close}


def run_screener(watchlist: list) -> pd.DataFrame:
    """Run the screener across a watchlist and return a results table."""
    results = [screen_stock(sym) for sym in watchlist]
    return pd.DataFrame(results)


if __name__ == "__main__":
    # Sample NSE watchlist - edit as needed
    watchlist = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]

    results_df = run_screener(watchlist)
    print("\nNSE Intraday Screener Results\n" + "-" * 35)
    print(results_df.to_string(index=False))
