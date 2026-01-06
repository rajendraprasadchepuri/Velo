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

def get_vsa_bear_signal(df):
    """Calculates VSA Short Logic (Effort/Result Bearish)"""
    # High volume + Bearish close in bottom 30% of range
    bar_range = df['High'] - df['Low']
    bar_range = bar_range.replace(0, 0.0001)
    close_pos = (df['Close'] - df['Low']) / bar_range
    vol_ma = df['Volume'].rolling(window=20).mean()
    return (df['Volume'] > vol_ma) & (close_pos < 0.3)

def calculate_confidence(ticker_symbol):
    try:
        # 1. Fetch Intraday Data (5-minute intervals)
        df = yf.download(ticker_symbol, period='5d', interval='5m', progress=False)
        # Fetch Daily data for Previous Day High/Low
        df_daily = yf.download(ticker_symbol, period='5d', interval='1d', progress=False)
        
        if df.empty or df_daily.empty: return 0, "No Data", 0, 0, 0, 0, 0, 0, 0, 0, "NEUTRAL"

        # Fix for yfinance returning MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if isinstance(df_daily.columns, pd.MultiIndex):
            df_daily.columns = df_daily.columns.get_level_values(0)

        prev_day_high = df_daily['High'].iloc[-2]
        prev_day_low = df_daily['Low'].iloc[-2]
        
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
        
        # ATR
        from ta.volatility import AverageTrueRange
        atr_indicator = AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close'], window=14)
        df['ATR'] = atr_indicator.average_true_range()
        current_atr = df['ATR'].iloc[-1]

        # 3. Logic Checks (Latest Candle)
        last = df.iloc[-1]
        
        # --- BULL SCORING ---
        bull_score = 0
        bull_details = []
        
        if last['Close'] > last['EMA200']:
            bull_score += 15
            bull_details.append("Trend > EMA200")
        if last['Close'] > last['VWAP']:
            bull_score += 15
            bull_details.append("Val > VWAP")
        if get_vsa_signal(df).iloc[-1]:
            bull_score += 15
            bull_details.append("VSA Bull Vol")
        if last['MACD'] > last['MACD_Sig']:
            bull_score += 15
            bull_details.append("MACD Bull Cross")
        if last['Close'] > last['BB_Mid']:
            bull_score += 10
            bull_details.append("Price > BB Mid")
        if last['RSI'] > 60:
            bull_score += 10
            bull_details.append("RSI Bullish (>60)")
        if last['Close'] > prev_day_high:
            bull_score += 10
            bull_details.append("Breakout > PDH")

        # --- BEAR SCORING ---
        bear_score = 0
        bear_details = []
        
        if last['Close'] < last['EMA200']:
            bear_score += 15
            bear_details.append("Trend < EMA200")
        if last['Close'] < last['VWAP']:
            bear_score += 15
            bear_details.append("Val < VWAP")
        if get_vsa_bear_signal(df).iloc[-1]:
            bear_score += 15
            bear_details.append("VSA Bear Vol")
        if last['MACD'] < last['MACD_Sig']:
            bear_score += 15
            bear_details.append("MACD Bear Cross")
        if last['Close'] < last['BB_Mid']:
            bear_score += 10
            bear_details.append("Price < BB Mid")
        if last['RSI'] < 40:
            bear_score += 10
            bear_details.append("RSI Bearish (<40)")
        if last['Close'] < prev_day_low:
            bear_score += 10
            bear_details.append("Breakdown < PDL")

        # Market Alignment
        nifty = yf.download('^NSEI', period='1d', interval='5m', progress=False)
        if not nifty.empty:
            if isinstance(nifty.columns, pd.MultiIndex):
                nifty.columns = nifty.columns.get_level_values(0)
            
            nifty_close = nifty['Close'].iloc[-1]
            nifty_open = nifty['Open'].iloc[-1]
            
            if nifty_close > nifty_open:
                bull_score += 10
                bull_details.append("Nifty Green")
            else:
                bear_score += 10
                bear_details.append("Nifty Red")
        
        # --- DECISION ---
        prev_close = df_daily['Close'].iloc[-2]
        todays_high = df_daily['High'].iloc[-1] # Used as Safe Entry for Long
        todays_low = df_daily['Low'].iloc[-1]   # Used as Safe Entry for Short
        current_vwap = last['VWAP']
        
        if bull_score >= bear_score:
            final_score = bull_score
            final_details = bull_details
            side = "BUY"
            safe_entry = todays_high
            trigger_price = last['High']
            target_price = safe_entry * 1.005
        else:
            final_score = bear_score
            final_details = bear_details
            side = "SELL"
            safe_entry = todays_low
            trigger_price = last['Low']
            target_price = safe_entry * 0.995

        from src.utils import round_to_tick
        return final_score, final_details, round_to_tick(prev_day_high), round_to_tick(prev_day_low), round_to_tick(prev_close), round_to_tick(safe_entry), round_to_tick(target_price), round_to_tick(current_atr), round_to_tick(trigger_price), round_to_tick(current_vwap), side

    except Exception as e:
        return 0, [f"Error: {e}"], 0, 0, 0, 0, 0, 0, 0, 0, "NEUTRAL"
