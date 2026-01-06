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
df_raw = tracker.load_trades()

# --- FILTERS ---
st.sidebar.header("🔍 Filter Trades")

# 1. Strategy Filter
strategies = df_raw['Strategy'].unique().tolist() if 'Strategy' in df_raw.columns else ['MTF', 'Intraday']
selected_strategies = st.sidebar.multiselect("Select Strategy", options=strategies, default=strategies)

# 2. Status Filter
statuses = df_raw['Status'].unique().tolist() if not df_raw.empty else []
selected_statuses = st.sidebar.multiselect("Select Status", options=statuses, default=statuses)

# 3. Date Filter
min_date = pd.to_datetime(df_raw['SignalDate']).min().date() if not df_raw.empty else pd.to_datetime('today').date()
max_date = pd.to_datetime(df_raw['SignalDate']).max().date() if not df_raw.empty else pd.to_datetime('today').date()

date_range = st.sidebar.date_input(
    "Signal Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Apply Filters
df = df_raw.copy()

if selected_strategies:
    df = df[df['Strategy'].isin(selected_strategies)]

if selected_statuses:
    df = df[df['Status'].isin(selected_statuses)]

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_d, end_d = date_range
    df['SignalDate'] = pd.to_datetime(df['SignalDate'])
    df = df[(df['SignalDate'].dt.date >= start_d) & (df['SignalDate'].dt.date <= end_d)]
    df['SignalDate'] = df['SignalDate'].dt.strftime('%Y-%m-%d')


if df.empty:
    st.info("No trades match the selected filters.")
else:
    # --- CALCULATE METRICS ---
    total_trades = len(df)
    closed_trades = df[df['Status'].isin(['TARGET_HIT', 'STOP_LOSS_HIT', 'EXIT_AT_CLOSE'])]
    open_trades = df[df['Status'] == 'OPEN']
    
    wins = closed_trades[closed_trades['PnL'] > 0]
    losses = closed_trades[closed_trades['PnL'] <= 0]
    
    num_wins = len(wins)
    num_losses = len(losses)
    
    win_rate = (num_wins / len(closed_trades) * 100) if len(closed_trades) > 0 else 0
    total_pnl = closed_trades['PnL'].sum()
    
    # Profit Factor
    gross_win = wins['PnL'].sum()
    gross_loss = abs(losses['PnL'].sum())
    profit_factor = (gross_win / gross_loss) if gross_loss > 0 else (gross_win if gross_win > 0 else 0)
    
    avg_win = wins['PnL'].mean() if not wins.empty else 0
    avg_loss = losses['PnL'].mean() if not losses.empty else 0
    
    best_trade = closed_trades['PnL'].max() if not closed_trades.empty else 0
    worst_trade = closed_trades['PnL'].min() if not closed_trades.empty else 0
    
    # --- EXPERT METRICS ---
    # Expectancy (Edge) = (Win % * Avg Win) - (Loss % * Avg Loss)
    # This is roughly equal to Avg PnL but mathematically separated
    expectancy = (win_rate/100 * avg_win) - ((1 - win_rate/100) * abs(avg_loss))
    
    # Max Drawdown
    # Sort by date to get equity curve
    if not closed_trades.empty:
        # Ensure we have date
        closed_trades = closed_trades.sort_values(by='SignalDate')
        closed_trades['Equity'] = closed_trades['PnL'].cumsum()
        closed_trades['Peak'] = closed_trades['Equity'].cummax()
        closed_trades['Drawdown'] = closed_trades['Equity'] - closed_trades['Peak']
        max_dd = closed_trades['Drawdown'].min()
    else:
        max_dd = 0.0

    # --- DASHBOARD UI ---
    st.markdown("### 📈 Performance Overview")
    
    # Row 1: Key KPIs
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Trades", total_trades, help="Total number of trades executed")
    m2.metric("Win Rate", f"{win_rate:.1f}%", help="Percentage of winning trades")
    m3.metric("Profit Factor", f"{profit_factor:.2f}", help="Gross Profit / Gross Loss (> 1.5 is good)")
    m4.metric("Net Profit", f"{total_pnl:.2f}%", delta=f"{total_pnl:.2f}%", help=f"Gross Win ({gross_win:.2f}%) - Gross Loss ({gross_loss:.2f}%)")
    
    # Row 2: Expert Analysis
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("Total Win (Gross)", f"{gross_win:.2f}%", help="Sum of all winning trades")
    e2.metric("Total Loss (Gross)", f"-{gross_loss:.2f}%", delta_color="inverse", help="Sum of all losing trades")
    e3.metric("Expectancy", f"{expectancy:.2f}%", help="Expected return per trade (The Edge)", delta_color="normal" if expectancy > 0 else "inverse")
    e4.metric("Max Drawdown", f"{max_dd:.2f}%", help="Maximum drop from peak equity (Capital Risk)", delta_color="inverse")


    # Row 3: Extremes (Optional, or can be combined)
    # Keeping it simple for now, moved Best/Worst to tooltip or secondary view if needed, 
    # but let's keep them as a smaller section or part of insights.
    
    # --- RECOMMENDATIONS ENGINE ---
    st.markdown("### 💡 Strategy Insights & Recommendations")
    
    insights = []
    
    # 1. Edge Check
    if expectancy > 0.5:
        insights.append(f"🔥 **Strong Edge**: Your expectancy is {expectancy:.2f}% per trade. This is excellent for compounding.")
    elif expectancy < 0:
        insights.append(f"🛑 **Negative Edge**: You are losing {abs(expectancy):.2f}% per trade on average. Use the 'Intraday' or 'MTF' filter to isolate the bleeding strategy.")

    # 2. Risk Reward Check
    if abs(avg_loss) > avg_win:
        insights.append("⚠️ **Inverted Risk/Reward**: Your Avg Loss > Avg Win. You need a high win rate (>60%) to sustain this.")
    elif avg_win > (2 * abs(avg_loss)):
        insights.append("✅ **Sniper Risk Management**: Avg Win is >2x Avg Loss. This allows you to differ occasional losing streaks.")
        
    # 3. Drawdown Check
    if abs(max_dd) > 10:
        insights.append(f"📉 **High Drawdown**: Max Drawdown is {max_dd:.2f}%. Consider reducing position size to preserve capital stability.")
        
    # 4. Profit Factor Check
    if profit_factor > 2.0:
        insights.append("💰 **Holy Grail Territory**: Profit Factor > 2.0 is elite performance.")

    if not insights:
        st.info("Collect more data to generate specific insights.")
    else:
        for insight in insights:
            if "⚠️" in insight or "🛑" in insight or "📉" in insight:
                st.warning(insight)
            else:
                st.success(insight)

    
    
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
            column_order=["TradeID", "Ticker", "SignalDate", "EntryDate", "EntryPrice", "StopLoss", "TargetPrice", "Status", "ExitPrice", "ExitDate", "PnL", "Notes"],
            column_config={
                "TradeID": "ID",
                "Ticker": "Symbol",
                "SignalDate": "Signal Date",
                "EntryDate": st.column_config.DatetimeColumn("Entry Date", format="YYYY-MM-DD", help="Date of Entry"),
                "EntryPrice": st.column_config.NumberColumn("Entry", format="₹%.2f"),
                "StopLoss": st.column_config.NumberColumn("SL", format="₹%.2f"),
                "TargetPrice": st.column_config.NumberColumn("Target", format="₹%.2f"),
                "ExitPrice": st.column_config.NumberColumn("Exit Price", format="₹%.2f"),
                "ExitDate": st.column_config.DatetimeColumn("Exit Date", format="YYYY-MM-DD"),
                "PnL": st.column_config.NumberColumn("PnL %", format="%.2f%%"),
                "Strategy": None, 
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
            # Format Time Columns to show Full DateTime
            if 'EntryDate' in df_intra.columns:
                df_intra['EntryDate'] = pd.to_datetime(df_intra['EntryDate'], errors='coerce')
            
            if 'ExitDate' in df_intra.columns:
                 df_intra['ExitDate'] = pd.to_datetime(df_intra['ExitDate'], errors='coerce')
            
            # Recalculate PnL for display if ExitPrice exists
            def calc_pnl(row):
                if pd.notnull(row['ExitPrice']) and row['ExitPrice'] > 0 and pd.notnull(row['EntryPrice']) and row['EntryPrice'] > 0:
                    return (row['ExitPrice'] - row['EntryPrice']) / row['EntryPrice'] * 100
                return row['PnL']
            
            if 'ExitPrice' in df_intra.columns and 'EntryPrice' in df_intra.columns:
                df_intra['PnL'] = df_intra.apply(calc_pnl, axis=1)
            
            if 'EntryPrice' in df_intra.columns and 'StopLoss' in df_intra.columns:
                df_intra['SL %'] = ((df_intra['EntryPrice'] - df_intra['StopLoss']).abs() / df_intra['EntryPrice']) * 100
            
            if 'EntryPrice' in df_intra.columns and 'TargetPrice' in df_intra.columns:
                df_intra['Target %'] = ((df_intra['TargetPrice'] - df_intra['EntryPrice']).abs() / df_intra['EntryPrice']) * 100

            # Calculate Risk and Rec Qty
            if 'EntryPrice' in df_intra.columns and 'StopLoss' in df_intra.columns:
                 df_intra['Risk'] = (df_intra['EntryPrice'] - df_intra['StopLoss']).abs()
                 
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
                "EntryDate": st.column_config.DatetimeColumn("Entry Time", format="YYYY-MM-DD HH:mm:ss"),
                "EntryPrice": st.column_config.NumberColumn("Entry", format="₹%.2f"),
                "StopLoss": st.column_config.NumberColumn("SL", format="₹%.2f"),
                "SL %": st.column_config.NumberColumn("SL %", format="%.2f%%"),
                "Risk": st.column_config.NumberColumn("Risk/Share", format="₹%.2f"),
                "Qty (1L)": st.column_config.NumberColumn("Qty (1L Cap)", format="%d"),
                "UpdatedStopLoss": st.column_config.NumberColumn("Updated SL", format="₹%.2f"),
                "TargetPrice": st.column_config.NumberColumn("Target", format="₹%.2f"),
                "Target %": st.column_config.NumberColumn("Tgt %", format="%.2f%%"),
                "ExitPrice": st.column_config.NumberColumn("Exit Price", format="₹%.2f"),
                "ExitDate": st.column_config.DatetimeColumn("Exit Time", format="YYYY-MM-DD HH:mm:ss"),
                "PnL": st.column_config.NumberColumn("PnL %", format="%.2f%%"),
                "Strategy": None
            }
        )
