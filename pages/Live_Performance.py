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
                "Strategy": None # Hide strategy column as it's redundant here
            }
        )

    with tab2:
        st.caption("Intraday Trades")
        df_intra = df[df['Strategy'] == 'Intraday'] if 'Strategy' in df.columns else pd.DataFrame()
        st.dataframe(
            df_intra,
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
                "Strategy": None
            }
        )
