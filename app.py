import streamlit as st
import pandas as pd
import plotly.express as px
from src.data_loader import fetch_stock_data
from src.analysis import calculate_statistics, calculate_technical_indicators

st.set_page_config(page_title="Stock Analysis & Prediction", layout="wide")
from src.ui import add_logo
add_logo()

st.title("Stock Analysis & Prediction Dashboard")

st.sidebar.header("Configuration")
ticker_input = st.sidebar.text_input("Enter Stock Ticker (e.g., RELIANCE, TCS)", "RELIANCE")
ticker = ticker_input.upper()
if not ticker.endswith(".NS") and not ticker.endswith(".BO"):
    ticker += ".NS"

period = st.sidebar.selectbox("Select Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=3)

if "data" not in st.session_state:
    st.session_state.data = None
if "ticker" not in st.session_state:
    st.session_state.ticker = ""

if st.button("Analyze"):
    with st.spinner(f"Analyzing {ticker}..."):
        # Fetch Data
        df = fetch_stock_data(ticker, period=period)
        
        if not df.empty:
            # Calculate Indicators
            df = calculate_technical_indicators(df)
            
            # Fetch Benchmark (Nifty 50) & Calculate Market Metrics
            from src.data_loader import fetch_benchmark
            from src.analysis import calculate_market_metrics
            
            benchmark_df = fetch_benchmark(period=period)
            df = calculate_market_metrics(df, benchmark_df)
            
            stats = calculate_statistics(df)
            
            # Store in session state
            st.session_state.data = df
            st.session_state.stats = stats
            st.session_state.ticker = ticker
        else:
            st.error(f"No data found for {ticker}. Please check the ticker symbol.")
            st.session_state.data = None

# Display Dashboard if data exists
if st.session_state.data is not None:
    df = st.session_state.data
    stats = st.session_state.stats
    current_ticker = st.session_state.ticker
    
    # Display Stats
    st.header(f"Analysis for {current_ticker}")
    col1, col2 = st.columns(2)
    col1.metric("Last Price", f"₹{stats.get('Last Price', 0):.2f}")
    col2.metric("Volatility (Ann.)", f"{stats.get('Volatility', 0):.2%}")
    
    # Display Charts
    st.subheader("Price History")
    fig = px.line(df, x=df.index, y=['Close', 'SMA_50', 'EMA_20'], title=f'{current_ticker} Stock Price with Indicators')
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Technical Indicators")
    st.dataframe(df.tail())
    
    # News and Sentiment
    st.subheader("News & Sentiment Analysis")
    from src.data_loader import fetch_news
    from src.sentiment import analyze_news_sentiment
    
    # Cache news to avoid refetching on every interaction
    if "news_data" not in st.session_state or st.session_state.news_ticker != current_ticker:
        st.session_state.news_data = fetch_news(current_ticker)
        st.session_state.news_ticker = current_ticker
    
    news = st.session_state.news_data
    avg_sentiment, processed_news = analyze_news_sentiment(news)
    
    st.metric("Average News Sentiment", f"{avg_sentiment:.2f}")
    
    if processed_news:
        for item in processed_news[:5]: # Show top 5 news
            sentiment_color = "green" if item.get('sentiment', 0) > 0 else "red" if item.get('sentiment', 0) < 0 else "gray"
            title = item.get('title', 'No Title')
            link = item.get('link', '#')
            publisher = item.get('publisher', 'Unknown')
            sentiment_score = item.get('sentiment', 0)
            
            st.markdown(f"**[{title}]({link})**")
            st.markdown(f"Publisher: {publisher} | Sentiment: :{sentiment_color}[{sentiment_score:.2f}]")
            st.write("---")
    else:
        st.info("No news found.")
        
    # Prediction
    st.subheader("Price Prediction (Beta)")
    from src.model import train_model, train_xgboost_model, train_prophet_model, train_arima_model, train_holtwinters_model, train_moving_average_model, predict_future
    
    col_m1, col_m2 = st.columns(2)
    model_option = col_m1.selectbox("Select Model", ["Random Forest", "XGBoost", "Prophet", "ARIMA", "Holt-Winters", "Moving Average"])
    enable_tuning = col_m2.checkbox("Enable Hyperparameter Tuning (Slower)", value=False, help="Optimizes model parameters for better accuracy. Takes longer to train.")
    
    forecast_days = st.slider("Forecast Horizon (Days)", min_value=1, max_value=60, value=7)
    
    if st.button("Train Model & Predict"):
        with st.spinner(f"Training {model_option} model..."):
            model = None
            metrics = {}
            test_results = None
            
            if model_option == "Random Forest":
                model, metrics, test_results = train_model(df, sentiment_score=avg_sentiment, tune=enable_tuning)
            elif model_option == "XGBoost":
                model, metrics, test_results = train_xgboost_model(df, sentiment_score=avg_sentiment, tune=enable_tuning)
            elif model_option == "Prophet":
                model, metrics, test_results = train_prophet_model(df, tune=enable_tuning)
            elif model_option == "ARIMA":
                model, metrics, test_results = train_arima_model(df, tune=enable_tuning)
            elif model_option == "Holt-Winters":
                model, metrics, test_results = train_holtwinters_model(df, tune=enable_tuning)
            elif model_option == "Moving Average":
                model, metrics, test_results = train_moving_average_model(df, tune=enable_tuning)
            
            if model:
                st.success(f"{model_option} trained successfully!")
                
                mape = metrics['MAPE']
                mape_pct = mape * 100
                
                # Display MAPE with Target Indicator
                col_metric1, col_metric2 = st.columns(2)
                col_metric1.metric("Model MAPE", f"{mape_pct:.2f}%")
                
                if mape_pct < 5.0:
                    col_metric2.success("Target Met (< 5%) ✅")
                else:
                    col_metric2.error("Target Missed (> 5%) ❌")
                    st.caption("Try enabling Hyperparameter Tuning or using a different model.")
                
                # Display Best Params if available
                if 'Best Params' in metrics:
                    with st.expander("✨ Best Hyperparameters Found"):
                        st.json(metrics['Best Params'])
                
                # Show Test Results
                y_test, preds = test_results
                test_df = pd.DataFrame({"Actual": y_test, "Predicted": preds})
                st.line_chart(test_df)
                
                # Predict Future
                with st.spinner(f"Forecasting next {forecast_days} days..."):
                    future_preds = predict_future(model, df, days=forecast_days, sentiment_score=avg_sentiment, model_type=model_option)
                
                # Create Future Dates
                last_date = df.index[-1]
                future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, forecast_days + 1)]
                
                future_df = pd.DataFrame({"Predicted Price": future_preds}, index=future_dates)
                
                st.subheader(f"{forecast_days}-Day Forecast")
                
                # Plot History + Forecast
                # We combine historical close and future predictions
                history_df = df[['Close']].copy()
                history_df.columns = ['Price']
                history_df['Type'] = 'History'
                
                future_plot_df = future_df.copy()
                future_plot_df.columns = ['Price']
                future_plot_df['Type'] = 'Forecast'
                
                combined_df = pd.concat([history_df.tail(90), future_plot_df]) # Show last 90 days history + forecast
                
                fig_forecast = px.line(combined_df, x=combined_df.index, y='Price', color='Type', 
                                     title=f'{current_ticker} Price Forecast',
                                     color_discrete_map={"History": "blue", "Forecast": "orange"})
                fig_forecast.update_traces(mode='lines')
                st.plotly_chart(fig_forecast, use_container_width=True)
                
                # Forecast Signal
                current_price = df['Close'].iloc[-1]
                final_price = future_preds[-1]
                total_return = (final_price - current_price) / current_price * 100
                
                st.subheader("Forecast Signal")
                col_sig1, col_sig2 = st.columns(2)
                
                col_sig1.metric(f"{forecast_days}-Day Return", f"{total_return:.2f}%", f"₹{final_price - current_price:.2f}")
                
                if total_return > 10:
                    col_sig2.success("STRONG BUY 🚀🚀")
                    col_sig2.caption("Projected return > 10%")
                elif total_return > 2:
                    col_sig2.success("BUY 🚀")
                    col_sig2.caption("Projected return > 2%")
                elif total_return < -10:
                    col_sig2.error("STRONG SELL 📉📉")
                    col_sig2.caption("Projected loss > 10%")
                elif total_return < -2:
                    col_sig2.error("SELL 📉")
                    col_sig2.caption("Projected loss > 2%")
                else:
                    col_sig2.info("HOLD ✋")
                    col_sig2.caption("Flat trend (-2% to +2%)")
                    
                # Show Forecast Table
                st.write("Forecast Data:")
                st.dataframe(future_df)
                
            else:
                st.warning(f"Could not train model: {metrics.get('error', 'Unknown error')}")
