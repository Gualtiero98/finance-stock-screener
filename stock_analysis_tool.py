from bs4 import BeautifulSoup
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Step 1: Scrape tickers from Yahoo Finance with pagination
def scrape_tickers_from_yahoo_paginated(base_url, num_pages=10):
    tickers = set()
    
    for page in range(0, num_pages):
        url = f"{base_url}&offset={page * 25}&count=25"  # Adjust pagination parameters as needed
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for div in soup.find_all('div', {'class': 'name yf-ravs5v stacked'}):
            ticker = div.find('span', {'class': 'symbol yf-ravs5v'}).text.strip()
            tickers.add(ticker)
    
    return tickers

# Define the URLs for gainers, most active, and trending stocks
urls = {
    "gainers": 'https://finance.yahoo.com/markets/stocks/gainers?count=25',
    "most_active": 'https://finance.yahoo.com/markets/stocks/most-active?count=25',
    "trending": 'https://finance.yahoo.com/markets/stocks/trending?count=25'
}

# Scrape tickers from each category for the first 10 pages
tickers_sets = {}

for category, url in urls.items():
    print(f"Scraping {category} tickers...")
    tickers_sets[category] = scrape_tickers_from_yahoo_paginated(url, num_pages=10)
    print(f"Scraped {len(tickers_sets[category])} unique {category} tickers.\n")

# Step 2: Identify tickers that are present in at least two of the three categories
common_tickers = set()

# Iterate through each ticker and count its occurrence across the categories
ticker_count = {}
for category in tickers_sets:
    for ticker in tickers_sets[category]:
        if ticker not in ticker_count:
            ticker_count[ticker] = 0
        ticker_count[ticker] += 1

# Filter out tickers that appear in at least two categories
common_tickers = {ticker for ticker, count in ticker_count.items() if count >= 2}

print(f"Common Tickers: {common_tickers}")

# Step 3: Fetch historical data for the common tickers and perform analysis
def fetch_data_for_tickers(tickers, start_date, end_date):
    stock_data = {}
    for ticker in tickers:
        stock_data[ticker] = yf.download(ticker, start=start_date, end=end_date)
    return stock_data

# Fetch historical data for the common tickers
start_date = "2020-01-01"
end_date = "2023-01-01"
stock_data = fetch_data_for_tickers(common_tickers, start_date, end_date)

# Calculate technical indicators (RSI, MACD, etc.)
def calculate_metrics(data):
    data['Daily Return'] = data['Adj Close'].pct_change()
    data['50-Day Moving Average'] = data['Adj Close'].rolling(window=50).mean()
    data['200-Day Moving Average'] = data['Adj Close'].rolling(window=200).mean()
    data = calculate_rsi(data)
    data = calculate_macd(data)
    data = calculate_moving_averages(data)
    return data

# Add RSI calculation
def calculate_rsi(data, window=14):
    delta = data['Adj Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    data['RSI'] = rsi.reindex_like(data['Adj Close'])
    return data

# Add MACD calculation
def calculate_macd(data):
    data['26 EMA'] = data['Adj Close'].ewm(span=26, min_periods=0, adjust=False, ignore_na=False).mean()
    data['12 EMA'] = data['Adj Close'].ewm(span=12, min_periods=0, adjust=False, ignore_na=False).mean()
    data['MACD'] = data['12 EMA'] - data['26 EMA']
    data['Signal Line'] = data['MACD'].ewm(span=9, min_periods=0, adjust=False, ignore_na=False).mean()
    return data

# Moving averages calculation
def calculate_moving_averages(data):
    data['50-Day Moving Average'] = data['Adj Close'].rolling(window=50).mean()
    data['200-Day Moving Average'] = data['Adj Close'].rolling(window=200).mean()
    data['Golden Cross'] = data['50-Day Moving Average'] > data['200-Day Moving Average']
    return data

# Screening logic that includes RSI and MACD
def screen_stocks(stock_data):
    screened_stocks = {}
    
    for ticker, data in stock_data.items():
        data = calculate_metrics(data)
        
        avg_return = data['Daily Return'].tail(60).mean()  # 60 trading days (~3 months)
        current_price = data['Adj Close'].iloc[-1]
        moving_avg_200 = data['200-Day Moving Average'].iloc[-1]
        volatility = data['Daily Return'].rolling(window=60).std().iloc[-1]
        rsi = data['RSI'].iloc[-1]
        macd = data['MACD'].iloc[-1]
        signal_line = data['Signal Line'].iloc[-1]
        golden_cross = data['Golden Cross'].iloc[-1]

        # Screening criteria that includes an average return of at least 3% over the last 3 months
        if avg_return >= 0.03 and current_price > moving_avg_200 and volatility < 0.02 and rsi < 70 and macd > signal_line and golden_cross:
            screened_stocks[ticker] = {
                'Average Return (3 months)': avg_return,
                'Current Price': current_price,
                '200-Day Moving Average': moving_avg_200,
                'Volatility': volatility,
                'RSI': rsi,
                'MACD': macd,
                'Signal Line': signal_line,
                'Golden Cross': golden_cross
            }
    
    return screened_stocks

# Apply screening
screened_stocks = screen_stocks(stock_data)

# Print the screened stocks
print("Screened Stocks:")
for ticker, metrics in screened_stocks.items():
    print(f"{ticker}: {metrics}")
