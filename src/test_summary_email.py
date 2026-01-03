import sys
import os

# Ensure we can import from current directory
sys.path.append(os.getcwd())

try:
    from notifications import send_summary_email
except ImportError:
    # Try adding src to path
    sys.path.append(os.path.join(os.getcwd(), 'src'))
    try:
        from notifications import send_summary_email
    except ImportError:
        print("Could not import notifications module.")
        sys.exit(1)

print("Constructing dummy signals for summary email...")

signals = [
    {
        "Ticker": "APOLLOHOSP.NS",
        "Industry": "Medical Care Facilities",
        "Signal": "STRONG BUY",
        "Confidence Score": 85,
        "Current Price": 7129.50,
        "Stop Loss": 6977.70,
        "Target Price": 7433.10,
        "Est. Days": "5-8 Days",
        "Reasoning": "Short-term Trend: Price > EMA20, Ideal Momentum",
        "Fundamental Rating": "💎 Premium",
        "Market Cap": 102511000000,
        "P/E Ratio": 61.35,
        "P/B Ratio": 11.27,
        "ROE": 0.20,
        "Dividend Yield": 0.0028,
        "Operating Margin": 0.11
    }
]

print(f"Sending summary email to multiple recipients...")
send_summary_email(signals)
