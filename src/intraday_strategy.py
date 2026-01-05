import yfinance as yf
import pandas as pd
import ta
from ta.trend import EMAIndicator, MACD
from ta.volume import VolumeWeightedAveragePrice
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

# --- HIGH OCTANE INTRADAY LIST (High Beta + High Liquidity) ---
from src.config import WATCHLIST

def get_vsa_signal(df):
    """Calculates Effort vs Result (VSA) logic"""
    # High volume + Bullish close in the top 30% of the day's range
    bar_range = df['High'] - df['Low']
    bar_range = bar_range.replace(0, 0.0001)
    close_pos = (df['Close'] - df['Low']) / bar_range
    vol_ma = df['Volume'].rolling(window=20).mean()
    return (df['Volume'] > vol_ma) & (close_pos > 0.7)

def calculate_confidence(ticker_symbol):
    try:
        # 1. Fetch Intraday Data (5-minute intervals)
        df = yf.download(ticker_symbol, period='5d', interval='5m', progress=False)
        # Fetch Daily data for Previous Day High
        df_daily = yf.download(ticker_symbol, period='5d', interval='1d', progress=False)
        
        if df.empty or df_daily.empty: return 0, "No Data", 0, 0, 0, 0, 0, 0, 0, 0

        # Fix for yfinance returning MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if isinstance(df_daily.columns, pd.MultiIndex):
            df_daily.columns = df_daily.columns.get_level_values(0)

        prev_day_high = df_daily['High'].iloc[-2]
        
        # 2. Indicators (using 'ta' library)
        # EMA
        ema = EMAIndicator(close=df['Close'], window=200)
        df['EMA200'] = ema.ema_indicator()
        
        # VWAP
        vwap = VolumeWeightedAveragePrice(high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume'])
        df['VWAP'] = vwap.volume_weighted_average_price()
        
        # RSI
        rsi = RSIIndicator(close=df['Close'], window=14)
        df['RSI'] = rsi.rsi()
        
        # MACD
        macd = MACD(close=df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_Sig'] = macd.macd_signal()
        
        # Bollinger Bands
        bb = BollingerBands(close=df['Close'], window=20, window_dev=2)
        df['BB_Mid'] = bb.bollinger_mavg()
        
        # 3. Logic Checks (Latest Candle)
        last = df.iloc[-1]
        
        score = 0
        details = []
        
        # Check against EMA
        if last['Close'] > last['EMA200']:
            score += 15
            details.append("Trend (EMA200) ✅")
            
        # Check against VWAP
        if last['Close'] > last['VWAP']:
            score += 15
            details.append("Inst. Value (VWAP) ✅")
            
        # VSA Check
        vsa_signal = get_vsa_signal(df).iloc[-1]
        if vsa_signal:
            score += 15
            details.append("VSA (Effort/Result) ✅")
            
        # MACD Momentum
        if last['MACD'] > last['MACD_Sig']:
            score += 15
            details.append("MACD Momentum ✅")
            
        # Volatility
        if last['Close'] > last['BB_Mid']:
            score += 10
            details.append("Volatility (BB Mid) ✅")
            
        # RSI Strength
        if last['RSI'] > 60:
            score += 10
            details.append("RSI Strength (>60) ✅")
            
        # Day Breakout
        if last['Close'] > prev_day_high:
            score += 10
            details.append("Day Breakout (>PDH) ✅")
            
        # ATR for Dynamic SL
        from ta.volatility import AverageTrueRange
        atr_indicator = AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close'], window=14)
        df['ATR'] = atr_indicator.average_true_range()
        current_atr = df['ATR'].iloc[-1]
        
        # Trigger Candle High (High of the signal candle)
        trigger_high = last['High']
        current_vwap = last['VWAP']

        # Market Alignment (Simplified: Nifty Current Close > Open)
        nifty = yf.download('^NSEI', period='1d', interval='5m', progress=False)
        if not nifty.empty:
            if isinstance(nifty.columns, pd.MultiIndex):
                nifty.columns = nifty.columns.get_level_values(0)
            
            if nifty['Close'].iloc[-1] > nifty['Open'].iloc[-1]:
                score += 10
                details.append("Market Alignment (Nifty Green) ✅")
        
        pdl = df_daily['Low'].iloc[-2]
        prev_close = df_daily['Close'].iloc[-2]
        todays_high = df_daily['High'].iloc[-1]
        
        # Safe Target: 0.5% (This will be overridden by RRR 1:2 in tracker, but good for display)
        exit_price = todays_high * 1.005

        return score, details, prev_day_high, pdl, prev_close, todays_high, exit_price, current_atr, trigger_high, current_vwap
    except Exception as e:
        return 0, f"Error: {e}", 0, 0, 0, 0, 0, 0, 0, 0
