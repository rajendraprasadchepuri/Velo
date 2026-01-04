
import yfinance as yf
import pandas as pd

def check_nifty():
    print("Downloading Nifty...")
    nifty = yf.download('^NSEI', period='1d', interval='5m', progress=False)
    if not nifty.empty:
        print(f"Columns type: {type(nifty.columns)}")
        print(f"Columns: {nifty.columns}")
        
        try:
            # Replicating the suspicious line
            close_val = nifty['Close'].iloc[-1]
            open_val = nifty['Open'].iloc[-1]
            print(f"Close value type: {type(close_val)}")
            print(f"Close value: \n{close_val}")
            
            comparison = close_val > open_val
            print(f"Comparison type: {type(comparison)}")
            print(f"Comparison: \n{comparison}")
            
            if comparison:
                print("Condition is True")
            else:
                print("Condition is False")
                
        except ValueError as e:
            print(f"CAUGHT EXPECTED ERROR: {e}")
        except Exception as e:
            print(f"CAUGHT UNEXPECTED ERROR: {e}")

if __name__ == "__main__":
    check_nifty()
