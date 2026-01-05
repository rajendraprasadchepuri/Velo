import sys
import os
import pandas as pd
import numpy as np

# Add current directory to path
sys.path.append(os.getcwd())

from src.data_loader import fetch_stock_data, fetch_benchmark
from src.analysis import calculate_technical_indicators, calculate_market_metrics
from src.model import train_model, train_prophet_model, predict_future

def verify_forecast():
    print("Fetching Data...")
    df = fetch_stock_data("RELIANCE.NS", period="1y")
    bench = fetch_benchmark(period="1y")
    
    if df.empty or bench.empty:
        print("Failed to fetch data.")
        return

    df = calculate_technical_indicators(df)
    df = calculate_market_metrics(df, bench)
    
    print("\n--- Testing Prophet Forecast (60 Days) ---")
    model_prophet, _, _ = train_prophet_model(df)
    if model_prophet:
        preds = predict_future(model_prophet, df, days=60, model_type="Prophet")
        print(f"Prophet Predictions: {len(preds)}")
        if len(preds) == 60:
            print("Prophet Forecast Length Correct.")
        else:
            print(f"Error: Expected 60, got {len(preds)}")
    else:
        print("Prophet Training Failed.")

    print("\n--- Testing RF Recursive Forecast (5 Days) ---")
    # We test 5 days for RF to save time, as recursive is slow
    model_rf, _, _ = train_model(df, tune=False)
    if model_rf:
        preds = predict_future(model_rf, df, days=5, model_type="Random Forest")
        print(f"RF Predictions: {len(preds)}")
        print(f"Values: {preds}")
        if len(preds) == 5:
            print("RF Forecast Length Correct.")
        else:
            print(f"Error: Expected 5, got {len(preds)}")
    else:
        print("RF Training Failed.")

if __name__ == "__main__":
    verify_forecast()
