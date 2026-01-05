import streamlit as st
import yfinance as yf
import pandas as pd
import ta
from ta.trend import EMAIndicator, MACD
from ta.volume import VolumeWeightedAveragePrice
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

st.set_page_config(page_title="Intraday Analysis", layout="wide")
st.title("Intraday Confidence Score")

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
        
        if df.empty or df_daily.empty: return 0, "No Data", 0, 0, 0, 0, 0

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
        
        # Safe Target: 0.5%
        exit_price = todays_high * 1.005

        return score, details, prev_day_high, pdl, prev_close, todays_high, exit_price
    except Exception as e:
        return 0, f"Error: {e}", 0, 0, 0, 0, 0

# --- EXECUTION ---
nifty_top_10 = [
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

if "intraday_results" not in st.session_state:
    st.session_state.intraday_results = None

if st.button("Calculate Scores"):
    results = []
    progress_bar = st.progress(0)
    
    for i, stock in enumerate(nifty_top_10):
        with st.spinner(f"Analyzing {stock}..."):
            score, details, pdh, pdl, prev_close, todays_high, exit_price = calculate_confidence(stock)
            if isinstance(details, str) and details.startswith("Error"):
                 pass # Skip errors in simplified results
            else:
                 results.append({
                     "Ticker": stock, 
                     "Score": score, 
                     "Details": ", ".join(details),
                     "PDH": pdh,
                     "PDL": pdl,
                     "Prev Close": prev_close,
                     "Safe Entry": todays_high,
                     "Exit Price": exit_price,
                     "Target %": "0.5%",
                     "Time to Enter": "09:30 AM"
                 })
        progress_bar.progress((i + 1) / len(nifty_top_10))
        
    df_results = pd.DataFrame(results)
    if not df_results.empty:
        df_results = df_results[df_results['Score'] >= 90]
        st.session_state.intraday_results = df_results
    else:
        st.session_state.intraday_results = pd.DataFrame() # Empty

if st.session_state.intraday_results is not None:
    df_display = st.session_state.intraday_results
    
    st.subheader("Analysis Results")
    if df_display.empty:
        st.info("No stocks matched the 90+ score criteria.")
    else:
        st.dataframe(df_display.style.format({
            "Score": "{:.0f}",
            "PDH": "{:.2f}",
            "PDL": "{:.2f}",
            "Prev Close": "{:.2f}",
            "Safe Entry": "{:.2f}",
            "Exit Price": "{:.2f}"
        }).background_gradient(subset=["Score"], cmap="RdYlGn", vmin=0, vmax=100))

        # Add to Tracker Button
        st.markdown("---")
        from src.tracker import TradeTracker
        if st.button("💾 Add Intraday Signals to Live Tracker"):
            tracker = TradeTracker()
            count = 0
            for index, row in df_display.iterrows():
                # Convert row to dict for add_trade
                row_dict = row.to_dict()
                success, msg = tracker.add_trade(row_dict, strategy_type="Intraday")
                if success: count += 1
            
            if count > 0:
                st.success(f"Successfully added {count} trades to Live Tracker!")
            else:
                st.warning("No new unique trades to add.")
