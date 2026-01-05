import yfinance as yf
import pandas as pd

df = yf.download('UPL.NS', period='1d', progress=False)
with open("debug_upl.txt", "w") as f:
    f.write(str(df.columns) + "\n")
    f.write(str(df) + "\n")
    if not df.empty:
        f.write("First Row:\n")
        f.write(str(df.iloc[0]) + "\n")
