import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# List of liquid stocks for MTF (Top Nifty 50 + Midcaps)
# List of liquid stocks for MTF (Consolidated High Liquidity + Momentum)
from src.config import WATCHLIST

def get_ultra_precision_signal(ticker_symbol, nifty_df=None):
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
        
    from src.utils import fetch_data_robust

    def get_data(symbol):
        return fetch_data_robust(symbol, period="1y", interval="1d")

    stock_df = get_data(ticker_symbol)
    if stock_df is None or stock_df.empty or len(stock_df) < 50: 
        return None

    # Align with Nifty for Relative Strength
    rs_score = 0
    bg_color = "neutral"
    
    if nifty_df is not None and not nifty_df.empty:
        # Align dates
        common_idx = stock_df.index.intersection(nifty_df.index)
        if len(common_idx) > 20:
            s_aligned = stock_df.loc[common_idx]
            n_aligned = nifty_df.loc[common_idx]
            
            # Metric: 20-Day Performance Comparison
            s_ret = (s_aligned['Close'].iloc[-1] / s_aligned['Close'].iloc[-20]) - 1
            n_ret = (n_aligned['Close'].iloc[-1] / n_aligned['Close'].iloc[-20]) - 1
            
            rs_val = (s_ret - n_ret) * 100 # Alpha in %
            rs_score = rs_val
    
    # --- 1. Technical Indicator Calculations ---
    # EMA Alignment (Trend)
    stock_df['EMA20'] = stock_df['Close'].ewm(span=20, adjust=False).mean()
    stock_df['EMA50'] = stock_df['Close'].ewm(span=50, adjust=False).mean()
    
    # RSI (Momentum)
    delta = stock_df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    stock_df['RSI'] = 100 - (100 / (1 + (gain / loss.replace(0, np.nan))))

    # ADX (High-Precision Wilder's Smoothing)
    tr1 = stock_df['High'] - stock_df['Low']
    tr2 = abs(stock_df['High'] - stock_df['Close'].shift(1))
    tr3 = abs(stock_df['Low'] - stock_df['Close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean() # Smoothed ATR
    
    up_move = stock_df['High'].diff()
    down_move = stock_df['Low'].shift(1) - stock_df['Low']
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    plus_di = 100 * (pd.Series(plus_dm, index=stock_df.index).ewm(alpha=1/14, adjust=False).mean() / atr)
    minus_di = 100 * (pd.Series(minus_dm, index=stock_df.index).ewm(alpha=1/14, adjust=False).mean() / atr)
    
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan))
    stock_df['ADX'] = dx.ewm(alpha=1/14, adjust=False).mean().fillna(0)

    # VPT (Volume Price Trend)
    vpt = (stock_df['Volume'] * stock_df['Close'].pct_change()).cumsum()

    # --- 2. Confidence Scoring Logic ---
    latest = stock_df.iloc[-1]
    score = 0
    reasons = []

    # EMA Alignment (30%)
    if latest['Close'] > latest['EMA20'] > latest['EMA50']:
        score += 30
        reasons.append("Bullish Trend: Price > EMA20 > EMA50")
    elif latest['Close'] > latest['EMA20']:
        score += 15
        reasons.append("Short-term Trend: Price > EMA20")

    # RSI Momentum (20%)
    if 50 <= latest['RSI'] <= 65:
        score += 20
        reasons.append(f"Ideal Momentum: RSI at {round(latest['RSI'],1)}")
    elif 65 < latest['RSI'] <= 75:
        score += 10
        reasons.append("Strong Momentum: RSI Over 65")

    # ADX Strength (20%)
    if latest['ADX'] > 25:
        score += 20
        reasons.append(f"Strong Trend: ADX at {round(latest['ADX'],1)}")

    # Volume Confirmation (15%)
    if len(vpt) > 5 and vpt.iloc[-1] > vpt.tail(5).mean():
        score += 15
        reasons.append("Institutional Flow: VPT rising")

    # ALPHA / Relative Strength (15%) - NEW!
    if rs_score > 0:
        score += 15
        reasons.append(f"Alpha Leader: Outperforming Nifty by {rs_score:.1f}%")

    # --- 3. Dynamic Levels & Time Estimation ---
    latest_price = latest['Close']
    atr_val = atr.iloc[-1]
    
    # Define Entry Point
    ema20_val = latest['EMA20']
    if latest_price > ema20_val * 1.02: 
        entry_point = ema20_val * 1.01  
        entry_type = "LIMIT (Pullback)"
    else:
        entry_point = latest_price
        entry_type = "MARKET"

    stop_loss = entry_point - (1.5 * atr_val)
    target_price = entry_point + (3.0 * atr_val)
    
    recent_diffs = stock_df['Close'].diff().tail(20)
    avg_up = recent_diffs[recent_diffs > 0].mean()
    velocity = avg_up if pd.notnull(avg_up) and avg_up > 0 else (atr_val * 0.5)
    est_days = round((target_price - entry_point) / velocity) if velocity > 0 else 7

    fund_rating = "⚠️ Neutral"
    if roe is not None and op_margin is not None:
        is_quality = roe > 0.15 and op_margin > 0.10
        if is_quality:
            fund_rating = "💎 Premium" if (pe_ratio and pe_ratio > 60) else "✅ Strong"
        elif roe < 0 or op_margin < 0:
            fund_rating = "❌ Weak"
        else:
            fund_rating = "⚠️ Moderate"

    return {
        "Ticker": ticker_symbol,
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Industry": industry,
        "Signal": "STRONG BUY" if score >= 80 else "BUY" if score >= 60 else "WATCH",
        "Confidence Score": score,
        "Raw Score": score,
        "RS_Score": round(rs_score, 2), # NEW
        "Current Price": round(latest_price, 2),
        "Entry Price": round(entry_point, 2),
        "Stop Loss": round(stop_loss, 2),
        "Target Price": round(target_price, 2),
        "Est. Days": f"{max(1, int(est_days))}-{max(1, int(est_days+3))} Days",
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
    
    # 1. regime Filter: Nifty 50
    from src.utils import fetch_data_robust
    nifty = fetch_data_robust("^NSEI", period="1y", interval="1d")
    
    market_status = "NEUTRAL"
    if nifty is not None and not nifty.empty:
        nifty_ema50 = nifty['Close'].ewm(span=50, adjust=False).mean().iloc[-1]
        cur_nifty = nifty['Close'].iloc[-1]
        
        market_bullish = cur_nifty > nifty_ema50
        market_status = "BULLISH" if market_bullish else "BEARISH (Caution)"
    else:
         # Fallback if Nifty fails
         market_bullish = True 
         cur_nifty = 0
         nifty_ema50 = 0
    
    warnings = []
    if not market_bullish:
        warnings.append(f"⚠️ **Market Regime Filter Active**: Nifty ({int(cur_nifty)}) < EMA50 ({int(nifty_ema50)}). Buying power reduced.")

    total_stocks = len(WATCHLIST)
    valid_signals = []
    
    for i, ticker in enumerate(WATCHLIST):
        if progress_callback:
            progress_callback(i / total_stocks, f"Scanning {ticker}...")
            
        try:
            # Pass Nifty DF for RS calculation
            analysis = get_ultra_precision_signal(ticker, nifty_df=nifty) 
            if not analysis: continue
            
            # REGIME FILTER:
            # If Market Bearish, ONLY allow Super-High Confidence (90+) + High Alpha
            if not market_bullish:
                if analysis['Confidence Score'] < 90 or analysis['RS_Score'] < 0:
                     analysis['Confidence Score'] = 0 # Suppress signal
                     analysis['Signal'] = "SUPPRESSED (Market Regime)"
            
            results.append(analysis)
            
            if analysis["Signal"] in ["BUY", "STRONG BUY"] and analysis["Confidence Score"] >= 80:
                valid_signals.append(analysis)
                
        except Exception as e:
            print(f"Error scanning {ticker}: {e}")
            continue

    if valid_signals:
        try:
            from .notifications import send_summary_email # Relative import fix
            send_summary_email(valid_signals)
        except:
             pass 
            
    return results, warnings
            
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
