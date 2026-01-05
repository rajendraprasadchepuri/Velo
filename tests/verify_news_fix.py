import sys
import os
import yfinance as yf

# Add current directory to path
sys.path.append(os.getcwd())

from src.data_loader import fetch_news

def verify_news_fix(ticker):
    print(f"Fetching news for {ticker}...")
    news = fetch_news(ticker)
    print(f"Fetched {len(news)} items.")
    
    for i, item in enumerate(news):
        if 'title' not in item:
            print(f"FAIL: Item {i} still missing title!")
            print(item)
        else:
            print(f"Item {i}: {item['title'][:50]}...")

    print("Verification complete.")

if __name__ == "__main__":
    verify_news_fix("RELIANCE.NS")
