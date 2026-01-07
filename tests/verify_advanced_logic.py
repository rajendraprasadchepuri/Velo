import pandas as pd
import unittest
from unittest.mock import MagicMock, patch
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.tracker import TradeTracker

class TestAdvancedLogic(unittest.TestCase):
    def setUp(self):
        self.tracker_file = "test_advanced_trades.csv"
        self.tracker = TradeTracker()
        self.tracker.filepath = self.tracker_file
        # Create a fresh file
        pd.DataFrame(columns=["TradeID","Ticker","SignalDate","EntryPrice","StopLoss","TargetPrice","Status","ExitPrice","ExitDate","EntryDate","UpdatedStopLoss","PnL","Notes","Strategy","ATR","TriggerHigh","VWAP","InitialSL"]).to_csv(self.tracker_file, index=False)

    def tearDown(self):
        if os.path.exists(self.tracker_file):
            os.remove(self.tracker_file)

    @patch('src.tracker.datetime')
    @patch('yfinance.download')
    def test_entry_confirmation_and_advanced_logic(self, mock_download, mock_datetime):
        # Mock current time to be 09:30 AM (During Market Hours)
        mock_now = datetime(2026, 1, 6, 9, 30, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strftime.side_effect = lambda fmt: mock_now.strftime(fmt)
        print("\nTesting Advanced Strategy Logic...")
        
        # 1. Setup Trade with Advanced Params
        signal = {
            "Ticker": "TEST_ADV",
            "Entry Price": 100.0, # Trigger line (High of signal candle)
            "Signal": "Advanced Buy",
            "ATR": 2.0,
            "TriggerHigh": 100.0,
            "VWAP": 99.0
        }
        self.tracker.add_trade(signal, strategy_type="Intraday", signal_date="2026-01-06")
        
        # 2. Mock Data for Entry
        # Candle 1: 09:16 - High 100.0, Low 99.0, Close 99.5 (No Entry, Close <= Trigger)
        # Candle 2: 09:17 - High 100.5, Low 99.5, Close 100.2 (Entry! Close > 100.05)
        # Wait, buffer is 0.05% of 100 = 0.05. Target Entry > 100.05.
        
        # Candle 1: 03:46 UTC (09:16 IST)
        # Candle 2: 03:47 UTC (09:17 IST)
        
        dates = pd.to_datetime(["2026-01-06 03:46:00", "2026-01-06 03:47:00"]).tz_localize('UTC')
        data_entry = pd.DataFrame({
            "Open": [99.0, 99.5],
            "High": [100.0, 100.5],
            "Low": [99.0, 99.5],
            "Close": [99.5, 100.2], # 100.2 > 100.05
            "Volume": [1000, 2000]
        }, index=dates)
        
        mock_download.return_value = data_entry
        
        self.tracker.update_status()
        
        df = self.tracker.load_trades()
        row = df.iloc[0]
        
        print("Status after Entry:", row['Status'])
        self.assertEqual(row['Status'], "OPEN")
        self.assertEqual(row['EntryPrice'], 100.2) # Execution at Close
        
        # Verify SL = Entry - 1.5 * ATR
        # SL = 100.2 - (1.5 * 2.0) = 100.2 - 3.0 = 97.2
        print(f"Calculated SL: {row['StopLoss']} (Expected: 97.2)")
        self.assertAlmostEqual(row['StopLoss'], 97.2)
        
        # Verify Target = Entry + 2 * Risk
        # Risk = 100.2 - 97.2 = 3.0
        # Target = 100.2 + (2 * 3.0) = 106.2
        print(f"Calculated Target: {row['TargetPrice']} (Expected: 106.2)")
        self.assertAlmostEqual(row['TargetPrice'], 106.2)
        
        # 3. Mock Data for Target Hit
        # Candle 3: 09:18 - High 106.5 (Hits 106.2), Close 105.0
        # Candle 3: 03:48 UTC (09:18 IST) - High 106.5 (Hits 106.2)
        dates_target = pd.to_datetime(["2026-01-06 03:46:00", "2026-01-06 03:47:00", "2026-01-06 03:48:00"]).tz_localize('UTC')
        data_target = pd.DataFrame({
            "Open": [99.0, 99.5, 100.2],
            "High": [100.0, 100.5, 106.5],
            "Low": [99.0, 99.5, 104.0],
            "Close": [99.5, 100.2, 105.0],
            "Volume": [1000, 2000, 3000]
        }, index=dates_target)
        
        mock_download.return_value = data_target
        self.tracker.update_status()
        
        df = self.tracker.load_trades()
        row = df.iloc[0]
        
        print("Status after Target Hit:", row['Status'])
        print(f"Updated SL: {row['UpdatedStopLoss']} (Expected: {row['EntryPrice']})")
        
        # Should be OPEN (Trailing)
        self.assertEqual(row['Status'], "OPEN")
        # SL should be moved to Entry (Breakeven)
        self.assertEqual(row['UpdatedStopLoss'], row['EntryPrice'])
        # Target should be extended
        # New Target = Old Target + Risk = 106.2 + 3.0 = 109.2
        print(f"New Target: {row['TargetPrice']} (Expected: 109.2)")
        self.assertAlmostEqual(row['TargetPrice'], 109.2)

if __name__ == '__main__':
    unittest.main()
