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

# Initialize session state
if "scanner_results" not in st.session_state:
    st.session_state.scanner_results = None
if "scanner_warnings" not in st.session_state:
    st.session_state.scanner_warnings = []

if st.button("🚀 Run Ultra-Precision Scanner"):
    progress_bar = st.progress(0, text="Starting scanner...")
    
    def update_progress(progress, text):
        progress_bar.progress(progress, text=text)
        
    results, warnings = run_pro_scanner(progress_callback=update_progress)
    progress_bar.empty()
    
    # Store in session state
    st.session_state.scanner_results = results
    st.session_state.scanner_warnings = warnings

# Display results if they exist in session state
if st.session_state.scanner_warnings:
    for warn in st.session_state.scanner_warnings:
        st.warning(warn)

if st.session_state.scanner_results is not None:
    results = st.session_state.scanner_results
    if not results:
        st.info("No data returned or scanner failed.")
    else:
        df = pd.DataFrame(results)
        
        # Sort by Raw Score desc
        df = df.sort_values(by="Raw Score", ascending=False)
        
        # Filter for high confidence only
        df = df[df['Confidence Score'] >= 80]
        
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
            df[['Ticker', 'Industry', 'Signal', 'Confidence Score', 'Current Price', 'Stop Loss', 'Target Price', 'Est. Days', 'Reasoning']],
            use_container_width=True,
            column_config={
                "Ticker": "Stock Symbol",
                "Industry": "Sector",
                "Signal": "Trade Signal",
                "Confidence Score": st.column_config.ProgressColumn(
                    "Confidence",
                    help="Confidence score based on technicals",
                    format="%d%%",
                    min_value=0,
                    max_value=100,
                ),
                "Current Price": st.column_config.NumberColumn(format="₹%.2f"),
                "Stop Loss": st.column_config.NumberColumn(format="₹%.2f"),
                "Target Price": st.column_config.NumberColumn(format="₹%.2f"),
                "Est. Days": "Timeframe",
                "Reasoning": "Analysis",
            }
        )

        st.subheader("Fundamental Analysis")
        st.dataframe(
            df[['Ticker', 'Fundamental Rating', 'Market Cap', 'P/E Ratio', 'P/B Ratio', 'ROE', 'Dividend Yield', 'Operating Margin']],
            use_container_width=True,
            column_config={
                "Ticker": "Stock Symbol",
                "Fundamental Rating": "Trend",
                "Market Cap": st.column_config.NumberColumn("Market Cap", format="₹%d"), # Using integer format for large numbers or could use compact
                "P/E Ratio": st.column_config.NumberColumn("P/E", format="%.2f"),
                "P/B Ratio": st.column_config.NumberColumn("P/B", format="%.2f"),
                "ROE": st.column_config.NumberColumn("ROE", format="%.2f%%"), # Assuming raw data is like 0.15 or 15, let's assume raw is 0.15 -> percent
                "Dividend Yield": st.column_config.NumberColumn("Div Yield", format="%.2f%%"),
                "Operating Margin": st.column_config.NumberColumn("Op Margin", format="%.2f%%"),
            }
        )
        
        if high_conviction == 0:
            st.info("❌ No 80%+ confidence signals found today. Better to wait than force a trade.")
        else:
            st.success(f"🎯 Found {high_conviction} high-probability setups!")

st.markdown("---")
st.header("Strategy Backtest")
st.markdown("Test the strategy performance on historical data.")

col_b1, col_b2, col_b3 = st.columns(3, vertical_alignment="bottom")
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
