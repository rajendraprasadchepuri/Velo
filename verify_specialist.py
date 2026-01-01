import sys
import os
import pandas as pd
import numpy as np

# Add current directory to path
sys.path.append(os.getcwd())

from src.data_loader import fetch_stock_data, fetch_benchmark
from src.analysis import calculate_technical_indicators, calculate_market_metrics
from src.model import prepare_features

def verify_specialist_features():
    print("Fetching Stock Data (RELIANCE.NS)...")
    df = fetch_stock_data("RELIANCE.NS", period="1y")
    
    print("Fetching Benchmark Data (^NSEI)...")
    bench = fetch_benchmark(period="1y")
    
    if df.empty or bench.empty:
        print("Failed to fetch data.")
        return

    print("Calculating Technical Indicators (including OBV)...")
    df = calculate_technical_indicators(df)
    
    if 'OBV' in df.columns:
        print("OBV calculated successfully.")
    else:
        print("Error: OBV missing.")

    print("Calculating Market Metrics (Beta, Relative Return)...")
    df = calculate_market_metrics(df, bench)
    
    if 'Beta' in df.columns and 'Relative_Return' in df.columns:
        print("Market Metrics (Beta, Relative Return) calculated successfully.")
        print(f"Latest Beta: {df['Beta'].iloc[-1]}")
    else:
        print("Error: Market Metrics missing.")

    print("Preparing Features (checking Seasonality)...")
    X, y, cols = prepare_features(df)
    
    if 'DayOfWeek' in cols and 'Month' in cols:
        print("Seasonality Features (DayOfWeek, Month) added successfully.")
    else:
        print("Error: Seasonality Features missing.")
        
    print(f"Total Features: {len(cols)}")
    print("Verification Complete.")

if __name__ == "__main__":
    verify_specialist_features()
