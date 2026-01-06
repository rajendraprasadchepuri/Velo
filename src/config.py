import os

def load_watchlist():
    """Loads watchlist from watchlist.txt, ignoring comments and empty lines."""
    watchlist_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'watchlist.txt')
    stocks = []
    
    if os.path.exists(watchlist_path):
        with open(watchlist_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Handle comma separated lines if user pastes a list
                    parts = [s.strip() for s in line.split(',')]
                    for p in parts:
                        if p: stocks.append(p)
    else:
        # Fallback if file missing
        return ["TATASTEEL.NS", "RELIANCE.NS", "SBIN.NS"]
        
    return sorted(list(set(stocks)))

WATCHLIST = load_watchlist()

# Limit for scanner to avoid timeouts if list gets too huge (optional, keeping strict for now)
MAX_STOCKS_TO_MONITOR = 100 
if len(WATCHLIST) > MAX_STOCKS_TO_MONITOR:
    pass

# --- SECTOR MAPPING ---
# Maps specific stocks to their Sector Index Ticker
SECTOR_MAP = {
    # Banks -> Nifty Bank
    "HDFCBANK.NS": "^NSEBANK", "ICICIBANK.NS": "^NSEBANK", "SBIN.NS": "^NSEBANK", 
    "AXISBANK.NS": "^NSEBANK", "KOTAKBANK.NS": "^NSEBANK", "INDUSINDBK.NS": "^NSEBANK",
    "BANKBARODA.NS": "^NSEBANK", "PNB.NS": "^NSEBANK", "IDFCFIRSTB.NS": "^NSEBANK",
    
    # IT -> Nifty IT
    "TCS.NS": "^CNXIT", "INFY.NS": "^CNXIT", "HCLTECH.NS": "^CNXIT", 
    "WIPRO.NS": "^CNXIT", "TECHM.NS": "^CNXIT", "LTIM.NS": "^CNXIT",
    
    # Auto -> Nifty Auto
    "MARUTI.NS": "^CNXAUTO", "TATAMOTORS.NS": "^CNXAUTO", "M&M.NS": "^CNXAUTO",
    "BAJAJ-AUTO.NS": "^CNXAUTO", "HEROMOTOCO.NS": "^CNXAUTO", "EICHERMOT.NS": "^CNXAUTO",
    
    # Metals -> Nifty Metal
    "TATASTEEL.NS": "^CNXMETAL", "HINDALCO.NS": "^CNXMETAL", "JSWSTEEL.NS": "^CNXMETAL",
    "VEDL.NS": "^CNXMETAL", "COALINDIA.NS": "^CNXMETAL", "NMDC.NS": "^CNXMETAL",
    "NATIONALUM.NS": "^CNXMETAL", "JINDALSTEL.NS": "^CNXMETAL",
    
    # FMCG -> Nifty FMCG
    "ITC.NS": "^CNXFMCG", "HUL.NS": "^CNXFMCG", "NESTLEIND.NS": "^CNXFMCG",
    "BRITANNIA.NS": "^CNXFMCG", "TATACONSUM.NS": "^CNXFMCG", "MARICO.NS": "^CNXFMCG",
    "GODREJCP.NS": "^CNXFMCG",
    
    # Pharma -> Nifty Pharma
    "SUNPHARMA.NS": "^CNXPHARMA", "CIPLA.NS": "^CNXPHARMA", "DRREDDY.NS": "^CNXPHARMA",
    "DIVISLAB.NS": "^CNXPHARMA", "APOLLOHOSP.NS": "^CNXPHARMA", "LUPIN.NS": "^CNXPHARMA",
    "AUROPHARMA.NS": "^CNXPHARMA",
    
    # Energy/Power
    "RELIANCE.NS": "^CNXENERGY", "NTPC.NS": "^CNXENERGY", "POWERGRID.NS": "^CNXENERGY",
    "ONGC.NS": "^CNXENERGY", "ADANIGREEN.NS": "^CNXENERGY", "ADANIPOWER.NS": "^CNXENERGY"
}

# Fallback for general market
MARKET_INDEX = "^NSEI" # Nifty 50
