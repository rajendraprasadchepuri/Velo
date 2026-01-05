"""
Live_Performance.py

Streamlit page for displaying real-time trade performance.
Features:
- Dashboard stats (Win Rate, Open Positions, Avg PnL).
- Interactive Trade Log table with formatted columns.
- Manual "Refresh" button to trigger `TradeTracker.update_status()`.
- Separate tabs for MTF (Swing) and Intraday strategies.
"""
import streamlit as st
import pandas as pd
from src.ui import add_logo
from src.tracker import TradeTracker

st.set_page_config(page_title="Live Performance", layout="wide")
add_logo()

st.title("📊 Live Strategy Performance")

tracker = TradeTracker()

# Actions
col_actions, col_space = st.columns([1, 4])
if col_actions.button("↻ Refresh Trade Status"):
    with st.spinner("Fetching latest market data..."):
        count = tracker.update_status()
    st.success(f"Updated {count} trades.")
    st.rerun()

# Display Stats
df = tracker.load_trades()

if df.empty:
    st.info("No trades tracked yet. Go to 'MTF Strategy' and add some signals!")
else:
    # Key Metrics
    total_trades = len(df)
    closed_trades = df[df['Status'].isin(['TARGET_HIT', 'STOP_LOSS_HIT'])]
    open_trades = df[df['Status'] == 'OPEN']
    
    wins = len(closed_trades[closed_trades['Status'] == 'TARGET_HIT'])
    losses = len(closed_trades[closed_trades['Status'] == 'STOP_LOSS_HIT'])
    win_rate = (wins / len(closed_trades) * 100) if len(closed_trades) > 0 else 0
    avg_pnl = closed_trades['PnL'].mean() if not closed_trades.empty else 0
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Trades", total_trades)
    m2.metric("Open Position", len(open_trades))
    m3.metric("Win Rate", f"{win_rate:.1f}%")
    m4.metric("Avg PnL (Closed)", f"{avg_pnl:.2f}%", delta_color="normal")
    
    st.markdown("---")
    st.subheader("Trade Log")
    
    # Styling Status
    def color_status(val):
        color = 'grey'
        if val == 'TARGET_HIT': color = 'green'
        elif val == 'STOP_LOSS_HIT': color = 'red'
        elif val == 'OPEN': color = 'blue'
        elif val == 'WAITING_ENTRY': color = 'orange'
        elif val == 'NOT_TRIGGERED': color = 'grey'
        elif val == 'EXIT_AT_CLOSE': color = 'purple'
        return f'color: {color}; font-weight: bold'

    tab1, tab2 = st.tabs(["MTF Strategy", "Intraday Strategy"])

    with tab1:
        st.caption("MTF Swing Trades")
        df_mtf = df[df['Strategy'] == 'MTF'] if 'Strategy' in df.columns else df
        st.dataframe(
            df_mtf,
            use_container_width=True,
            column_config={
                "TradeID": "ID",
                "Ticker": "Symbol",
                "SignalDate": "Date",
                "EntryPrice": st.column_config.NumberColumn("Entry", format="₹%.2f"),
                "StopLoss": st.column_config.NumberColumn("SL", format="₹%.2f"),
                "TargetPrice": st.column_config.NumberColumn("Target", format="₹%.2f"),
                "ExitPrice": st.column_config.NumberColumn("Exit Price", format="₹%.2f"),
                "PnL": st.column_config.NumberColumn("PnL %", format="%.2f%%"),
                "Strategy": None, # Hide strategy column as it's redundant here
                "UpdatedStopLoss": None,
                "ATR": None,
                "TriggerHigh": None,
                "VWAP": None,
                "InitialSL": None
            }
        )

    with tab2:
        st.caption("Intraday Trades")
        df_intra = df[df['Strategy'] == 'Intraday'] if 'Strategy' in df.columns else pd.DataFrame()
        
        if not df_intra.empty:
            # Format Time Columns to show only Time (HH:MM:SS) if they exist
            if 'EntryDate' in df_intra.columns:
                df_intra['EntryDate'] = pd.to_datetime(df_intra['EntryDate'], errors='coerce').dt.strftime('%H:%M:%S')
            
            if 'ExitDate' in df_intra.columns:
                 # Only format if it's not None
                 # We need to handle mixed types (None and strings)
                 df_intra['ExitDate'] = pd.to_datetime(df_intra['ExitDate'], errors='coerce').dt.strftime('%H:%M:%S')
            
            # Recalculate PnL for display if ExitPrice exists
            # This ensures consistency even if CSV had rounding diffs
            # Note: We use apply to handle row-wise calculation safely
            def calc_pnl(row):
                if pd.notnull(row['ExitPrice']) and row['ExitPrice'] > 0 and pd.notnull(row['EntryPrice']) and row['EntryPrice'] > 0:
                    return (row['ExitPrice'] - row['EntryPrice']) / row['EntryPrice'] * 100
                return row['PnL']
            
            if 'ExitPrice' in df_intra.columns and 'EntryPrice' in df_intra.columns:
                df_intra['PnL'] = df_intra.apply(calc_pnl, axis=1)
            # Calculate % Differences for Display
            if 'EntryPrice' in df_intra.columns and 'StopLoss' in df_intra.columns:
                df_intra['SL %'] = ((df_intra['EntryPrice'] - df_intra['StopLoss']).abs() / df_intra['EntryPrice']) * 100
            
            if 'EntryPrice' in df_intra.columns and 'TargetPrice' in df_intra.columns:
                df_intra['Target %'] = ((df_intra['TargetPrice'] - df_intra['EntryPrice']).abs() / df_intra['EntryPrice']) * 100

            # Calculate Risk and Rec Qty
            if 'EntryPrice' in df_intra.columns and 'StopLoss' in df_intra.columns:
                 # Risk Per Share
                 df_intra['Risk'] = (df_intra['EntryPrice'] - df_intra['StopLoss']).abs()
                 
                 # Recommended Quantity for 1 Lakh Capital (1% Risk = 1000 INR)
                 # Qty = 1000 / Risk Per Share
                 def calc_qty(risk):
                     if risk > 0:
                         return int(1000 / risk)
                     return 0
                 
                 df_intra['Qty (1L)'] = df_intra['Risk'].apply(calc_qty)

        st.dataframe(
            df_intra,
            use_container_width=True,
            column_order=["Status", "SignalDate", "Ticker", "EntryDate", "EntryPrice", "StopLoss", "SL %", "Risk", "Qty (1L)", "UpdatedStopLoss", "TargetPrice", "Target %", "ExitPrice", "ExitDate", "PnL", "Notes"],
            column_config={
                "TradeID": "ID",
                "Ticker": "Symbol",
                "SignalDate": "Date",
                "EntryDate": "Entry Time",
                "EntryPrice": st.column_config.NumberColumn("Entry", format="₹%.2f"),
                "StopLoss": st.column_config.NumberColumn("SL", format="₹%.2f"),
                "SL %": st.column_config.NumberColumn("SL %", format="%.2f%%"),
                "Risk": st.column_config.NumberColumn("Risk/Share", format="₹%.2f"),
                "Qty (1L)": st.column_config.NumberColumn("Qty (1L Cap)", format="%d"),
                "UpdatedStopLoss": st.column_config.NumberColumn("Updated SL", format="₹%.2f"),
                "TargetPrice": st.column_config.NumberColumn("Target", format="₹%.2f"),
                "Target %": st.column_config.NumberColumn("Tgt %", format="%.2f%%"),
                "ExitPrice": st.column_config.NumberColumn("Exit Price", format="₹%.2f"),
                "ExitDate": "Exit Time",
                "PnL": st.column_config.NumberColumn("PnL %", format="%.2f%%"),
                "Strategy": None
            }
        )
