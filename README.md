# Stock Analysis & Prediction App

A comprehensive application for analyzing stock market data, sentiment from news, and predicting future prices using advanced machine learning models.

## 🚀 Features

* **Real-time Data Analysis**: Fetches live stock data for Indian markets (NSE/BSE).
* **Interactive Charts**: Visualize price history with SMA, EMA, and other technical indicators using Plotly.
* **Sentiment Analysis**: Analyzes recent news headlines to gauge market sentiment (Positive/Negative).
* **Advanced Predictions**:
  * **Random Forest & XGBoost**: Machine learning models incorporating sentiment scores.
  * **Prophet**: Facebook's time-series forecasting tool.
  * **ARIMA & Holt-Winters**: Classical statistical forecasting methods.
  * **Moving Average**: Simple baseline model.
* **Hyperparameter Tuning**: Optional automatic tuning to optimize model performance.
* **Forecast Signals**: actionable Buy/Sell/Hold signals based on projected returns.

## 🛠️ Tech Stack

* **Frontend**: Streamlit
* **Data Processing**: Pandas, NumPy
* **Visualization**: Plotly Express
* **Machine Learning**: Scikit-learn, XGBoost, Prophet, Statsmodels
* **Finance Data**: yfinance
* **Natural Language Processing**: TextBlob

## 📦 Installation

### Prerequisites

* Python 3.8 or higher
* Git

### Setup

1. **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd stock-prediction-app
    ```

2. **Create and activate a virtual environment:**

    * **Windows:**

        ```powershell
        python -m venv .venv
        .\.venv\Scripts\activate
        ```

    * **macOS/Linux:**

        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## 🚀 Usage

### Running the App (Windows Shortcut)

Simply double-click the `run_app.bat` file in the root directory.

### Running Manually

Ensure your virtual environment is activated, then run:

```bash
streamlit run app.py
```

## 📂 Project Structure

```
.
├── src/                # Source code for logic
│   ├── data_loader.py  # Data fetching functions (Stock prices, News)
│   ├── analysis.py     # Technical indicators and stats
│   ├── model.py        # ML Training and Prediction logic
│   └── sentiment.py    # News sentiment analysis
├── tests/              # Verification and debug scripts
├── app.py              # Main Streamlit application entry point
├── run_app.bat         # Windows launcher script
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```

## ⚠️ Disclaimer

This application is for internal purpose only. It is not financial advice. algorithmic predictions can be wrong. Always do your own research before investing.

Contact : Prasanna - +918851924366
        : Rajendra Prasad - +919676260340
