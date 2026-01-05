
import pandas as pd
import os
import shutil
from src.tracker import TradeTracker
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Setup Test Environment
TEST_DIR = "test_data"
if not os.path.exists(TEST_DIR):
    os.makedirs(TEST_DIR)

TEST_CSV = os.path.join(TEST_DIR, "live_trades.csv")

def setup_tracker():
    if os.path.exists(TEST_CSV):
        os.remove(TEST_CSV)
    
    # Monkeypatch the CSV_PATH in tracker
    tracker = TradeTracker()
    tracker.filepath = TEST_CSV
    tracker._ensure_file_exists()
    return tracker

def create_mock_candle(time_str, open_p, high_p, low_p, close_p):
    return {
        "Open": open_p, "High": high_p, "Low": low_p, "Close": close_p
    }

def verify_updates():
    print("Starting Verification...")
    tracker = setup_tracker()
    
    # 1. Add Initial Trade (Intraday)
    print("\n1. Adding Initial Intraday Trade...")
    signal_date = "2024-01-01"
    signal = {
        "Ticker": "TESTSTOCK.NS",
        "Entry Price": 100.0,
        "Stop Loss": 99.0,
        "Target Price": 101.0, # 1% Target initially
        "Signal": "Test Signal"
    }
    tracker.add_trade(signal, strategy_type="Intraday", signal_date=signal_date)
    
    df = tracker.load_trades()
    print(f"Trade Added. Status: {df.iloc[0]['Status']}")
    assert df.iloc[0]['Status'] == 'WAITING_ENTRY'

    # 2. Mock Data for Triggering Entry
    # Candle 1: 09:15 - 09:20 (Skip)
    # Candle 2: 09:20 - 09:25 (Trigger Entry: Low 99.5, High 100.5)
    
    dates = pd.date_range(start=f"{signal_date} 09:15:00", periods=5, freq="5min")
    data_dict = {
        dates[0]: [100, 100, 100, 100], # Skip
        dates[1]: [100, 100.5, 99.5, 100], # Trigger Entry (Low 99.5 <= 100 <= High 100.5)
        dates[2]: [100, 100.8, 100.2, 100.5], # Nothing
        dates[3]: [100, 101.2, 100.5, 101.0], # Target Hit (High 101.2 >= Target 101.0)
        dates[4]: [101, 101.5, 100.8, 101.2], # Second Bump or fallback
    }
    
    # Manually constructing DataFrame that matches yfinance format roughly
    data = pd.DataFrame.from_dict(data_dict, orient='index', columns=['Open', 'High', 'Low', 'Close'])
    data.index.name = 'Datetime'
    
    # Mock yfinance download
    with patch('yfinance.download') as mock_yf:
        mock_yf.return_value = data
        
        # Run Update
        print("\n2. Running Update (Entry Trigger + Target Hit)...")
        tracker.update_status()
        
        df = tracker.load_trades()
        row = df.iloc[0]
        print(f"Status: {row['Status']}")
        print(f"Entry Time: {row['EntryDate']}")
        print(f"Updated SL: {row['UpdatedStopLoss']}")
        print(f"New Target: {row['TargetPrice']}")
        print(f"Notes: {row['Notes']}")
        
        # Checks
        if row['EntryDate'] is None:
            print("FAILURE: Entry Date not set")
        else:
            print("SUCCESS: Entry Date set")
            
        if row['UpdatedStopLoss'] == 101.0:
            print("SUCCESS: SL moved to 101.0")
        else:
            print(f"FAILURE: SL expected 101.0, got {row['UpdatedStopLoss']}")
            
        expected_new_target = 101.0 + (100.0 * 0.005) # 101.5
        if row['TargetPrice'] == expected_new_target:
             print(f"SUCCESS: Target moved to {expected_new_target}")
        else:
             print(f"FAILURE: Target expected {expected_new_target}, got {row['TargetPrice']}")

        # 3. Next Update: Price drops to hit new SL (Trailing Hit)
        # New candle where Low drops to 100.9 (below new SL 101.0)
        print("\n3. Running Update (Trailing SL Hit)...")
        
        dates_2 = pd.date_range(start=f"{signal_date} 09:40:00", periods=1, freq="5min")
        data_2 = pd.DataFrame({
            'Open': [101.5], 'High': [101.5], 'Low': [100.9], 'Close': [101.0]
        }, index=dates_2)
        
        mock_yf.return_value = data_2
        tracker.update_status()
        
        df = tracker.load_trades()
        row = df.iloc[0]
        print(f"Status: {row['Status']}")
        print(f"Exit Price: {row['ExitPrice']}")
        print(f"Exit Time: {row['ExitDate']}")
        
        if row['Status'] == 'STOP_LOSS_HIT':
             print("SUCCESS: Trade Closed on Trailing SL")
        else:
             print(f"FAILURE: Status expected STOP_LOSS_HIT, got {row['Status']}")
             
        if row['ExitPrice'] == 101.0:
             print("SUCCESS: Exit Price correct (Trailing SL)")
        else:
             print(f"FAILURE: Exit Price expected 101.0, got {row['ExitPrice']}")

    # Cleanup
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

if __name__ == "__main__":
    verify_updates()
