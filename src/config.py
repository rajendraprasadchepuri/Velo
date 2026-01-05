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
