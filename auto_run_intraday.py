import pandas as pd
from datetime import datetime
from src.intraday_strategy import WATCHLIST, calculate_confidence
from src.tracker import TradeTracker
import colorama
from colorama import Fore, Style

colorama.init()

def main():
    print(f"{Fore.CYAN}--- Auto Intraday Scanner Started at {datetime.now()} ---{Style.RESET_ALL}")
    
    results = []
    print(f"Scanning {len(WATCHLIST)} stocks...")
    
    for i, stock in enumerate(WATCHLIST):
        try:
            score, details, pdh, pdl, prev_close, todays_high, exit_price = calculate_confidence(stock)
            
            if score >= 90:
                print(f"{Fore.GREEN}[FOUND] {stock} | Score: {score} | Entry: {todays_high}{Style.RESET_ALL}")
                results.append({
                     "Ticker": stock, 
                     "Score": score, 
                     "Details": ", ".join(details),
                     "PDH": pdh,
                     "PDL": pdl,
                     "Prev Close": prev_close,
                     "Safe Entry": todays_high,
                     "Exit Price": exit_price,
                     "Target %": "0.5%",
                })
            else:
                # Optional: Print checking status
                if i % 10 == 0: print(f"Checked {i}/{len(WATCHLIST)}...")
                
        except Exception as e:
            print(f"{Fore.RED}Error scanning {stock}: {e}{Style.RESET_ALL}")

    if not results:
        print(f"{Fore.YELLOW}No High Confidence (90+) signals found today.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.CYAN}--- Adding {len(results)} Trades to Tracker ---{Style.RESET_ALL}")
    
    tracker = TradeTracker()
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    added_count = 0
    updated_count = 0
    
    for row_dict in results:
        # Prepare signal data for add_trade
        # Remap keys to match what tracker expects if needed, or tracker handles it flexible
        # Tracker uses: 'Entry Price', 'Stop Loss' (optional), 'Target Price' (optional), 'Safe Entry' (fallback)
        
        # We pass row_dict directly as it has 'Safe Entry', 'Exit Price'
        row_dict['Entry Price'] = row_dict['Safe Entry']
        
        success, msg = tracker.add_trade(
            row_dict, 
            strategy_type="Intraday", 
            signal_date=today_str
        )
        
        if success:
            if "updated" in msg.lower():
                print(f"{Fore.BLUE}UPDATED: {row_dict['Ticker']} ({msg}){Style.RESET_ALL}")
                updated_count += 1
            else:
                print(f"{Fore.GREEN}ADDED: {row_dict['Ticker']}{Style.RESET_ALL}")
                added_count += 1
        else:
            print(f"{Fore.YELLOW}SKIPPED: {row_dict['Ticker']} ({msg}){Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}--- Summary ---{Style.RESET_ALL}")
    print(f"New Trades: {added_count}")
    print(f"Updated Trades: {updated_count}")
    print(f"Done.")

    # Keep window open for a few seconds if running via bat
    import time
    time.sleep(5)

if __name__ == "__main__":
    main()
