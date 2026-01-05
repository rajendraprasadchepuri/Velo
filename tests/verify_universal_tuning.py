import sys
import os
import pandas as pd
import numpy as np

# Add current directory to path
sys.path.append(os.getcwd())

from src.data_loader import fetch_stock_data
from src.model import train_prophet_model, train_arima_model, train_holtwinters_model, train_moving_average_model

def verify_universal_tuning():
    print("Fetching Data...")
    df = fetch_stock_data("RELIANCE.NS", period="1y")
    if df.empty:
        print("Failed to fetch data.")
        return

    print("\n--- Testing Prophet Tuning ---")
    _, metrics_p, _ = train_prophet_model(df, tune=True)
    if 'Best Params' in metrics_p:
        print(f"SUCCESS: Prophet Best Params: {metrics_p['Best Params']}")
    else:
        print("FAILURE: Prophet Best Params not found.")

    print("\n--- Testing ARIMA Tuning ---")
    _, metrics_a, _ = train_arima_model(df, tune=True)
    if 'Best Params' in metrics_a:
        print(f"SUCCESS: ARIMA Best Params: {metrics_a['Best Params']}")
    else:
        print("FAILURE: ARIMA Best Params not found.")

    print("\n--- Testing Holt-Winters Tuning ---")
    _, metrics_hw, _ = train_holtwinters_model(df, tune=True)
    if 'Best Params' in metrics_hw:
        print(f"SUCCESS: HW Best Params: {metrics_hw['Best Params']}")
    else:
        print("FAILURE: HW Best Params not found.")
        
    print("\n--- Testing MA Tuning ---")
    _, metrics_ma, _ = train_moving_average_model(df, tune=True)
    if 'Best Params' in metrics_ma:
        print(f"SUCCESS: MA Best Params: {metrics_ma['Best Params']}")
    else:
        print("FAILURE: MA Best Params not found.")

if __name__ == "__main__":
    verify_universal_tuning()
