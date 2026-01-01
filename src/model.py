import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error

def prepare_features(df, sentiment_score=0):
    """
    Prepares features for the model including lags and rolling stats.
    """
    data = df.copy()
    
    # Base technical indicators
    feature_cols = ['RSI', 'MACD', 'MACD_Signal', 'BB_High', 'BB_Low', 'SMA_50', 'EMA_20', 'Daily_Return', 'ATR', 'Stoch_K', 'Stoch_D', 'OBV']
    
    # Add Market Context features if available
    if 'Beta' in data.columns:
        feature_cols.extend(['Beta', 'Relative_Return', 'Market_Return'])
        
    # Add Seasonality Features
    data['DayOfWeek'] = data.index.dayofweek
    data['Month'] = data.index.month
    feature_cols.extend(['DayOfWeek', 'Month'])
    
    # Add Lag Features (Past 3 days)
    for lag in range(1, 4):
        data[f'Close_Lag_{lag}'] = data['Close'].shift(lag)
        feature_cols.append(f'Close_Lag_{lag}')
        
    # Add Rolling Features
    data['Rolling_Mean_5'] = data['Close'].rolling(window=5).mean()
    data['Rolling_Std_5'] = data['Close'].rolling(window=5).std()
    feature_cols.extend(['Rolling_Mean_5', 'Rolling_Std_5'])
    
    # Fill NaNs created by indicators and lags
    data = data.dropna()
    
    # Add sentiment
    data['Sentiment'] = sentiment_score
    
    # Target: Next day's Daily Return (instead of Close)
    # This makes the target stationary and solves the extrapolation problem
    data['Target'] = data['Daily_Return'].shift(-1)
    
    data = data.dropna()
    
    # We return the full data so we can access 'Close' for price reconstruction
    return data, feature_cols

def tune_hyperparameters(X_train, y_train, model_type="Random Forest"):
    """
    Performs RandomizedSearchCV to find better hyperparameters.
    """
    from sklearn.model_selection import RandomizedSearchCV
    
    if model_type == "Random Forest":
        param_dist = {
            'n_estimators': [100, 200, 300],
            'max_depth': [None, 10, 20, 30],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4]
        }
        model = RandomForestRegressor(random_state=42)
        
    elif model_type == "XGBoost":
        from xgboost import XGBRegressor
        param_dist = {
            'n_estimators': [100, 200, 300],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'max_depth': [3, 5, 7, 9],
            'subsample': [0.6, 0.8, 1.0],
            'colsample_bytree': [0.6, 0.8, 1.0]
        }
        model = XGBRegressor(random_state=42)
    else:
        return None

    search = RandomizedSearchCV(model, param_distributions=param_dist, n_iter=10, cv=3, scoring='neg_mean_absolute_percentage_error', n_jobs=-1, random_state=42)
    search.fit(X_train, y_train)
    return search.best_estimator_, search.best_params_

def train_model(df, sentiment_score=0, tune=False):
    """
    Trains a Random Forest Regressor.
    """
    data, feature_cols = prepare_features(df, sentiment_score)
    
    if len(data) < 50:
        return None, {"error": "Not enough data to train model"}, None
    
    split = int(len(data) * 0.8)
    train_data = data.iloc[:split]
    test_data = data.iloc[split:]
    
    X_train = train_data[feature_cols + ['Sentiment']]
    y_train = train_data['Target'] # This is now Return
    
    X_test = test_data[feature_cols + ['Sentiment']]
    y_test_return = test_data['Target'] # This is Return
    
    best_params = None
    if tune:
        model, best_params = tune_hyperparameters(X_train, y_train, "Random Forest")
    else:
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
    
    # Predict Returns
    pred_returns = model.predict(X_test)
    
    # Reconstruct Prices for Evaluation
    # Predicted_Price = Current_Close * (1 + Predicted_Return)
    # Note: test_data['Close'] is the Current Close (t), Target is Return (t+1)
    current_close = test_data['Close']
    predicted_prices = current_close * (1 + pred_returns)
    
    # Actual Prices
    # We can use the calculated target return to reconstruct, or just shift Close back?
    # Actually, Target was shift(-1). So Actual Price (t+1) is available in original df.
    # But simpler: Actual_Price = Current_Close * (1 + Actual_Return)
    actual_prices = current_close * (1 + y_test_return)
    
    mape = mean_absolute_percentage_error(actual_prices, predicted_prices)
    
    metrics = {"MAPE": mape, "Test Size": len(test_data)}
    if best_params:
        metrics["Best Params"] = best_params
        
    return model, metrics, (actual_prices, predicted_prices)

def train_xgboost_model(df, sentiment_score=0, tune=False):
    """
    Trains an XGBoost Regressor.
    """
    try:
        from xgboost import XGBRegressor
    except ImportError:
        return None, {"error": "XGBoost not installed"}, None

    data, feature_cols = prepare_features(df, sentiment_score)
    
    if data.empty or len(data) < 30:
        return None, {"error": "Not enough data to train XGBoost"}, None
    
    split = int(len(data) * 0.8)
    train_data = data.iloc[:split]
    test_data = data.iloc[split:]
    
    X_train = train_data[feature_cols + ['Sentiment']]
    y_train = train_data['Target']
    
    X_test = test_data[feature_cols + ['Sentiment']]
    y_test_return = test_data['Target']
    
    best_params = None
    if tune:
        model, best_params = tune_hyperparameters(X_train, y_train, "XGBoost")
    else:
        model = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
        model.fit(X_train, y_train)
    
    pred_returns = model.predict(X_test)
    
    # Reconstruct Prices
    current_close = test_data['Close']
    predicted_prices = current_close * (1 + pred_returns)
    actual_prices = current_close * (1 + y_test_return)
    
    mape = mean_absolute_percentage_error(actual_prices, predicted_prices)
    
    metrics = {"MAPE": mape, "Test Size": len(test_data)}
    if best_params:
        metrics["Best Params"] = best_params
        
    return model, metrics, (actual_prices, predicted_prices)

def train_prophet_model(df, tune=False):
    """
    Trains a Prophet model.
    """
    try:
        from prophet import Prophet
    except ImportError:
        return None, {"error": "Prophet not installed"}, None

    # Prophet requires 'ds' and 'y' columns
    data = df.reset_index()[['Date', 'Close']]
    data.columns = ['ds', 'y']
    
    # Remove timezone info if present (Prophet can be picky)
    if data['ds'].dt.tz is not None:
        data['ds'] = data['ds'].dt.tz_localize(None)

    if len(data) < 30:
        return None, {"error": "Not enough data for Prophet"}, None

    split = int(len(data) * 0.8)
    train = data.iloc[:split]
    test = data.iloc[split:]
    
    best_params = None
    
    if tune:
        # Simple Grid Search
        param_grid = {
            'changepoint_prior_scale': [0.05, 0.1, 0.5],
            'seasonality_prior_scale': [1.0, 10.0]
        }
        
        best_mape = float('inf')
        best_model_params = {}
        
        # Use a validation split from training data
        val_split = int(len(train) * 0.8)
        val_train = train.iloc[:val_split]
        val_test = train.iloc[val_split:]
        
        import itertools
        keys, values = zip(*param_grid.items())
        for v in itertools.product(*values):
            params = dict(zip(keys, v))
            
            m = Prophet(daily_seasonality=True, **params)
            m.fit(val_train)
            
            future = m.make_future_dataframe(periods=len(val_test))
            forecast = m.predict(future)
            preds = forecast.iloc[val_split:]['yhat'].values
            
            # Handle length mismatch
            min_len = min(len(preds), len(val_test))
            score = mean_absolute_percentage_error(val_test['y'].values[:min_len], preds[:min_len])
            
            if score < best_mape:
                best_mape = score
                best_model_params = params
        
        best_params = best_model_params
        model = Prophet(daily_seasonality=True, **best_params)
    else:
        model = Prophet(daily_seasonality=True)
        
    model.fit(train)
    
    future = model.make_future_dataframe(periods=len(test))
    forecast = model.predict(future)
    
    # Extract predictions for test set
    predictions = forecast.iloc[split:]['yhat'].values
    y_test = test['y'].values
    
    if len(predictions) != len(y_test):
        # Handle potential length mismatch if future dataframe logic differs
        min_len = min(len(predictions), len(y_test))
        predictions = predictions[:min_len]
        y_test = y_test[:min_len]

    mse = mean_squared_error(y_test, predictions)
    mape = mean_absolute_percentage_error(y_test, predictions)
    
    metrics = {"MAPE": mape, "Test Size": len(y_test)}
    if best_params:
        metrics["Best Params"] = best_params
    
    # Convert to Series with Index
    # 'test' dataframe has the index (Date) because we split 'data' which had 'ds'
    # Wait, 'data' was reset_index(). 'test' has integer index relative to 'data'.
    # We need to recover the original dates.
    # 'df' passed in has Date index.
    # The 'test' slice corresponds to the end of 'df'.
    
    test_dates = df.index[-len(y_test):]
    
    y_test_series = pd.Series(y_test, index=test_dates)
    predictions_series = pd.Series(predictions, index=test_dates)
    
    return model, metrics, (y_test_series, predictions_series)

def train_arima_model(df, tune=False):
    """
    Trains an ARIMA/SARIMA model.
    Uses statsmodels.tsa.statespace.sarimax.SARIMAX.
    """
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
    except ImportError:
        return None, {"error": "statsmodels not installed"}, None

    # ARIMA works on univariate series
    data = df['Close'].asfreq('B') # Business day frequency
    data = data.fillna(method='ffill')
    
    if len(data) < 50:
        return None, {"error": "Not enough data for ARIMA"}, None

    split = int(len(data) * 0.8)
    train = data.iloc[:split]
    test = data.iloc[split:]
    
    best_params = None
    order = (1, 1, 1)
    
    if tune:
        # Simple Grid Search for Order
        import itertools
        p = d = q = range(0, 2) # 0, 1
        pdq = list(itertools.product(p, d, q))
        
        best_aic = float('inf')
        best_order = (1, 1, 1)
        
        for param in pdq:
            try:
                temp_model = SARIMAX(train, order=param, seasonal_order=(0, 0, 0, 0), enforce_stationarity=False, enforce_invertibility=False)
                results = temp_model.fit(disp=False)
                if results.aic < best_aic:
                    best_aic = results.aic
                    best_order = param
            except:
                continue
        
        order = best_order
        best_params = {"order": order}
    
    # Train final model
    model = SARIMAX(train, order=order, seasonal_order=(0, 0, 0, 0))
    model_fit = model.fit(disp=False)
    
    predictions = model_fit.forecast(steps=len(test))
    
    # Align indices
    predictions = pd.Series(predictions, index=test.index)
    
    mape = mean_absolute_percentage_error(test, predictions)
    
    metrics = {"MAPE": mape, "Test Size": len(test)}
    if best_params:
        metrics["Best Params"] = best_params
        
    return model_fit, metrics, (test, predictions)

def train_holtwinters_model(df, tune=False):
    """
    Trains a Holt-Winters Exponential Smoothing model.
    """
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
    except ImportError:
        return None, {"error": "statsmodels not installed"}, None

    data = df['Close'].asfreq('B')
    data = data.fillna(method='ffill')
    
    if len(data) < 50:
        return None, {"error": "Not enough data for Holt-Winters"}, None

    split = int(len(data) * 0.8)
    train = data.iloc[:split]
    test = data.iloc[split:]
    
    # Additive trend, no seasonality (stocks usually don't have fixed period seasonality like retail sales)
    # Statsmodels automatically optimizes parameters during fit()
    model = ExponentialSmoothing(train, trend='add', seasonal=None)
    model_fit = model.fit()
    
    predictions = model_fit.forecast(steps=len(test))
    
    mape = mean_absolute_percentage_error(test, predictions)
    
    metrics = {"MAPE": mape, "Test Size": len(test)}
    
    if tune:
        # Extract optimized parameters
        params = model_fit.params
        # Filter for relevant ones
        best_params = {k: v for k, v in params.items() if k in ['smoothing_level', 'smoothing_trend', 'smoothing_seasonal', 'damping_trend']}
        metrics["Best Params"] = best_params
    
    return model_fit, metrics, (test, predictions)

def train_moving_average_model(df, window=20, tune=False):
    """
    Simple Moving Average Forecast.
    """
    data = df['Close']
    
    if tune:
        # Simple window tuning
        best_mape = float('inf')
        best_window = 20
        
        split = int(len(data) * 0.8)
        train = data.iloc[:split]
        test = data.iloc[split:]
        
        for w in [10, 20, 50, 100]:
            if len(train) < w: continue
            sma = train.rolling(window=w).mean().iloc[-1]
            preds = np.full(len(test), sma)
            score = mean_absolute_percentage_error(test, preds)
            if score < best_mape:
                best_mape = score
                best_window = w
        window = best_window
    
    if len(data) < window:
        return None, {"error": "Not enough data for MA"}, None

    split = int(len(data) * 0.8)
    train = data.iloc[:split]
    test = data.iloc[split:]
    
    # Calculate SMA on training data
    sma = train.rolling(window=window).mean().iloc[-1]
    
    # Predict flat line
    predictions = np.full(len(test), sma)
    
    mape = mean_absolute_percentage_error(test, predictions)
    
    metrics = {"MAPE": mape, "Test Size": len(test)}
    if tune:
        metrics["Best Params"] = {"window": window}
    
    # We return the scalar SMA value as the "model"
    return sma, metrics, (test, predictions)

def predict_next_day(model, df, sentiment_score=0, model_type="Random Forest"):
    """
    Predicts the next day's price.
    """
    if model_type == "Prophet":
        future = model.make_future_dataframe(periods=1)
        forecast = model.predict(future)
        return forecast.iloc[-1]['yhat']
        
    # Select last row
    last_row_features = data.iloc[-1:][feature_cols]
    
    prediction = model.predict(last_row_features)
    return prediction[0]

def predict_future(model, df, days=30, sentiment_score=0, model_type="Random Forest"):
    """
    Predicts stock prices for the next 'days' days.
    """
    future_predictions = []
    
    if model_type == "Prophet":
        future = model.make_future_dataframe(periods=days)
        forecast = model.predict(future)
        # Return last 'days' predictions
        return forecast.iloc[-days:]['yhat'].values
        
    if model_type == "ARIMA" or model_type == "Holt-Winters":
        # statsmodels forecast
        forecast = model.forecast(steps=days)
        return forecast.values
        
    if model_type == "Moving Average":
        # model is the scalar SMA value
        return np.full(days, model)
        
    # Recursive Forecasting for RF/XGBoost
    # We need to append predictions to df and re-calculate features for the next step
    # To avoid modifying the original df, we work on a copy
    # However, re-calculating ALL indicators on a growing DF is slow.
    # For efficiency in this demo, we will append the prediction and re-calc.
    
    current_df = df.copy()
    
    # We need to ensure 'Date' index extends into the future for seasonality features
    last_date = current_df.index[-1]
    
    for i in range(days):
        next_date = last_date + pd.Timedelta(days=1)
        
        # Prepare features for the LAST row of current_df
        # We reuse the logic from predict_next_day but adapted for the loop
        
        # 1. Re-calc indicators (needed for lags and rolling to update)
        # In a highly optimized production system, we would update incrementally.
        # Here, we re-calc on the whole history + new predictions.
        
        # Note: We need to handle the fact that we don't have High/Low/Volume for the future.
        # Assumption: High/Low/Open are same as Close (or we project them).
        # This is a limitation of recursive forecasting with complex features.
        # Simplified assumption: Next Open/High/Low/Close = Predicted Close.
        
        # We can't easily re-calc complex indicators like ATR/Stoch without High/Low.
        # Strategy: We will assume High=Low=Close=Predicted for future steps.
        # This will dampen volatility indicators (ATR -> 0), which is expected for a mean forecast.
        
        # Re-calculate indicators
        # We need to import here to avoid circular dependency if moved, 
        # but better to assume functions are available or pass them.
        # For now, we assume 'current_df' has columns. We need to append a new row.
        
        # Actually, calling 'prepare_features' or 'calculate_technical_indicators' inside the loop 
        # requires the full DF.
        
        # Let's do a simplified approach:
        # Extract the last row's features.
        # Predict.
        # Create a new row with that prediction.
        # Append to DF.
        # Re-calculate indicators on the new DF.
        
        # To make this work with 'calculate_technical_indicators', we need High, Low, Volume.
        # We will forward-fill Volume, and set High=Low=Close=Prediction.
        
        # 1. Predict next step using current tail
        
        # Prepare data for prediction
        # We need to calculate features on the EXTENDED dataframe (current_df)
        # But calculating everything is slow.
        # We can implement a mini-feature-calc here or just use the full calc.
        # Given the error, let's use the full calc but optimize if needed.
        
        # We need to re-calculate indicators because lags/rolling depend on the new row
        # But we can't calculate indicators for the *next* step until we have the *current* step's price.
        # Wait, the loop is:
        # 1. Use history to predict T+1
        # 2. Add T+1 to history
        # 3. Use history+T+1 to predict T+2
        
        # The error happened because I tried to access 'Close_Lag_1' etc. from 'data' 
        # but 'data' was just a copy of 'current_df' which MIGHT NOT have had those columns 
        # if 'calculate_technical_indicators' wasn't called or if they were dropped.
        
        # In the first iteration, 'current_df' is 'df', which HAS indicators.
        # But 'df' might have NaNs dropped? No, 'df' passed to this function usually has indicators.
        
        # Let's ensure we calculate features for the last row.
        # We can manually calculate the specific features needed for the last row 
        # to avoid full re-calc overhead and potential NaN issues.
        
        # Manual Feature Calculation for the last row of 'current_df'
        last_idx = current_df.index[-1]
        
        # Lags
        lag_1 = current_df['Close'].iloc[-1]
        lag_2 = current_df['Close'].iloc[-2]
        lag_3 = current_df['Close'].iloc[-3]
        
        # Rolling (window=5)
        roll_mean_5 = current_df['Close'].tail(5).mean()
        roll_std_5 = current_df['Close'].tail(5).std()
        
        # Indicators (RSI, MACD, etc) are already in current_df for the last row 
        # IF we called calculate_technical_indicators at the end of loop.
        # For the first iteration, they are there.
        
        # Construct single-row DataFrame for prediction
        X_next = pd.DataFrame(index=[last_idx])
        
        # Copy existing indicators from the last row of current_df
        # We assume these columns exist in current_df
        base_cols = ['RSI', 'MACD', 'MACD_Signal', 'BB_High', 'BB_Low', 'SMA_50', 'EMA_20', 'Daily_Return', 'ATR', 'Stoch_K', 'Stoch_D', 'OBV']
        for col in base_cols:
            X_next[col] = current_df[col].iloc[-1]
            
        # Add Lags & Rolling (manually calculated to be safe)
        X_next['Close_Lag_1'] = lag_1
        X_next['Close_Lag_2'] = lag_2
        X_next['Close_Lag_3'] = lag_3
        X_next['Rolling_Mean_5'] = roll_mean_5
        X_next['Rolling_Std_5'] = roll_std_5
        
        # Add Sentiment & Seasonality
        X_next['Sentiment'] = sentiment_score
        X_next['DayOfWeek'] = next_date.dayofweek
        X_next['Month'] = next_date.month
        
        # Market Context (Forward fill)
        if 'Beta' in current_df.columns:
            X_next['Beta'] = current_df['Beta'].iloc[-1]
            X_next['Relative_Return'] = current_df['Relative_Return'].iloc[-1]
            X_next['Market_Return'] = current_df['Market_Return'].iloc[-1]
            
        # Ensure column order matches training
        # We need to know the exact columns used in training.
        # We can infer from the keys we just set.
        feature_cols = ['RSI', 'MACD', 'MACD_Signal', 'BB_High', 'BB_Low', 'SMA_50', 'EMA_20', 'Daily_Return', 'ATR', 'Stoch_K', 'Stoch_D', 'OBV', 
                        'Close_Lag_1', 'Close_Lag_2', 'Close_Lag_3', 'Rolling_Mean_5', 'Rolling_Std_5', 'Sentiment', 'DayOfWeek', 'Month']
        
        if 'Beta' in current_df.columns:
            feature_cols.extend(['Beta', 'Relative_Return', 'Market_Return'])
            
        # Reorder columns to match feature_cols exactly
        # Note: If training used a different order, this might still fail if we don't know that order.
        # But 'prepare_features' defines the order, and we are using the same list here.
        # Ideally, the model object should store feature names, but sklearn RF doesn't always make it easy to access in a standard way across versions without feature_names_in_
        
        # Check if model has feature_names_in_ (sklearn > 1.0)
        if hasattr(model, "feature_names_in_"):
             X_next = X_next[model.feature_names_in_]
        else:
             # Fallback to our hardcoded list
             X_next = X_next[feature_cols]
        
        # Predict Return
        next_return = model.predict(X_next)[0]
        
        # Reconstruct Price
        # Next_Price = Last_Close * (1 + Next_Return)
        last_close = current_df['Close'].iloc[-1]
        next_price = last_close * (1 + next_return)
        
        future_predictions.append(next_price)
        
        # 2. Append new row to current_df
        new_row = pd.DataFrame({
            'Open': [next_price],
            'High': [next_price],
            'Low': [next_price],
            'Close': [next_price],
            'Volume': [current_df['Volume'].iloc[-1]] # Forward fill volume
        }, index=[next_date])
        
        # Forward fill other columns to avoid NaNs in next iteration's base indicators
        # (This is an approximation. Ideally we re-calc indicators)
        for col in current_df.columns:
            if col not in new_row.columns:
                new_row[col] = current_df[col].iloc[-1]
                
        current_df = pd.concat([current_df, new_row])
        
        # 3. Re-calculate indicators?
        # Re-calculating full indicators is slow and might introduce NaNs if not careful.
        # But if we don't, RSI/MACD won't change, which is bad.
        # Let's try to re-calc ONLY if we are in a small loop, or accept static indicators for speed.
        # For 60 days, static indicators = flat line. We want dynamic.
        # We MUST re-calc.
        
        from src.analysis import calculate_technical_indicators
        # We only need to re-calc if we have enough data.
        # And we need to handle the fact that High/Low are synthetic.
        current_df = calculate_technical_indicators(current_df)
        
        last_date = next_date
        
    return future_predictions
