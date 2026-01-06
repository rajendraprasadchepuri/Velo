import yfinance as yf
from src.config import SECTOR_MAP, MARKET_INDEX

def get_sector_status(ticker):
    """
    Scientifically analyzes the parent sector of a stock.
    Returns:
        sector_name (str): e.g. "NIFTY BANK"
        change_pct (float): e.g. 1.25
        trend (str): "BULLISH", "BEARISH", or "NEUTRAL"
    """
    sector_ticker = SECTOR_MAP.get(ticker, MARKET_INDEX)
    sector_name = sector_ticker.replace("^", "").replace("CNX", "NIFTY ").replace("NSE", "NIFTY ").replace("I", "50")
    
    try:
        # Fetch Sector Data (Today)
        # We need the % change from yesterday's close
        data = yf.download(sector_ticker, period="2d", interval="1d", progress=False, auto_adjust=True)
        
        if data is None or data.empty:
            return sector_name, 0.0, "NEUTRAL"
            
        if len(data) < 2:
            # Only today's data available (maybe Monday morning?)
            # Compare Open vs Current
            row = data.iloc[-1]
            open_p = row['Open']
            current_p = row['Close']
            change = ((current_p - open_p) / open_p) * 100
        else:
            prev_close = data.iloc[-2]['Close']
            current_close = data.iloc[-1]['Close']
            change = ((current_close - prev_close) / prev_close) * 100
            
        # Determine Trend
        trend = "NEUTRAL"
        if change > 0.25: trend = "BULLISH"
        elif change < -0.25: trend = "BEARISH"
        
        return sector_name, change, trend
        
    except Exception as e:
        print(f"Sector Error ({ticker}): {e}")
        return sector_name, 0.0, "NEUTRAL"

def check_alignment(ticker, trade_side):
    """
    Returns a Score Modifier (-20 to +20) based on alignment.
    """
    name, change, trend = get_sector_status(ticker)
    
    score_mod = 0
    reason = f"Sector {name} is {trend} ({change:.2f}%)"
    
    if trade_side == "BUY":
        if trend == "BULLISH": score_mod = 20
        elif trend == "BEARISH": score_mod = -30 # Penalty for fighting trend
    elif trade_side == "SELL":
        if trend == "BEARISH": score_mod = 20
        elif trend == "BULLISH": score_mod = -30
        
    return score_mod, reason, change
