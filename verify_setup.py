import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    print("Testing imports...")
    import streamlit
    import yfinance
    import pandas
    import ta
    import textblob
    import plotly
    print("Imports successful.")

    print("Testing data loader...")
    from src.data_loader import fetch_stock_data
    df = fetch_stock_data("AAPL", period="1mo")
    if not df.empty:
        print(f"Data fetched successfully. Shape: {df.shape}")
    else:
        print("Warning: Data fetch returned empty DataFrame.")

    print("Testing analysis...")
    from src.analysis import calculate_technical_indicators, calculate_statistics
    df = calculate_technical_indicators(df)
    stats = calculate_statistics(df)
    print(f"Analysis successful. Volatility: {stats.get('Volatility')}")

    print("Testing model training...")
    from src.model import train_model
    # Mock sentiment
    model, metrics, _ = train_model(df, sentiment_score=0.1)
    if model:
        print(f"Model trained successfully. RMSE: {metrics['RMSE']}")
    else:
        print("Model training failed (likely insufficient data).")

    print("Verification complete.")

except Exception as e:
    print(f"Verification failed: {e}")
    sys.exit(1)
