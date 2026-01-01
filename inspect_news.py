import sys
import os
import yfinance as yf
import json

# Add current directory to path
sys.path.append(os.getcwd())

def inspect_news(ticker):
    print(f"Fetching news for {ticker}...")
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        print(f"Found {len(news)} news items.")
        if news:
            print("First news item structure:")
            print(json.dumps(news[0], indent=2))
            
            # Check for title in all items
            for i, item in enumerate(news):
                if 'title' not in item:
                    print(f"Item {i} missing 'title'. Keys: {item.keys()}")
                    if 'content' in item:
                        print(f"Content: {json.dumps(item['content'], indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_news("RELIANCE.NS")
