import streamlit as st
import pandas as pd
from src.mtf_strategy import run_pro_scanner

st.set_page_config(page_title="MTF Strategy", layout="wide")
from src.ui import add_logo
add_logo()

st.title("Ultra-Precision MTF Strategy")
st.markdown("""
This strategy focuses on **high-probability trades** by combining:
- **Market Guardrails:** Checks if Nifty 50 and Sector indices are bullish.
- **Trend Alignment:** Ensures stock price is above EMA20.
- **Volume Confirmation:** Uses Volume Price Trend (VPT) to detect institutional buying.
""")

if st.button("🚀 Run Ultra-Precision Scanner"):
    progress_bar = st.progress(0, text="Starting scanner...")
    
    def update_progress(progress, text):
        progress_bar.progress(progress, text=text)
        
    results, warnings = run_pro_scanner(progress_callback=update_progress)
    progress_bar.empty()
    
    # Display warnings
    for warn in warnings:
        st.warning(warn)
        
    if not results:
        st.info("No data returned or scanner failed.")
    else:
        df = pd.DataFrame(results)
        
        # Sort by Raw Score desc
        df = df.sort_values(by="Raw Score", ascending=False)
        
        # Display Summary Metrics
        total_scanned = len(results)
        high_conviction = len(df[df['Signal'] == "STRONG BUY"])
        
        col1, col2 = st.columns(2)
        col1.metric("Stocks Scanned", total_scanned)
        col2.metric("High Conviction Signals", high_conviction)
        
        st.subheader("Scanner Results")
        
        # Color coding for Signal
        def color_signal(val):
            color = 'red'
            if val == "STRONG BUY": color = 'green'
            elif val == "WATCH": color = 'orange'
            return f'color: {color}'

        # Display Dataframe with style
        st.dataframe(
            df[['Ticker', 'Signal', 'Confidence Score', 'Current Price', 'Market Correlation', 'Reasons']],
            use_container_width=True,
            column_config={
                "Ticker": "Stock Symbol",
                "Signal": "Trade Signal",
                "Confidence Score": st.column_config.ProgressColumn(
                    "Confidence",
                    help="Confidence score based on technicals",
                    format="%s",
                    min_value=0,
                    max_value=100,
                ),
            }
        )
        
        if high_conviction == 0:
            st.info("❌ No 80%+ confidence signals found today. Better to wait than force a trade.")
        else:
            st.success(f"🎯 Found {high_conviction} high-probability setups!")

st.markdown("---")
st.header("Strategy Backtest")
st.markdown("Test the strategy performance on historical data.")

col_b1, col_b2, col_b3 = st.columns(3)
backtest_ticker = col_b1.text_input("Ticker Symbol", "FEDERALBNK.NS")
backtest_years = col_b2.number_input("Years to Backtest", min_value=1, max_value=5, value=1)
run_backtest = col_b3.button("Run Backtest")

if run_backtest:
    from src.mtf_strategy import run_strategy_backtest
    with st.spinner(f"Backtesting {backtest_ticker}..."):
        # Determine sector index based on ticker
        import yfinance as yf
        try:
            info = yf.Ticker(backtest_ticker).info
            sector_res = "^NSEBANK" if "Bank" in info.get('industry', '') else "^NSEI"
        except:
            sector_res = "^NSEBANK" # Default fallback
            
        metrics = run_strategy_backtest(backtest_ticker, sector_index=sector_res, years=backtest_years)
        
        if "Error" in metrics:
            st.error(metrics["Error"])
        else:
            st.subheader(f"Backtest Results: {backtest_ticker}")
            
            b_col1, b_col2, b_col3 = st.columns(3)
            b_col1.metric("Total Return (MTF)", metrics["Total Return (MTF)"])
            b_col2.metric("Buy & Hold Return", metrics["Buy & Hold Return"])
            b_col3.metric("Max Drawdown", metrics["Max Drawdown"])
            
            b_col4, b_col5 = st.columns(2)
            b_col4.metric("Trade Opportunity Days", metrics["Trade Opportunity Days"])
            b_col5.metric("Daily Win Rate", metrics["Daily Win Rate"])
            
            if float(metrics["Total Return (MTF)"].strip('%')) > float(metrics["Buy & Hold Return"].strip('%')):
                st.success("🚀 Strategy Outperformed Buy & Hold!")
            else:
                st.warning("Strategy Underperformed Buy & Hold.")
