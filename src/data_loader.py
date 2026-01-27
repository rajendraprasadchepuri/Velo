import yfinance as yf
import pandas as pd
import streamlit as st

@st.cache_data(ttl=300) # Cache for 5 minutes
def fetch_stock_data(ticker, period="max"):
    """
    Fetches historical stock data from yfinance.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        return hist
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()

def fetch_news(ticker):
    """
    Fetches news for a given ticker using yfinance.
    Returns a list of dictionaries with 'title', 'link', 'publisher', 'providerPublishTime'.
    """
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        
        # Filter and normalize
        valid_news = []
        for item in news:
            title = item.get('title')
            link = item.get('link')
            publisher = item.get('publisher')
            pub_time = item.get('providerPublishTime')
            
            # Check content if top-level missing
            if not title and 'content' in item:
                content = item['content']
                title = content.get('title')
                
                if not link:
                    link = content.get('clickThroughUrl')
                    if isinstance(link, dict):
                        link = link.get('url')
                
                if not publisher:
                    publisher = content.get('provider', {}).get('displayName')
                
                if not pub_time:
                    pub_time = content.get('pubDate')

            if title and link:
                valid_news.append({
                    'title': title,
                    'link': link,
                    'publisher': publisher or 'Unknown',
                    'providerPublishTime': pub_time or 0
                })
        
        return valid_news
    except Exception as e:
        print(f"Error fetching news for {ticker}: {e}")
        return []

@st.cache_data(ttl=3000) # Cache for 50 Mins
def fetch_benchmark(period="max", ticker="^NSEI"):
    """
    Fetches historical data for a benchmark index (default Nifty 50).
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        return hist
    except Exception as e:
        print(f"Error fetching benchmark {ticker}: {e}")
        return pd.DataFrame()
