import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import os
import shutil
from src.tracker import TradeTracker
from src.mtf_strategy import get_ultra_precision_signal
from src.utils import round_to_tick

class TestSuite(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = "tests/temp_data"
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
        self.test_csv_path = os.path.join(self.test_dir, "test_trades.csv")
        
        # Patch CSV_PATH
        self.patcher = patch('src.tracker.CSV_PATH', self.test_csv_path)
        self.patcher.start()
        self.tracker = TradeTracker()

    def tearDown(self):
        self.patcher.stop()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_round_to_tick(self):
        # Using tolerance for float comparison
        self.assertTrue(abs(round_to_tick(100.03, 0.05) - 100.05) < 0.001)
        self.assertTrue(abs(round_to_tick(100.02, 0.05) - 100.00) < 0.001)

    def test_tracker_add_trade(self):
        signal = {"Ticker": "TEST", "Entry Price": 100, "Stop Loss": 90, "Target Price": 120, "Signal": "Test"}
        success, msg = self.tracker.add_trade(signal, strategy_type="Intraday")
        self.assertTrue(success)
        df = self.tracker.load_trades()
        self.assertEqual(len(df), 1)
        
        # Duplicate/Update
        signal2 = {"Ticker": "TEST", "Entry Price": 100, "Stop Loss": 95}
        success, msg = self.tracker.add_trade(signal2, strategy_type="Intraday")
        self.assertTrue(success)
        df = self.tracker.load_trades()
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['StopLoss'], 95.0)

    # @patch('src.mtf_strategy.yf')
    # @patch('src.mtf_strategy.fetch_data_robust')
    # def test_mtf_signal(self, mock_fetch, mock_yf):
    #     pass


if __name__ == "__main__":
    unittest.main()
