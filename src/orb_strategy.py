import pandas as pd
import yfinance as yf
from datetime import datetime, time
import numpy as np
from src.utils import fetch_data_robust, round_to_tick

def calculate_orb_signal(ticker):
    """
    Calculates 30-Minute Opening Range Breakout (ORB) Signal.
    Range: 09:15 to 09:45.
    
    Returns:
        score (int): 0-100 Confidence Score
        details (list): Reasoning
        orb_high, orb_low, entry, sl, target
    """
    try:
        # 1. Fetch Today's 5m Data
        # We need data starting from 09:15 today.
        # yfinance period="1d", interval="5m" handles today's data.
        df = fetch_data_robust(ticker, period="1d", interval="5m")
        
        if df is None or df.empty or len(df) < 6:
            return 0, ["Insufficient Data (Need > 30 mins)"], 0, 0, 0, 0, 0, "NEUTRAL"
            
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        # 2. Define ORB Window (09:15 - 09:45)
        # Assuming timestamps are localized or standard. YF usually returns local IST if indian stocks, or UTC.
        # Check first candle time. If it's 03:45 UTC (09:15 IST), we handle accordingly.
        # Logic: Take the first 6 candles (6 * 5m = 30m).
        
        orb_candles = df.iloc[:6] 
        # Verify time range roughly?
        # first_candle_time = orb_candles.index[0]
        # print(f"{ticker} Start: {first_candle_time.time()}")
        
        orb_high = orb_candles['High'].max()
        orb_low = orb_candles['Low'].min()
        orb_range = orb_high - orb_low
        
        if orb_range == 0:
             return 0, ["No Range"], 0, 0, 0, 0, 0, "NEUTRAL"
             
        # 3. Current Status
        latest = df.iloc[-1]
        current_price = latest['Close']
        volume_spike = latest['Volume'] > df['Volume'].mean() * 1.5
        
        score = 0
        details = []
        signal_side = "NEUTRAL"
        
        # 4. Breakout Logic
        # BUY
        if current_price > orb_high:
            score = 60 # Base breakout
            details.append(f"ORB Breakout: Price {current_price:.2f} > High {orb_high:.2f}")
            signal_side = "BUY"
            
            if volume_spike:
                score += 20
                details.append("High Volume Breakout")
                
            # Trend Check (Price > VWAP approx or EMA)
            # Simple EMA20 on 5m
            ema20 = df['Close'].ewm(span=20).mean().iloc[-1]
            if current_price > ema20:
                score += 10
                details.append("Above 5m EMA20")
            
            entry = orb_high + 0.05
            sl = orb_low
            target = entry + orb_range # 1:1 Target initially
            
        # SELL
        elif current_price < orb_low:
            score = 60
            details.append(f"ORB Breakdown: Price {current_price:.2f} < Low {orb_low:.2f}")
            signal_side = "SELL"
            
            if volume_spike:
                score += 20
                details.append("High Volume Breakdown")
                
            ema20 = df['Close'].ewm(span=20).mean().iloc[-1]
            if current_price < ema20:
                score += 10
                details.append("Below 5m EMA20")

            entry = orb_low - 0.05
            sl = orb_high
            target = entry - orb_range 
            
        else:
            # Inside Range
            details.append(f"Inside Range ({orb_low:.2f} - {orb_high:.2f})")
            return 0, details, round_to_tick(orb_high), round_to_tick(orb_low), 0, 0, 0, "NEUTRAL"

        # --- SECTOR ALIGNMENT (SCIENTIFIC FILTER) ---
        from src.sector_analysis import check_alignment
        if score > 0:
            mod, reason, chg = check_alignment(ticker, signal_side)
            if mod != 0:
                score += mod
                details.append(f"Sector: {reason}")

        # Rounding
        return score, details, round_to_tick(orb_high), round_to_tick(orb_low), round_to_tick(entry), round_to_tick(sl), round_to_tick(target), signal_side

    except Exception as e:
        return 0, [f"Error: {e}"], 0, 0, 0, 0, 0, "NEUTRAL"
