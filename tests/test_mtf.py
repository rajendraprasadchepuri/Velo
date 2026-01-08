import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from src.mtf_strategy import get_ultra_precision_signal, run_pro_scanner

class TestMTFStrategy(unittest.TestCase):

    def get_mock_df(self, trend="bullish"):
        # Create 100 periods of data
        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
        data = {
            "Open": np.linspace(100, 200, 100),
            "High": np.linspace(102, 202, 100),
            "Low": np.linspace(98, 198, 100),
            "Close": np.linspace(101, 201, 100), # Up trend
            "Volume": np.random.randint(1000, 5000, 100)
        }
        if trend == "bearish":
            data["Close"] = np.linspace(200, 100, 100)
            data["Open"] = np.linspace(200, 100, 100)
            
        df = pd.DataFrame(data, index=dates)
        return df

    @patch('src.mtf_strategy.yf')
    @patch('src.mtf_strategy.fetch_data_robust')
    def test_signal_bullish(self, mock_fetch, mock_yf):
        # Setup specific mock data for a Strong Buy
        df = self.get_mock_df(trend="bullish")
        
        # Make fundamentals decent
        mock_instance = mock_yf.Ticker.return_value
        mock_instance.info = {
            'industry': 'Tech', 
            'returnOnEquity': 0.2, 
            'operatingMargins': 0.15,
            'trailingPE': 20
        }
        
        mock_fetch.return_value = df
        
        # Test basic signal generation
        # We need Nifty for RS check, passing None skips RS or treats validly?
        # get_ultra_precision_signal(ticker, nifty_df=None)
        
        result = get_ultra_precision_signal("TEST.NS", nifty_df=None)
        
        self.assertIsNotNone(result)
        self.assertIn(result['Signal'], ["BUY", "STRONG BUY"])
        self.assertTrue(result['Confidence Score'] > 0)
        self.assertIn("Bullish Trend", result['Reasoning'])

    @patch('src.mtf_strategy.yf')
    @patch('src.mtf_strategy.fetch_data_robust')
    def test_run_scanner_regime_filtering(self, mock_fetch, mock_yf):
        # MOCK NIFTY: Bearish
        nifty_df = self.get_mock_df(trend="bearish")
        # Ensure EMA50 > Close (Bearish)
        # linear drop 200->100. Average is higher than current.
        
        # MOCK STOCK: Bullish
        stock_df = self.get_mock_df(trend="bullish") # Should score high naturally
        
        # Side effect: first call Nifty, second call Stock
        mock_fetch.side_effect = [nifty_df, stock_df, stock_df, stock_df] 
        
        # Also need to mock Ticker info to avoid None errors
        mock_instance = mock_yf.Ticker.return_value
        mock_instance.info = {'industry': 'Tech'}
        
        # Run scanner with 1 stock
        with patch('src.mtf_strategy.WATCHLIST', ["TEST.NS"]):
             results, warnings = run_pro_scanner()
             
             # Verify finding
             # Market Regime is Bearish.
             # Analysis score should be high, but logic says:
             # if not market_bullish: if score < 90 or RS < 0: score = 0.
             
             # Our mock bullish stock might not have RS calculated (nifty vs stock).
             # It calculates RS inside if nifty_df passed.
             # If RS < 0, it gets suppressed.
             
             self.assertTrue(len(results) > 0)
             res = results[0]
             
             # Check if it was processed
             # If our mock data yields > 90 and positive RS, it stays. 
             # If not, it becomes suppressed.
             
             self.assertIn("Market Regime Filter Active", warnings[0])

if __name__ == '__main__':
    unittest.main()
