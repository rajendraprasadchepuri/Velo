import sys
import os
import pandas as pd

# Add current directory to path
sys.path.append(os.getcwd())

from src.data_loader import fetch_stock_data
from src.analysis import calculate_technical_indicators
from src.model import train_model

def test_indian_ticker():
    print("Testing Indian Ticker (RELIANCE.NS)...")
    df = fetch_stock_data("RELIANCE.NS", period="3mo")
    if not df.empty:
        print(f"Successfully fetched {len(df)} rows.")
        return df
    else:
        print("Failed to fetch data.")
        return None

def test_model_training(df):
    print("Testing Model Training...")
    if df is None:
        print("Skipping model test due to data fetch failure.")
        return

    # Calculate indicators first
    df = calculate_technical_indicators(df)
    
    # Test with sufficient data
    model, metrics, _ = train_model(df, sentiment_score=0)
    if model:
        print(f"Model trained successfully. RMSE: {metrics['RMSE']}")
    else:
        print(f"Model training failed as expected or unexpected: {metrics.get('error')}")

    # Test with insufficient data (simulate short period)
    print("Testing with insufficient data...")
    short_df = df.tail(20) # Too short for 50-day SMA + training
    model, metrics, _ = train_model(short_df, sentiment_score=0)
    if not model:
        print(f"Correctly handled insufficient data: {metrics.get('error')}")
    else:
        print("Warning: Model trained on insufficient data?")

if __name__ == "__main__":
    df = test_indian_ticker()
    test_model_training(df)
