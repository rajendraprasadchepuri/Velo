import sys
import os
import pandas as pd
import numpy as np

# Add current directory to path
sys.path.append(os.getcwd())

from src.data_loader import fetch_stock_data
from src.analysis import calculate_technical_indicators
from src.model import train_model, train_xgboost_model, train_prophet_model

def verify_mape():
    print("Fetching Data...")
    df = fetch_stock_data("RELIANCE.NS", period="1y")
    if df.empty:
        print("Failed to fetch data.")
        return

    df = calculate_technical_indicators(df)
    
    print("\n--- Testing Random Forest MAPE ---")
    model, metrics, _ = train_model(df, tune=False)
    if model:
        mape = metrics.get('MAPE')
        print(f"RF MAPE: {mape:.4f} ({mape*100:.2f}%)")
        if 'RMSE' in metrics:
            print("Error: RMSE still present in metrics.")
        else:
            print("RMSE successfully removed.")
    else:
        print("RF Training Failed.")

    print("\n--- Testing Prophet MAPE ---")
    model_p, metrics_p, _ = train_prophet_model(df)
    if model_p:
        mape = metrics_p.get('MAPE')
        print(f"Prophet MAPE: {mape:.4f} ({mape*100:.2f}%)")
    else:
        print("Prophet Training Failed.")

if __name__ == "__main__":
    verify_mape()
