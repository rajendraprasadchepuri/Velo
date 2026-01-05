import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_summary_email(signals):
    if not signals:
        print("No signals to send.")
        return

    sender = "vizlesana@gmail.com"
    password = "eojxtohufkoxlqnp"
    receivers = [
    "rajendraprasadchepuri@gmail.com",
    #"gprasannakumar798@gmail.com"
]
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    subject = f"Velo - MTF Strategy Results {date_str} AutoSent"

    # HTML CSS Styles
    style = """
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f8; color: #333; margin: 0; padding: 20px; }
        h2 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 8px; margin-top: 30px; font-size: 24px; }
        
        table { width: 100%; border-collapse: collapse; margin-bottom: 30px; background-color: #ffffff; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; }
        
        th { background-color: #2c3e50; color: #ffffff; padding: 12px 15px; text-align: left; font-weight: 600; text-transform: uppercase; font-size: 13px; letter-spacing: 0.5px; }
        td { padding: 12px 15px; border-bottom: 1px solid #eeeeee; color: #444; font-size: 14px; }
        
        tr:nth-child(even) { background-color: #f9fafc; }
        tr:hover { background-color: #f1f4f8; }
        
        .buy { color: #27ae60; font-weight: bold; background-color: #e8f8f5; padding: 4px 8px; border-radius: 4px; display: inline-block; }
        .strong-buy { color: #ffffff; font-weight: bold; background-color: #27ae60; padding: 4px 8px; border-radius: 4px; display: inline-block; }
        
        .confidence-bar { height: 8px; background-color: #e0e0e0; border-radius: 4px; overflow: hidden; display: inline-block; width: 70px; vertical-align: middle; margin-right: 8px; }
        .confidence-fill { height: 100%; background-color: #e74c3c; border-radius: 4px; } 
        
        /* Fundamental Ratings - Badges */
        .trend-premium { color: #fff; background-color: #8e44ad; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
        .trend-strong { color: #fff; background-color: #27ae60; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
        .trend-neutral { color: #856404; background-color: #fff3cd; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
        .trend-weak { color: #721c24; background-color: #f8d7da; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    </style>
    """

    # constructing Table 1: Scanner Results
    table1_rows = ""
    for s in signals:
        signal_class = "strong-buy" if "STRONG" in s['Signal'] else "buy"
        conf = s['Confidence Score']
        # Styling confidence bar color based on score if we wanted, but image had red. sticking to red/gradient.
        
        table1_rows += f"""
        <tr>
            <td>{s.get('Date', datetime.now().strftime('%Y-%m-%d'))}</td>
            <td>{s['Ticker']}</td>
            <td>{s['Industry']}</td>
            <td class="{signal_class}">{s['Signal']}</td>
            <td>
                <div class="confidence-bar"><div class="confidence-fill" style="width: {conf}%;"></div></div> {conf}%
            </td>
            <td>₹{s['Current Price']}</td>
            <td>₹{s['Entry Price']}</td>
            <td>₹{s['Stop Loss']}</td>
            <td>₹{s['Target Price']}</td>
            <td>{s['Est. Days']}</td>
            <td>{s['Reasoning'].split(',')[0]}...</td>
        </tr>
        """

    # constructing Table 2: Fundamental Analysis
    table2_rows = ""
    for s in signals:
        rating = s['Fundamental Rating']
        rating_class = "trend-neutral"
        if "Premium" in rating: rating_class = "trend-premium"
        elif "Strong" in rating: rating_class = "trend-strong"
        elif "Weak" in rating: rating_class = "trend-weak"

        market_cap = f"₹{s['Market Cap']/10000000:.0f} Cr" if s['Market Cap'] else "N/A"
        pe = round(s['P/E Ratio'], 2) if s['P/E Ratio'] else "N/A"
        pb = round(s['P/B Ratio'], 2) if s['P/B Ratio'] else "N/A"
        roe = f"{round(s['ROE']*100, 2)}%" if s['ROE'] else "N/A"
        p_div = f"{round(s['Dividend Yield']*100, 2)}%" if s['Dividend Yield'] else "N/A"
        op_margin = f"{round(s['Operating Margin']*100, 2)}%" if s['Operating Margin'] else "N/A"

        table2_rows += f"""
        <tr>
            <td>{s['Ticker']}</td>
            <td class="{rating_class}">{rating}</td>
            <td>{market_cap}</td>
            <td>{pe}</td>
            <td>{pb}</td>
            <td>{roe}</td>
            <td>{p_div}</td>
            <td>{op_margin}</td>
        </tr>
        """

    html_content = f"""
    <html>
    <head>{style}</head>
    <body>
        <h2>Scanner Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Stock Symbol</th>
                    <th>Sector</th>
                    <th>Trade Signal</th>
                    <th>Confidence</th>
                    <th>Current Price</th>
                    <th>Entry Price</th>
                    <th>Stop Loss</th>
                    <th>Target Price</th>
                    <th>Timeframe</th>
                    <th>Analysis</th>
                </tr>
            </thead>
            <tbody>
                {table1_rows}
            </tbody>
        </table>

        <h2>Fundamental Analysis</h2>
        <table>
            <thead>
                <tr>
                    <th>Stock Symbol</th>
                    <th>Trend</th>
                    <th>Market Cap</th>
                    <th>P/E</th>
                    <th>P/B</th>
                    <th>ROE</th>
                    <th>Div Yield</th>
                    <th>Op Margin</th>
                </tr>
            </thead>
            <tbody>
                {table2_rows}
            </tbody>
        </table>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = ", ".join(receivers)
    msg["Subject"] = subject
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        print(f"Summary email sent with {len(signals)} signals.")
    except Exception as e:
        print(f"Failed to send summary email: {e}")
