import sys
import os
import pandas as pd
import numpy as np

# Add current directory to path
sys.path.append(os.getcwd())

from src.data_loader import fetch_stock_data
from src.model import train_arima_model, train_holtwinters_model, train_moving_average_model, predict_future

def verify_timeseries():
    print("Fetching Data...")
    df = fetch_stock_data("RELIANCE.NS", period="2y")
    if df.empty:
        print("Failed to fetch data.")
        return

    print("\n--- Testing ARIMA ---")
    model_arima, metrics_arima, _ = train_arima_model(df)
    if model_arima:
        print(f"ARIMA MAPE: {metrics_arima['MAPE']:.4f}")
        preds = predict_future(model_arima, df, days=5, model_type="ARIMA")
        print(f"ARIMA Forecast (5 days): {preds}")
    else:
        print("ARIMA Training Failed.")

    print("\n--- Testing Holt-Winters ---")
    model_hw, metrics_hw, _ = train_holtwinters_model(df)
    if model_hw:
        print(f"Holt-Winters MAPE: {metrics_hw['MAPE']:.4f}")
        preds = predict_future(model_hw, df, days=5, model_type="Holt-Winters")
        print(f"HW Forecast (5 days): {preds}")
    else:
        print("Holt-Winters Training Failed.")

    print("\n--- Testing Moving Average ---")
    model_ma, metrics_ma, _ = train_moving_average_model(df)
    if model_ma is not None:
        print(f"MA MAPE: {metrics_ma['MAPE']:.4f}")
        preds = predict_future(model_ma, df, days=5, model_type="Moving Average")
        print(f"MA Forecast (5 days): {preds}")
    else:
        print("MA Training Failed.")

if __name__ == "__main__":
    verify_timeseries()
