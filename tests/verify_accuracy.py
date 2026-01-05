import sys
import os
import pandas as pd
import numpy as np

# Add current directory to path
sys.path.append(os.getcwd())

from src.data_loader import fetch_stock_data
from src.analysis import calculate_technical_indicators
from src.model import train_model, predict_future

def verify_accuracy():
    print("Fetching Data (Max History)...")
    df = fetch_stock_data("RELIANCE.NS", period="max")
    if df.empty:
        print("Failed to fetch data.")
        return
    
    # Limit data for speed if it's too huge, but we want to test 'max' impact
    # Let's use last 2 years for speed in this test script
    df = df.tail(500) 

    df = calculate_technical_indicators(df)
    
    print("\n--- Testing Random Forest Accuracy (Target: Return) ---")
    model, metrics, (y_true, y_pred) = train_model(df, tune=False)
    
    if model:
        mape = metrics.get('MAPE')
        print(f"RF MAPE: {mape:.4f} ({mape*100:.2f}%)")
        
        # Check if predictions are prices (e.g., > 100) or returns (e.g., < 1)
        avg_pred = np.mean(y_pred)
        print(f"Average Predicted Price: {avg_pred:.2f}")
        
        if avg_pred < 10:
            print("Error: Predictions look like returns, not prices!")
        else:
            print("Predictions look like prices. Reconstruction successful.")
            
        if mape < 0.05:
            print("SUCCESS: MAPE < 5%")
        else:
            print("WARNING: MAPE > 5% (Might need tuning or more data)")
            
        # Test Forecast
        print("\n--- Testing Forecast ---")
        future_preds = predict_future(model, df, days=5, model_type="Random Forest")
        print(f"Future Prices (Next 5 days): {future_preds}")
        if future_preds[0] > 100:
             print("Forecast looks valid.")
        else:
             print("Forecast looks like returns (Error).")

    else:
        print("RF Training Failed.")

if __name__ == "__main__":
    verify_accuracy()
