import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
from src.intraday_strategy import WATCHLIST, calculate_confidence

st.set_page_config(page_title="Intraday Analysis", layout="wide")
st.title("Intraday Confidence Score")

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

# --- CALCULATION BUTTON ---
if st.button("Calculate Scores"):
    results = []
    progress_bar = st.progress(0)
    
    total_stocks = len(WATCHLIST)
    for i, stock in enumerate(WATCHLIST):
        with st.spinner(f"Analyzing {stock}..."):
            score, details, pdh, pdl, prev_close, todays_high, exit_price, atr, trigger_high, vwap = calculate_confidence(stock)
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
                     "Time to Enter": "09:45 AM",
                     "ATR": atr,
                     "TriggerHigh": trigger_high,
                     "VWAP": vwap
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
        st.dataframe(df_display.style.format({
            "Score": "{:.0f}",
            "PDH": "{:.2f}",
            "PDL": "{:.2f}",
            "Prev Close": "{:.2f}",
            "Safe Entry": "{:.2f}",
            "Exit Price": "{:.2f}"
        }).background_gradient(subset=["Score"], cmap="RdYlGn", vmin=0, vmax=100))

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
                    strategy_type="Intraday", 
                    signal_date=date_str
                )
                if success: count += 1
            
            if count > 0:
                st.success(f"Successfully added {count} trades to Live Tracker for {date_str}!")
            else:
                st.warning(f"No new unique trades to add for {date_str}.")
        
        st.caption(f"Note: Trades will be tracked for the session on {selected_date.strftime('%Y-%m-%d')}.")
