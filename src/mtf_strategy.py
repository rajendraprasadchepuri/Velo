import yfinance as yf
import pandas as pd
import numpy as np

# List of liquid stocks for MTF (Top Nifty 50 + Midcaps)
WATCHLIST = [
    # NIFTY 50
    "ADANIENT.NS","ADANIPORTS.NS","APOLLOHOSP.NS","ASIANPAINT.NS","AXISBANK.NS",
    "BAJAJ-AUTO.NS","BAJFINANCE.NS","BAJAJFINSV.NS","BHARTIARTL.NS","BPCL.NS",
    "BRITANNIA.NS","CIPLA.NS","COALINDIA.NS","DIVISLAB.NS","DRREDDY.NS",
    "EICHERMOT.NS","GRASIM.NS","HCLTECH.NS","HDFCBANK.NS","HDFCLIFE.NS",
    "HEROMOTOCO.NS","HINDALCO.NS","HINDUNILVR.NS","ICICIBANK.NS","INDUSINDBK.NS",
    "INFY.NS","ITC.NS","JSWSTEEL.NS","KOTAKBANK.NS","LT.NS","M&M.NS",
    "MARUTI.NS","NESTLEIND.NS","NTPC.NS","ONGC.NS","POWERGRID.NS",
    "RELIANCE.NS","SBILIFE.NS","SBIN.NS","SUNPHARMA.NS","TATACONSUM.NS",
    "TATAMOTORS.NS","TATASTEEL.NS","TCS.NS","TECHM.NS","TITAN.NS",
    "ULTRACEMCO.NS","UPL.NS","WIPRO.NS",

    # NIFTY MIDCAP 50
    "ABCAPITAL.NS","ASHOKLEY.NS","ASTRAL.NS","AUROPHARMA.NS","BHEL.NS",
    "BHARATFORG.NS","BIOCON.NS","CANFINHOME.NS","CHOLAFIN.NS","COFORGE.NS",
    "CONCOR.NS","CUMMINSIND.NS","DIXON.NS","FEDERALBNK.NS","GODREJPROP.NS",
    "HDFCAMC.NS","HINDPETRO.NS","IDFCFIRSTB.NS","IGL.NS","INDUSTOWER.NS",
    "JINDALSTEL.NS","LTTS.NS","LUPIN.NS","MARICO.NS","MINDTREE.NS",
    "MOTHERSON.NS","MPHASIS.NS","MRF.NS","MUTHOOTFIN.NS","NAM-INDIA.NS",
    "OBEROIRLTY.NS","PAGEIND.NS","PEL.NS","PERSISTENT.NS","POLYCAB.NS",
    "SAIL.NS","SBICARD.NS","SRF.NS","SUNTV.NS","TATACHEM.NS",
    "TATAPOWER.NS","TORNTPHARM.NS","TVSMOTOR.NS","UBL.NS","VOLTAS.NS",
    "WHIRLPOOL.NS","ZEEL.NS"
]

def get_ultra_precision_signal(ticker_symbol):
    # 1. Map the stock to its sector index (Focusing on Indian Markets)
    # Most MTF trades are in Bank or Nifty 50 stocks
    try:
        ticker = yf.Ticker(ticker_symbol)
        ticker_info = ticker.info
    except Exception:
        ticker_info = {}
        
    sector = ticker_info.get('sector', 'Unknown')
    
    # Define broad index (Nifty 50) and sector index (Bank Nifty as default for banks)
    market_index = "^NSEI"  # Nifty 50
    sector_index = "^NSEBANK" if "Bank" in ticker_info.get('industry', '') else "^NSEI"

    # 2. Fetch Data for Stock, Sector, and Market
    def get_data(symbol):
        df = yf.download(symbol, period="6mo", interval="1d", auto_adjust=True, progress=False)
        if df.empty: return df
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df

    stock_df = get_data(ticker_symbol)
    if stock_df.empty:
        return None

    sector_df = get_data(sector_index)
    market_df = get_data(market_index)

    # 3. Guardrail Logic (The 'Anti-Error' Filters)
    def is_bullish(df):
        if df is None or df.empty: return False
        ema20 = df['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
        return df['Close'].iloc[-1] > ema20

    market_support = is_bullish(market_df)
    sector_support = is_bullish(sector_df)
    
    # 4. Correlation Check (Does this stock move with the index?)
    correlation = 0
    if not market_df.empty and len(stock_df) > 1 and len(market_df) > 1:
        # Align dates
        aligned_stock = stock_df['Close'].pct_change()
        aligned_market = market_df['Close'].pct_change()
        correlation = aligned_stock.corr(aligned_market)

    # 5. Advanced Technical Scoring for the Stock
    score = 0
    reasons = []

    # Market & Sector Alignment (Crucial for Low Error)
    if market_support: 
        score += 20
        reasons.append("Market Guardrail: Nifty 50 is Bullish")
    if sector_support: 
        score += 20
        reasons.append(f"Sector Guardrail: {sector_index} is Bullish")
    
    # Stock Momentum (RSI + EMA)
    stock_ema20 = stock_df['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
    if stock_df['Close'].iloc[-1] > stock_ema20:
        score += 30
        reasons.append("Stock Trend: Above EMA20")

    # Volume Confirmation (VPT)
    vpt = (stock_df['Volume'] * stock_df['Close'].pct_change()).cumsum()
    if len(vpt) >= 2 and vpt.iloc[-1] > vpt.iloc[-2]:
        score += 30
        reasons.append("Money Flow: Institutional Buying (VPT Up)")

    # 6. Final Calculation
    latest_price = stock_df['Close'].iloc[-1]
    confidence = score
    
    signal = ""
    # Accuracy logic: If market is bearish, cap confidence at 50%
    if not market_support:
        confidence = min(confidence, 40)
        signal = "AVOID (Market Weakness)"
    else:
        signal = "STRONG BUY" if confidence >= 80 else "WATCH"

    return {
        "Ticker": ticker_symbol,
        "Signal": signal,
        "Confidence Score": f"{confidence}%",
        "Raw Score": confidence,
        "Market Correlation": round(correlation, 2),
        "Reasons": ", ".join(reasons),
        "Current Price": round(latest_price, 2)
    }

def run_pro_scanner(progress_callback=None):
    results = []
    
    # 1. Check Global Market Guardrail (Nifty 50)
    nifty = yf.download("^NSEI", period="1mo", interval="1d", progress=False)
    if isinstance(nifty.columns, pd.MultiIndex): nifty.columns = nifty.columns.get_level_values(0)
    
    market_bullish = False
    if not nifty.empty:
        market_bullish = nifty['Close'].iloc[-1] > nifty['Close'].ewm(span=20).mean().iloc[-1]
    
    warnings = []
    if not market_bullish:
        warnings.append("⚠️ Warning: Nifty 50 is below 20-EMA. Scanner will be extra strict.")

    total_stocks = len(WATCHLIST)
    for i, ticker in enumerate(WATCHLIST):
        if progress_callback:
            progress_callback(i / total_stocks, f"Scanning {ticker}...")
            
        try:
            # Reusing our high-precision logic
            analysis = get_ultra_precision_signal(ticker) 
            if not analysis: continue
            
            score = analysis['Raw Score']
            
            # Return all analysis so UI can filter
            results.append(analysis)
                
        except Exception as e:
            print(f"Error scanning {ticker}: {e}")
            continue
            
    return results, warnings

def run_strategy_backtest(ticker_symbol, sector_index="^NSEBANK", years=1):
    # 1. Fetch Data for Stock and Sector
    start_date = (pd.Timestamp.now() - pd.DateOffset(years=years)).strftime('%Y-%m-%d')
    stock_df = yf.download(ticker_symbol, start=start_date, interval="1d", auto_adjust=True, progress=False)
    sector_df = yf.download(sector_index, start=start_date, interval="1d", auto_adjust=True, progress=False)
    
    # Flatten multi-index columns if they exist
    if isinstance(stock_df.columns, pd.MultiIndex): stock_df.columns = stock_df.columns.get_level_values(0)
    if isinstance(sector_df.columns, pd.MultiIndex): sector_df.columns = sector_df.columns.get_level_values(0)

    if stock_df.empty or sector_df.empty:
        return {"Error": "No data found"}

    # 2. Technical Indicators
    # Trend
    stock_df['EMA20'] = stock_df['Close'].ewm(span=20, adjust=False).mean()
    sector_df['EMA20'] = sector_df['Close'].ewm(span=20, adjust=False).mean()
    
    # Volume Price Trend (VPT)
    stock_df['VPT'] = (stock_df['Volume'] * stock_df['Close'].pct_change()).cumsum()
    
    # RSI
    delta = stock_df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    stock_df['RSI'] = 100 - (100 / (1 + (gain / loss)))

    # Align Sector Data
    # We need to ensure indices match for vector operations, simpler is to just reindex or use common index
    # For simplicity assuming trading days match mostly or using what we have
    common_index = stock_df.index.intersection(sector_df.index)
    stock_df = stock_df.loc[common_index]
    sector_df = sector_df.loc[common_index]
    
    # 3. Strategy Signals (The 4 Pillars)
    # Alignment: Stock > EMA and Sector > EMA and VPT rising and RSI in zone
    stock_df['Signal'] = np.where(
        (stock_df['Close'] > stock_df['EMA20']) & 
        (sector_df['Close'] > sector_df['EMA20']) & 
        (stock_df['VPT'] > stock_df['VPT'].shift(1)) &
        (stock_df['RSI'] > 50),
        1, 0
    )

    # 4. Calculate MTF Net Returns
    daily_returns = stock_df['Close'].pct_change()
    
    # Leveraged Returns (4x)
    leverage = 4
    daily_mtf_interest = 0.0004  # 0.04% per day on the borrowed 75%
    borrowed_capital_weight = 0.75
    
    # Strategy Return = (Daily Return * 4) - (Daily Interest * 0.75)
    stock_df['Strategy_Return'] = (daily_returns * leverage) - (daily_mtf_interest * borrowed_capital_weight)
    
    # Only apply returns when Signal is active (using shift to avoid look-ahead bias)
    # Signal calculated at close of day T is for trade on day T+1
    stock_df['Actual_Returns'] = stock_df['Strategy_Return'] * stock_df['Signal'].shift(1)
    
    # Calculate Cumulative Growth
    stock_df['Portfolio_Value'] = (1 + stock_df['Actual_Returns'].fillna(0)).cumprod()
    stock_df['Market_Value'] = (1 + daily_returns.fillna(0)).cumprod()

    # 5. Performance Metrics
    if stock_df.empty: return {"Error": "Not enough data"}
    
    total_return = (stock_df['Portfolio_Value'].iloc[-1] - 1) * 100
    market_return = (stock_df['Market_Value'].iloc[-1] - 1) * 100
    
    # Max Drawdown
    cum_max = stock_df['Portfolio_Value'].cummax()
    drawdown = stock_df['Portfolio_Value'] / cum_max - 1
    max_drawdown = drawdown.min() * 100
    
    win_days = len(stock_df[stock_df['Actual_Returns'] > 0])
    total_trade_days = len(stock_df[stock_df['Signal'] == 1])

    return {
        "Ticker": ticker_symbol,
        "Total Return (MTF)": f"{round(total_return, 2)}%",
        "Buy & Hold Return": f"{round(market_return, 2)}%",
        "Max Drawdown": f"{round(max_drawdown, 2)}%",
        "Trade Opportunity Days": total_trade_days,
        "Daily Win Rate": f"{round((win_days/total_trade_days)*100, 2)}%" if total_trade_days > 0 else "0%"
    }
