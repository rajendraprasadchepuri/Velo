import sys
import os
import pandas as pd
import numpy as np

# Add current directory to path
sys.path.append(os.getcwd())

from src.data_loader import fetch_stock_data
from src.analysis import calculate_technical_indicators
from src.model import train_model

def verify_tuning():
    print("Fetching Data...")
    df = fetch_stock_data("RELIANCE.NS", period="1y") # Use 1y for speed
    if df.empty:
        print("Failed to fetch data.")
        return

    df = calculate_technical_indicators(df)
    
    print("\n--- Testing Tuning (Random Forest) ---")
    # Enable tuning
    model, metrics, _ = train_model(df, tune=True)
    
    if model:
        print(f"MAPE: {metrics.get('MAPE'):.4f}")
        if 'Best Params' in metrics:
            print("SUCCESS: Best Params found in metrics.")
            print(f"Params: {metrics['Best Params']}")
        else:
            print("FAILURE: Best Params NOT found in metrics.")
    else:
        print("Training Failed.")

if __name__ == "__main__":
    verify_tuning()
