import sys
import os
import pandas as pd
import numpy as np

# Add current directory to path
sys.path.append(os.getcwd())

from src.data_loader import fetch_stock_data
from src.analysis import calculate_technical_indicators
from src.model import train_xgboost_model, train_prophet_model

def verify_models():
    print("Fetching data...")
    df = fetch_stock_data("RELIANCE.NS", period="1y")
    if df.empty:
        print("Failed to fetch data.")
        return

    df = calculate_technical_indicators(df)
    # Add Daily_Return if missing (analysis.py should have it now)
    if 'Daily_Return' not in df.columns:
        df['Daily_Return'] = df['Close'].pct_change()

    print("\n--- Testing XGBoost ---")
    model_xgb, metrics_xgb, _ = train_xgboost_model(df)
    if model_xgb:
        print(f"XGBoost Success! RMSE: {metrics_xgb['RMSE']}")
    else:
        print(f"XGBoost Failed: {metrics_xgb.get('error')}")

    print("\n--- Testing Prophet ---")
    model_prophet, metrics_prophet, _ = train_prophet_model(df)
    if model_prophet:
        print(f"Prophet Success! RMSE: {metrics_prophet['RMSE']}")
    else:
        print(f"Prophet Failed: {metrics_prophet.get('error')}")

if __name__ == "__main__":
    verify_models()
