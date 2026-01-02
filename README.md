# Stock Analysis & Prediction App

A comprehensive application for analyzing stock market data, sentiment from news, forecasting future prices, and discovering high-probability trades using advanced strategies.

## 🚀 Key Features

### 1. Ultra-Precision MTF Strategy (New!)
A specialized scanner designed for **Margin Trading Facility (MTF)** and high-conviction swing trades.
*   **Four-Pillar Technical Logic**:
    *   **Trend**: Price > EMA20 > EMA50 (Bullish Alignment).
    *   **Momentum**: RSI between 50-75 (Sweet spot).
    *   **Strength**: ADX > 25 (Strong Trend).
    *   **Volume**: Rising Volume Price Trend (VPT) indicating institutional flow.
*   **Fundamental Guardrails**:
    *   **Real-time Metrics**: Market Cap, P/E, ROE, Operating Margins.
    *   **Smart Ratings**:
        *   ✅ **Strong**: Profitable (ROE > 15%, Margin > 10%) & Reasonable Price.
        *   💎 **Premium**: Great Fundamentals but Expensive (P/E > 60).
        *   ❌ **Weak**: Weak Fundamentals.
*   **Dynamic Risk Management**:
    *   **Stop Loss**: Calculated using 1.5x ATR.
    *   **Targets**: Calculated using 3.0x ATR.
    *   **Timeframe**: Velocity-based time estimation for targets.

### 2. Advanced Predictions & ML
*   **Ensemble Models**: Random Forest & XGBoost incorporating sentiment analysis.
*   **Forecasting**: Facebook Prophet & ARIMA for time-series projections.
*   **Sentiment Analysis**: Natural Language Processing (TextBlob) on news headlines to gauge market mood.

### 3. Interactive Analysis
*   **Real-time Data**: Live data for NSE/BSE stocks via `yfinance`.
*   **Interactive Charts**: Zoomable Plotly charts with SMA, EMA, and bands.
*   **Backtesting**: Built-in engine to test strategy performance on historical data.

---

## 🛠️ Tech Stack

*   **Frontend**: Streamlit
*   **Data Processing**: Pandas, NumPy
*   **Visualization**: Plotly Express
*   **Machine Learning**: Scikit-learn, XGBoost, Prophet, Statsmodels
*   **Finance Data**: yfinance
*   **Sentiment Analysis**: TextBlob

---

## 📦 Installation

### Prerequisites

*   Python 3.8 or higher
*   Git

### Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd stock-prediction-app
    ```

2.  **Create and activate a virtual environment:**
    *   **Windows:**
        ```powershell
        python -m venv .venv
        .\.venv\Scripts\activate
        ```
    *   **macOS/Linux:**
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

---

## 🚀 Usage

### Running the App
Run the following command in your terminal:

```bash
streamlit run app.py
```

Navigate to the **MTF Strategy** page from the sidebar to use the new scanner.

---

## 📂 Project Structure

```
.
├── src/
│   ├── data_loader.py    # standard data fetching
│   ├── mtf_strategy.py   # Advanced logic for MTF Scanner & Backtesting
│   ├── analysis.py       # Technical indicators
│   ├── model.py          # ML Training logic
│   └── sentiment.py      # News sentiment
├── pages/
│   └── MTF_Strategy.py   # UI for the MTF Scanner
├── app.py                # Main Dashboard
├── requirements.txt      # Dependencies
└── README.md             # Documentation
```

---

## ⚠️ Disclaimer

This application is for educational and internal purposes only. It is **not financial advice**. Algorithmic predictions and scanners can be wrong. Always do your own due diligence before investing.

### Contact
*   **Prasanna**: +91 88519 24366
*   **Rajendra Prasad**: +91 96762 60340
