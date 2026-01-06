import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
from src.intraday_strategy import calculate_confidence
from src.orb_strategy import calculate_orb_signal
from src.config import WATCHLIST
from src.ui import add_logo

st.set_page_config(page_title="Intraday Analysis", layout="wide")
add_logo()
st.title("Intraday Confidence Score")
st.markdown("""
### ⚡ Sniper Intraday Scanner
**Capture the Day's Move.** This tool scans the market for high-probability day trading setups using a 9-point confluence model.
- **🎯 Strategy:** Gap Logic + RSI + VWAP + Trend Alignment.
- **🕒 Best Time:** Run this scanning before market open (09:00 AM) or continuously during the session.
- **🚀 Goal:** Identify stocks poised for explosive intraday momentum with clearly defined entries and exits.
""")

# --- INITIALIZATION ---
if "intraday_results" not in st.session_state:
    st.session_state.intraday_results = None

import pytz

# --- SMART DATE LOGIC ---
ist = pytz.timezone('Asia/Kolkata')
now = datetime.now(ist)
target_date = now
session_label = "Today's Session"

if now.time() > time(15, 30):
    # Market Closed: Default to Next Day
    target_date = now + timedelta(days=1)
    # If default is Sat(5) or Sun(6), skip to Monday
    while target_date.weekday() >= 5:
        target_date += timedelta(days=1)
    session_label = f"Next Session ({target_date.strftime('%Y-%m-%d')})"

selected_date = target_date  # Used for add_trade

# Display current plan mode
st.info(f"📅 Strategy Mode: **{session_label}**")

# Strategy Selection
strategy_mode = st.radio("Select Strategy:", ["Sniper Trend (Default)", "ORB Breakout (09:15-09:45)"], horizontal=True)

# --- CALCULATION BUTTON ---
if st.button("Calculate Scores"):
    results = []
    progress_bar = st.progress(0)
    
    total_stocks = len(WATCHLIST)
    for i, stock in enumerate(WATCHLIST):
        with st.spinner(f"Analyzing {stock}..."):
            
            if "Sniper" in strategy_mode:
                score, details, pdh, pdl, prev_close, todays_high, exit_price, atr, trigger_high, vwap, side = calculate_confidence(stock)
                
                if isinstance(details, str) and details.startswith("Error"):
                     pass 
                else:
                     results.append({
                         "Ticker": stock, 
                         "Side": side,
                         "Score": score, 
                         "Details": ", ".join(details),
                         "Entry": todays_high,
                         "Stop Loss": prev_close, # or pdl based on logic
                         "Target": exit_price,
                         "ATR": atr,
                         "TriggerHigh": trigger_high,
                         "VWAP": vwap
                     })
            else:
                 # ORB STRATEGY
                 score, details, orb_h, orb_l, entry, sl, target, side = calculate_orb_signal(stock)
                 
                 if score > 0:
                     results.append({
                         "Ticker": stock,
                         "Side": side,
                         "Score": score,
                         "Details": ", ".join(details),
                         "Entry": entry,
                         "Stop Loss": sl,
                         "Target": target,
                         "ORB High": orb_h,
                         "ORB Low": orb_l
                     })
                     
        progress_bar.progress((i + 1) / total_stocks)
        
    df_results = pd.DataFrame(results)
    
    # Filter for high score
    if not df_results.empty:
        df_results = df_results[df_results['Score'] >= 90]
        st.session_state.intraday_results = df_results
    else:
        st.session_state.intraday_results = pd.DataFrame() # Empty results

# --- RESULTS DISPLAY ---
if st.session_state.intraday_results is not None:
    df_display = st.session_state.intraday_results
    
    st.subheader("Analysis Results")
    if df_display.empty:
        st.info("No stocks matched the 90+ score criteria.")
    else:

        # Color code Side
        def color_side(val):
            color = 'green' if val == 'BUY' else 'red' if val == 'SELL' else 'gray'
            return f'color: {color}; font-weight: bold'

        if "Sniper" in strategy_mode:
             st.dataframe(df_display.style.format({
                "Score": "{:.0f}",
                "Entry": "{:.2f}",
                "Stop Loss": "{:.2f}",
                "Target": "{:.2f}"
            }).map(color_side, subset=['Side'])
              .background_gradient(subset=["Score"], cmap="RdYlGn", vmin=0, vmax=100))
        else:
             st.dataframe(df_display.style.format({
                "Score": "{:.0f}",
                "Entry": "{:.2f}",
                "Stop Loss": "{:.2f}",
                "Target": "{:.2f}",
                "ORB High": "{:.2f}",
                "ORB Low": "{:.2f}"
            }).map(color_side, subset=['Side'])
              .background_gradient(subset=["Score"], cmap="RdYlGn", vmin=0, vmax=100))

        # --- ADD TO TRACKER ---
        st.markdown("---")
        from src.tracker import TradeTracker
        
        if st.button("💾 Add Intraday Signals to Live Tracker"):
            tracker = TradeTracker()
            count = 0
            date_str = selected_date.strftime("%Y-%m-%d")
            
            for index, row in df_display.iterrows():
                # Convert row to dict for add_trade
                row_dict = row.to_dict()
                success, msg = tracker.add_trade(
                    row_dict, 
                    strategy_type="Intraday (ORB)" if "ORB" in strategy_mode else "Intraday (Sniper)", 
                    signal_date=date_str
                )
                if success: count += 1
            
            if count > 0:
                st.success(f"Successfully added {count} trades to Live Tracker for {date_str}!")
            else:
                st.warning(f"No new unique trades to add for {date_str}.")
        
        st.caption(f"Note: Trades will be tracked for the session on {selected_date.strftime('%Y-%m-%d')}.")
