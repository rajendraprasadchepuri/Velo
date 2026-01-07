import pandas as pd
from datetime import datetime
from src.intraday_strategy import calculate_confidence
from src.tracker import TradeTracker
from src.config import WATCHLIST
import colorama
from colorama import Fore, Style

colorama.init()

def main():
    print(f"{Fore.CYAN}--- Auto Intraday Scanner Started at {datetime.now()} ---{Style.RESET_ALL}")
    
    results = []
    all_scanned = []
    print(f"Scanning {len(WATCHLIST)} stocks...")
    
    for i, stock in enumerate(WATCHLIST):
        try:
            # UNPACKING FIX: Now captures all 11 return values including side
            # Returned: score, details, prev_day_high, pdl, prev_close, todays_high, exit_price, current_atr, trigger_high, current_vwap, side
            score, details, pdh, pdl, prev_close, todays_high, exit_price, atr, trigger_high, vwap, side = calculate_confidence(stock)
            
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
                     # Pass Scientific Metrics to Tracker
                     "ATR": atr,
                     "TriggerHigh": trigger_high,
                     "ATR": atr,
                     "TriggerHigh": trigger_high,
                     "VWAP": vwap,
                     "Side": side
                })
            
            # --- NEW LOGGING: Collect all scores for debugging ---
            all_scanned.append({"Ticker": stock, "Score": score, "Details": details})
            
            if score >= 80 and score < 90:
                 print(f"{Fore.YELLOW}[CLOSE CALL] {stock} | Score: {score} | Missing: {set(['Trend > EMA200', 'Val > VWAP', 'VSA Bull Vol', 'MACD Bull Cross', 'Price > BB Mid', 'RSI Bullish (>60)', 'Breakout > PDH']) - set(details)}{Style.RESET_ALL}")
                 print(f"Details: {details}")

            if score < 90:
                 if i % 10 == 0: print(f"Checked {i}/{len(WATCHLIST)}... (Last: {stock} @ {score})")
                
        except Exception as e:
            print(f"{Fore.RED}Error scanning {stock}: {e}{Style.RESET_ALL}")

    # --- ANALYSIS: Print Top 5 Missed Opportunities ---
    if all_scanned:
        print(f"\n{Fore.YELLOW}--- Top 5 Missed Opportunities (Score < 90) ---{Style.RESET_ALL}")
        all_scanned.sort(key=lambda x: x['Score'], reverse=True)
        for item in all_scanned[:5]:
            print(f"{item['Ticker']}: {item['Score']} | {item['Details']}")
        print("---------------------------------------------------\n")

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
