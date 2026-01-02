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
"""WATCHLIST = [
    # NIFTY 50
    "ADANIENT.NS","ADANIPORTS.NS","APOLLOHOSP.NS","ASIANPAINT.NS","AXISBANK.NS",
    "BAJAJ-AUTO.NS"]
"""
def get_ultra_precision_signal(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        ticker_info = ticker.info
        industry = ticker_info.get('industry', 'N/A')
        
        # Fundamentals
        market_cap = ticker_info.get('marketCap')
        pe_ratio = ticker_info.get('trailingPE')
        pb_ratio = ticker_info.get('priceToBook')
        roe = ticker_info.get('returnOnEquity')
        div_yield = ticker_info.get('dividendYield')
        op_margin = ticker_info.get('operatingMargins')
    except Exception:
        ticker_info = {}
        industry = "N/A"
        market_cap = pe_ratio = pb_ratio = roe = div_yield = op_margin = None
        
    def get_data(symbol):
        df = yf.download(symbol, period="1y", interval="1d", auto_adjust=True, progress=False)
        if df.empty: return df
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df

    stock_df = get_data(ticker_symbol)
    if stock_df is None or stock_df.empty: return None

    # 1. Indicator Calculations
    stock_df['EMA20'] = stock_df['Close'].ewm(span=20, adjust=False).mean()
    stock_df['EMA50'] = stock_df['Close'].ewm(span=50, adjust=False).mean()
    
    # RSI
    delta = stock_df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    stock_df['RSI'] = 100 - (100 / (1 + (gain / loss)))

    # ADX (Trend Strength)
    tr = pd.concat([stock_df['High']-stock_df['Low'], 
                    abs(stock_df['High']-stock_df['Close'].shift()), 
                    abs(stock_df['Low']-stock_df['Close'].shift())], axis=1).max(axis=1)
    atr = tr.rolling(window=14).mean()
    
    # Calculate DM values
    plus_dm = stock_df['High'].diff().where(lambda x: (x > 0) & (x > -stock_df['Low'].diff()), 0)
    minus_dm = (-stock_df['Low'].diff()).where(lambda x: (x > 0) & (x > stock_df['High'].diff()), 0)
    
    # Calculate DI values
    plus_di = 100 * (plus_dm.rolling(14).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(14).mean() / atr)
    
    # Calculate DX and ADX
    # Avoid division by zero
    di_sum = plus_di + minus_di
    dx = 100 * abs(plus_di - minus_di) / di_sum.replace(0, np.nan)
    stock_df['ADX'] = dx.rolling(window=14).mean()

    # VPT (Volume Price Trend)
    vpt = (stock_df['Volume'] * stock_df['Close'].pct_change()).cumsum()

    # 2. Advanced Confidence Logic (Weighted)
    if len(stock_df) < 50: return None # Not enough data
    
    latest = stock_df.iloc[-1]
    
    score = 0
    reasons = []

    # EMA Alignment (30% weight) - The Core Trend
    if latest['Close'] > latest['EMA20'] > latest['EMA50']:
        score += 30
        reasons.append("Bullish Trend: Price > EMA20 > EMA50")
    elif latest['Close'] > latest['EMA20']:
        score += 15
        reasons.append("Short-term Trend: Price > EMA20")

    # RSI Momentum (20% weight)
    if 50 <= latest['RSI'] <= 65:
        score += 20
        reasons.append(f"Ideal Momentum: RSI at {round(latest['RSI'],1)}")
    elif 65 < latest['RSI'] <= 75:
        score += 10
        reasons.append("Strong Momentum: RSI Over 65")

    # ADX Strength (20% weight)
    if latest.get('ADX') and latest['ADX'] > 25:
        score += 20
        reasons.append(f"Strong Trend: ADX at {round(latest['ADX'],1)}")

    # Volume Confirmation (30% weight) - Institutional Check
    if len(vpt) >= 2 and vpt.iloc[-1] > vpt.iloc[-2]:
        score += 30
        reasons.append("Institutional Flow: VPT Rising")

    # 3. Dynamic Levels & Time
    latest_price = latest['Close']
    atr_val = atr.iloc[-1]
    stop_loss = latest_price - (1.5 * atr_val)
    target_price = latest_price + (3.0 * atr_val)
    
    # Velocity Time Estimation
    recent_diffs = stock_df['Close'].diff().tail(20)
    avg_up = recent_diffs[recent_diffs > 0].mean()
    velocity = avg_up if avg_up and not np.isnan(avg_up) else (atr_val * 0.5)
    est_days = round((target_price - latest_price) / velocity) if velocity > 0 else 7

    # Fundamental Rating Logic
    fund_rating = "⚠️ Neutral"
    try:
        if roe is not None and op_margin is not None:
            # Check Quality First
            is_quality = roe > 0.15 and op_margin > 0.10
            
            if is_quality:
                # Check Valuation (P/E) if available
                if pe_ratio and pe_ratio > 60:
                    fund_rating = "💎 Premium" # Great company, expensive price
                else:
                    fund_rating = "✅ Strong"
            elif roe < 0 or op_margin < 0:
                fund_rating = "❌ Weak"
            else:
                fund_rating = "⚠️ Moderate"
    except:
        pass

    return {
        "Ticker": ticker_symbol,
        "Industry": industry,
        "Signal": "STRONG BUY" if score >= 80 else "BUY" if score >= 60 else "WATCH",
        "Confidence Score": score,
        "Raw Score": score,
        "Current Price": round(latest_price, 2),
        "Stop Loss": round(stop_loss, 2),
        "Target Price": round(target_price, 2),
        "Est. Days": f"{int(est_days)}-{int(est_days+3)} Days",
        "Reasoning": ", ".join(reasons),
        "Market Cap": market_cap,
        "P/E Ratio": pe_ratio,
        "P/B Ratio": pb_ratio,
        "ROE": roe,
        "Dividend Yield": div_yield,
        "Operating Margin": op_margin,
        "Fundamental Rating": fund_rating
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
