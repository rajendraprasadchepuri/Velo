from unittest.mock import patch, MagicMock
import unittest
import src.mtf_strategy as mtf 

class DebugMock(unittest.TestCase):
    @patch('src.mtf_strategy.yf')
    def test_mock(self, mock_yf):
        print(f"Mock YF: {mock_yf}")
        print(f"Mock Ticker: {mock_yf.Ticker}")
        
        # Simulate code
        ticker = mock_yf.Ticker("TEST.NS")
        print(f"Ticker Instance: {ticker}")
        
        # Assignments
        ticker.info = {'a': 1} # This is what we did in test setting mock_instance.info
        print(f"Ticker Info: {ticker.info}")
        
        # Accessing
        val = ticker.info.get('a')
        print(f"Val: {val}")

if __name__ == "__main__":
    unittest.main()
