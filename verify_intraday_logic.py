
import yfinance as yf
import pandas as pd
import ta
from ta.trend import EMAIndicator, MACD
from ta.volume import VolumeWeightedAveragePrice
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

def get_vsa_signal(df):
    bar_range = df['High'] - df['Low']
    bar_range = bar_range.replace(0, 0.0001)
    close_pos = (df['Close'] - df['Low']) / bar_range
    vol_ma = df['Volume'].rolling(window=20).mean()
    return (df['Volume'] > vol_ma) & (close_pos > 0.7)


def calculate_confidence_mock(ticker):
    # This is a mock to verify the signature if we imported it, 
    # but since we copy-pasted logic in verify script, we need to update the verify script 
    # to actually RUN the logic and return the values.
    
    # We will update the logic below in verify_logic to match Intraday.py changes
    pass

def verify_logic():
    print("Testing Intraday Logic using 'ta' library with new columns...")
    ticker_symbol = "RELIANCE.NS"
    try:
        df = yf.download(ticker_symbol, period='5d', interval='5m', progress=False)
        df_daily = yf.download(ticker_symbol, period='5d', interval='1d', progress=False)
        
        if df.empty:
            print("Error: Empty DF")
            return
            
        # Fix for yfinance returning MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if isinstance(df_daily.columns, pd.MultiIndex):
            df_daily.columns = df_daily.columns.get_level_values(0)

        prev_day_high = df_daily['High'].iloc[-2]
        pdl = df_daily['Low'].iloc[-2]
        prev_close = df_daily['Close'].iloc[-2]
        todays_high = df_daily['High'].iloc[-1]
        exit_price = todays_high * 1.005
        
        print(f"PDH: {prev_day_high}, PDL: {pdl}, Prev Close: {prev_close}, Safe Entry: {todays_high}, Exit Price: {exit_price}")
        
        # 2. Indicators (using 'ta' library)
        ema = EMAIndicator(close=df['Close'], window=200)
        df['EMA200'] = ema.ema_indicator()
        
        vwap = VolumeWeightedAveragePrice(high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume'])
        df['VWAP'] = vwap.volume_weighted_average_price()
        
        rsi = RSIIndicator(close=df['Close'], window=14)
        df['RSI'] = rsi.rsi()
        
        macd = MACD(close=df['Close'])
        df['MACD'] = macd.macd()
        
        bb = BollingerBands(close=df['Close'], window=20, window_dev=2)
        df['BB_Mid'] = bb.bollinger_mavg()
        
        print("Tail of DF with indicators:")
        print(df[['Close', 'EMA200', 'VWAP', 'RSI', 'MACD', 'BB_Mid']].tail(2))
        
        # Verify Nifty logic specifically
        print("Verifying Nifty logic...")
        nifty = yf.download('^NSEI', period='1d', interval='5m', progress=False)
        if not nifty.empty:
            if isinstance(nifty.columns, pd.MultiIndex):
                print("Nifty MultiIndex detected, flattening...")
                nifty.columns = nifty.columns.get_level_values(0)
            
            close_val = nifty['Close'].iloc[-1]
            open_val = nifty['Open'].iloc[-1]
            print(f"Nifty Close: {close_val}, Open: {open_val}, Type: {type(close_val)}")
            if isinstance(close_val, pd.Series):
                raise ValueError("Nifty Close is still a Series!")
            
            if close_val > open_val:
                print("Nifty Green")
            else:
                print("Nifty Red")
        
        print("Success")
    except Exception as e:
        print(f"FAILED with error: {e}")

if __name__ == "__main__":
    verify_logic()
