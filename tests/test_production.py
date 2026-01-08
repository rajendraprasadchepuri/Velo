import unittest
import pandas as pd
import os
import shutil
from datetime import datetime
from src.tracker import TradeTracker
from src.utils import round_to_tick, calculate_position_size

class TestProductionLogic(unittest.TestCase):
    
    def setUp(self):
        # Create a temp data directory
        self.test_dir = "tests/temp_data"
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
        
        self.test_csv_path = os.path.join(self.test_dir, "test_trades.csv")
        
        # Patch CSV_PATH constant where it is used
        from unittest.mock import patch
        self.patcher = patch('src.tracker.CSV_PATH', self.test_csv_path)
        self.patcher.start()
        
        self.tracker = TradeTracker() # Now uses patched path

    def tearDown(self):
        self.patcher.stop()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_tracker_initialization(self):
        """Verify tracker creates the CSV with correct columns."""
        self.tracker._ensure_file_exists()
        self.assertTrue(os.path.exists(self.tracker.filepath))
        df = pd.read_csv(self.tracker.filepath)
        required_cols = ["TradeID", "Ticker", "Strategy", "Status", "EntryPrice", "StopLoss", "TargetPrice"]
        for col in required_cols:
            self.assertIn(col, df.columns)

    def test_add_intraday_trade(self):
        """Verify adding an Intraday trade works and sets correct fields."""
        signal = {
            "Ticker": "TEST.NS",
            "Entry Price": 100.0,
            "Stop Loss": 95.0,
            "Target Price": 110.0,
            "Signal": "Manual | Test",
            "Side": "BUY"
        }
        success, msg = self.tracker.add_trade(signal, strategy_type="Intraday", signal_date="2025-01-01")
        self.assertTrue(success)
        
        df = self.tracker.load_trades()
        self.assertEqual(len(df), 1)
        row = df.iloc[0]
        self.assertEqual(row['Ticker'], "TEST.NS")
        self.assertEqual(row['Strategy'], "Intraday")
        self.assertEqual(row['Status'], "WAITING_ENTRY")
        self.assertEqual(row['Side'], "BUY")

    def test_add_duplicate_trade(self):
        """Verify adding the same trade twice updates it instead of duplicating."""
        signal = {
            "Ticker": "TEST.NS",
            "Entry Price": 100.0,
            "Stop Loss": 95.0,
            "Signal": "Test 1"
        }
        self.tracker.add_trade(signal, strategy_type="Intraday", signal_date="2025-01-01")
        
        # Add again with different SL
        signal2 = {
            "Ticker": "TEST.NS",
            "Entry Price": 100.0,
            "Stop Loss": 98.0, # Changed
            "Signal": "Test 2"
        }
        success, msg = self.tracker.add_trade(signal2, strategy_type="Intraday", signal_date="2025-01-01")
        
        self.assertTrue(success)
        self.assertIn("updated", msg.lower())
        
        df = self.tracker.load_trades()
        self.assertEqual(len(df), 1) # Still 1 row
        self.assertEqual(df.iloc[0]['StopLoss'], 98.0) # Updated

    def test_position_sizing(self):
        """Test the position size utility."""
        # Risk 1% of 100,000 = 1000.
        # Entry 100, SL 90. Risk/Share = 10.
        # Qty = 1000 / 10 = 100.
        qty, risk_amount = calculate_position_size(100, 90, 100000, 1.0)
        self.assertEqual(qty, 100)
        self.assertEqual(risk_amount, 1000.0)
        
        # Test Short
        # Entry 100, SL 110. Risk/Share = 10.
        qty, risk_amount = calculate_position_size(100, 110, 100000, 1.0)
        self.assertEqual(qty, 100)

    def test_rounding(self):
        """Test round_to_tick."""
        self.assertAlmostEqual(round_to_tick(100.03, 0.05), 100.05)
        self.assertAlmostEqual(round_to_tick(100.02, 0.05), 100.00)
        self.assertAlmostEqual(round_to_tick(100.07, 0.05), 100.05)

if __name__ == '__main__':
    unittest.main()
