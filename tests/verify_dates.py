import sys
import os
import pandas as pd
import numpy as np

# Add current directory to path
sys.path.append(os.getcwd())

from src.data_loader import fetch_stock_data
from src.analysis import calculate_technical_indicators
from src.model import train_model, train_prophet_model, train_arima_model

def verify_dates():
    print("Fetching Data...")
    df = fetch_stock_data("RELIANCE.NS", period="1y")
    if df.empty:
        print("Failed to fetch data.")
        return

    df = calculate_technical_indicators(df)
    
    print("\n--- Testing RF Dates ---")
    result = train_model(df)
    if result[0] is None:
        print(f"RF Training Failed: {result[1]}")
    else:
        _, _, (y_true, y_pred) = result
        if isinstance(y_true, pd.Series) and isinstance(y_true.index, pd.DatetimeIndex):
            print("SUCCESS: RF returns Series with DatetimeIndex")
        else:
            print(f"FAILURE: RF returns {type(y_true)} with index {type(y_true.index) if hasattr(y_true, 'index') else 'None'}")

    print("\n--- Testing Prophet Dates ---")
    result_p = train_prophet_model(df)
    if result_p[0] is None:
        print(f"Prophet Training Failed: {result_p[1]}")
    else:
        _, _, (y_true_p, y_pred_p) = result_p
        if isinstance(y_true_p, pd.Series) and isinstance(y_true_p.index, pd.DatetimeIndex):
            print("SUCCESS: Prophet returns Series with DatetimeIndex")
        else:
            print(f"FAILURE: Prophet returns {type(y_true_p)} with index {type(y_true_p.index) if hasattr(y_true_p, 'index') else 'None'}")

    print("\n--- Testing ARIMA Dates ---")
    result_a = train_arima_model(df)
    if result_a[0] is None:
        print(f"ARIMA Training Failed: {result_a[1]}")
    else:
        _, _, (y_true_a, y_pred_a) = result_a
        if isinstance(y_true_a, pd.Series) and isinstance(y_true_a.index, pd.DatetimeIndex):
            print("SUCCESS: ARIMA returns Series with DatetimeIndex")
        else:
            print(f"FAILURE: ARIMA returns {type(y_true_a)} with index {type(y_true_a.index) if hasattr(y_true_a, 'index') else 'None'}")

if __name__ == "__main__":
    verify_dates()
