import pandas as pd
import ta

def calculate_technical_indicators(df):
    """
    Calculates technical indicators like RSI, MACD, Bollinger Bands.
    """
    if df.empty:
        return df
    
    # RSI
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    # MACD
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    
    # Bollinger Bands
    bollinger = ta.volatility.BollingerBands(df['Close'])
    df['BB_High'] = bollinger.bollinger_hband()
    df['BB_Low'] = bollinger.bollinger_lband()
    
    # Moving Averages
    df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
    df['EMA_20'] = ta.trend.ema_indicator(df['Close'], window=20)
    
    # Daily Return (needed for model)
    df['Daily_Return'] = df['Close'].pct_change()

    # ATR (Average True Range)
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
    
    # Stochastic Oscillator
    df['Stoch_K'] = ta.momentum.stoch(df['High'], df['Low'], df['Close'], window=14, smooth_window=3)
    df['Stoch_D'] = ta.momentum.stoch_signal(df['High'], df['Low'], df['Close'], window=14, smooth_window=3)
    
    # OBV (On-Balance Volume)
    df['OBV'] = ta.volume.on_balance_volume(df['Close'], df['Volume'])
    
    return df

def calculate_market_metrics(df, benchmark_df):
    """
    Calculates market-relative metrics like Beta and Relative Return.
    """
    if df.empty or benchmark_df.empty:
        return df
        
    # Align dates
    df_aligned = df.copy()
    bench_aligned = benchmark_df.copy()
    
    # Align dates by resetting index
    df_aligned = df.reset_index()
    bench_aligned = benchmark_df.reset_index()
    
    # Ensure Date column is datetime and timezone naive
    df_aligned['Date'] = pd.to_datetime(df_aligned['Date'], utc=True).dt.tz_localize(None)
    bench_aligned['Date'] = pd.to_datetime(bench_aligned['Date'], utc=True).dt.tz_localize(None)
    
    # Merge on Date
    merged = pd.merge(df_aligned, bench_aligned[['Date', 'Close']], on='Date', how='inner', suffixes=('', '_Market'))
    
    # Rename Market Close
    merged.rename(columns={'Close_Market': 'Market_Close'}, inplace=True)
    
    # Set Date back as index
    merged.set_index('Date', inplace=True)
    
    # Return merged directly (it has all original cols + new cols)
    # The index is now naive, which is safer for downstream tasks
    return merged

def calculate_statistics(df):
    """
    Calculates basic statistics like volatility and daily returns.
    """
    if df.empty:
        return {}
        
    df['Daily_Return'] = df['Close'].pct_change()
    volatility = df['Daily_Return'].std() * (252 ** 0.5) # Annualized volatility
    
    return {
        "Volatility": volatility,
        "Last Price": df['Close'].iloc[-1]
    }
