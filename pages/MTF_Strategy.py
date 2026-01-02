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
